"""
CloudFormation Service
Manages infrastructure stacks from templates with dependency resolution
"""
import json
import yaml
import uuid
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.cloudformation_stack import CloudFormationStack, CloudFormationStackResource
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.resource_ids import generate_resource_id, ResourceType

# Import services for resource provisioning
from app.services.instance_service import InstanceService
from app.services.s3_service import S3Service
from app.services.rds_service import RDSService
from app.services.lambda_service import LambdaService


class CloudFormationService:
    """Service for managing CloudFormation stacks."""
    
    # Supported resource types with their provisioning functions
    SUPPORTED_RESOURCES = {
        "AWS::EC2::Instance",
        "AWS::S3::Bucket",
        "AWS::RDS::DBInstance",
        "AWS::Lambda::Function",
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_stack(
        self,
        account_id: str,
        stack_name: str,
        template_body: str,
        parameters: Optional[Dict[str, str]] = None,
        disable_rollback: bool = False,
        timeout_in_minutes: Optional[int] = None,
        capabilities: Optional[List[str]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> CloudFormationStack:
        """Create a new CloudFormation stack."""
        # Validate stack name
        if not (1 <= len(stack_name) <= 128):
            raise ValidationError("Stack name must be 1-128 characters")
        
        # Check if stack exists
        existing = self.db.query(CloudFormationStack).filter_by(
            stack_name=stack_name,
            account_id=account_id
        ).first()
        if existing:
            raise ValidationError(f"Stack already exists: {stack_name}")
        
        # Parse template
        template, template_format = self._parse_template(template_body)
        
        # Validate template
        self._validate_template(template)
        
        # Generate stack ID
        stack_id = f"arn:aws:cloudformation:us-east-1:{account_id}:stack/{stack_name}/{uuid.uuid4()}"
        
        # Create stack record
        stack = CloudFormationStack(
            stack_name=stack_name,
            stack_id=stack_id,
            account_id=account_id,
            template_body=template_body,
            template_format=template_format,
            stack_status="CREATE_IN_PROGRESS",
            disable_rollback=disable_rollback,
            parameters=json.dumps(parameters) if parameters else None,
            capabilities=json.dumps(capabilities) if capabilities else None,
            tags=json.dumps(tags) if tags else None,
            timeout_in_minutes=timeout_in_minutes
        )
        
        self.db.add(stack)
        self.db.commit()
        self.db.refresh(stack)
        
        # Process stack creation
        try:
            self._process_stack_creation(stack, template, parameters or {})
            
            # Update stack status
            stack.stack_status = "CREATE_COMPLETE"
            stack.last_updated_time = datetime.utcnow()
            self.db.commit()
        
        except Exception as e:
            # Handle rollback
            if disable_rollback:
                stack.stack_status = "CREATE_FAILED"
                stack.stack_status_reason = str(e)
                self.db.commit()
            else:
                self._rollback_stack(stack, str(e))
            
            raise ValidationError(f"Stack creation failed: {e}")
        
        return stack
    
    def _parse_template(self, template_body: str) -> Tuple[Dict[str, Any], str]:
        """Parse CloudFormation template (JSON or YAML)."""
        # Try JSON first
        try:
            template = json.loads(template_body)
            return template, "JSON"
        except json.JSONDecodeError:
            pass
        
        # Try YAML
        try:
            template = yaml.safe_load(template_body)
            return template, "YAML"
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid template format: {e}")
    
    def _validate_template(self, template: Dict[str, Any]) -> None:
        """Validate CloudFormation template structure."""
        # Check required fields
        if "Resources" not in template:
            raise ValidationError("Template must contain 'Resources' section")
        
        resources = template.get("Resources", {})
        if not resources:
            raise ValidationError("Template must contain at least one resource")
        
        # Validate each resource
        for logical_id, resource in resources.items():
            if "Type" not in resource:
                raise ValidationError(f"Resource {logical_id} missing 'Type'")
            
            resource_type = resource["Type"]
            if resource_type not in self.SUPPORTED_RESOURCES:
                raise ValidationError(
                    f"Unsupported resource type: {resource_type}. "
                    f"Supported: {', '.join(self.SUPPORTED_RESOURCES)}"
                )
    
    def _process_stack_creation(
        self,
        stack: CloudFormationStack,
        template: Dict[str, Any],
        parameters: Dict[str, str]
    ) -> None:
        """Process stack creation with dependency resolution."""
        resources = template.get("Resources", {})
        
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(resources)
        
        # Resolve dependencies and get creation order
        creation_order = self._resolve_dependencies(dependency_graph)
        
        # Create resources in order
        created_resources = {}
        
        for logical_id in creation_order:
            resource_def = resources[logical_id]
            
            try:
                # Create stack resource record
                stack_resource = CloudFormationStackResource(
                    stack_name=stack.stack_name,
                    logical_resource_id=logical_id,
                    resource_type=resource_def["Type"],
                    resource_status="CREATE_IN_PROGRESS",
                    resource_properties=json.dumps(resource_def.get("Properties", {}))
                )
                self.db.add(stack_resource)
                self.db.commit()
                
                # Provision the resource
                physical_id = self._provision_resource(
                    stack.account_id,
                    resource_def,
                    created_resources,
                    parameters
                )
                
                # Update resource status
                stack_resource.physical_resource_id = physical_id
                stack_resource.resource_status = "CREATE_COMPLETE"
                stack_resource.last_updated_timestamp = datetime.utcnow()
                self.db.commit()
                
                # Store created resource for references
                created_resources[logical_id] = physical_id
            
            except Exception as e:
                # Update resource status
                stack_resource.resource_status = "CREATE_FAILED"
                stack_resource.resource_status_reason = str(e)
                self.db.commit()
                
                raise ValidationError(f"Failed to create resource {logical_id}: {e}")
        
        # Process outputs
        if "Outputs" in template:
            outputs = self._process_outputs(template["Outputs"], created_resources)
            stack.outputs = json.dumps(outputs)
            self.db.commit()
    
    def _build_dependency_graph(self, resources: Dict[str, Any]) -> Dict[str, Set[str]]:
        """Build dependency graph from resources."""
        graph = defaultdict(set)
        
        for logical_id, resource in resources.items():
            # Explicit dependencies (DependsOn)
            depends_on = resource.get("DependsOn", [])
            if isinstance(depends_on, str):
                depends_on = [depends_on]
            
            for dep in depends_on:
                graph[logical_id].add(dep)
            
            # Implicit dependencies (Ref and GetAtt)
            properties = resource.get("Properties", {})
            self._find_references(properties, graph, logical_id, resources)
        
        return graph
    
    def _find_references(
        self,
        obj: Any,
        graph: Dict[str, Set[str]],
        current_resource: str,
        all_resources: Dict[str, Any]
    ) -> None:
        """Find Ref and GetAtt references in properties."""
        if isinstance(obj, dict):
            # Check for Ref
            if "Ref" in obj:
                ref_target = obj["Ref"]
                if ref_target in all_resources:
                    graph[current_resource].add(ref_target)
            
            # Check for Fn::GetAtt
            if "Fn::GetAtt" in obj:
                get_att = obj["Fn::GetAtt"]
                if isinstance(get_att, list) and len(get_att) > 0:
                    target = get_att[0]
                    if target in all_resources:
                        graph[current_resource].add(target)
            
            # Recurse into nested dicts
            for value in obj.values():
                self._find_references(value, graph, current_resource, all_resources)
        
        elif isinstance(obj, list):
            # Recurse into lists
            for item in obj:
                self._find_references(item, graph, current_resource, all_resources)
    
    def _resolve_dependencies(self, graph: Dict[str, Set[str]]) -> List[str]:
        """Topological sort to resolve dependencies."""
        # Calculate in-degrees
        in_degree = defaultdict(int)
        all_nodes = set(graph.keys())
        
        for node in graph:
            for dep in graph[node]:
                in_degree[dep] += 0  # Ensure all nodes are in in_degree
                all_nodes.add(dep)
        
        for node in all_nodes:
            if node not in in_degree:
                in_degree[node] = 0
        
        for node in graph:
            for dep in graph[node]:
                in_degree[node] += 1
        
        # Kahn's algorithm
        queue = [node for node in all_nodes if in_degree[node] == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Update dependents
            for dependent in all_nodes:
                if node in graph[dependent]:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        if len(result) != len(all_nodes):
            raise ValidationError("Circular dependency detected in template")
        
        return result
    
    def _provision_resource(
        self,
        account_id: str,
        resource_def: Dict[str, Any],
        created_resources: Dict[str, str],
        parameters: Dict[str, str]
    ) -> str:
        """Provision a single resource."""
        resource_type = resource_def["Type"]
        properties = resource_def.get("Properties", {})
        
        # Resolve references in properties
        resolved_properties = self._resolve_properties(properties, created_resources, parameters)
        
        # Provision based on resource type
        if resource_type == "AWS::EC2::Instance":
            return self._provision_ec2_instance(account_id, resolved_properties)
        
        elif resource_type == "AWS::S3::Bucket":
            return self._provision_s3_bucket(account_id, resolved_properties)
        
        elif resource_type == "AWS::RDS::DBInstance":
            return self._provision_rds_instance(account_id, resolved_properties)
        
        elif resource_type == "AWS::Lambda::Function":
            return self._provision_lambda_function(account_id, resolved_properties)
        
        else:
            raise ValidationError(f"Unsupported resource type: {resource_type}")
    
    def _resolve_properties(
        self,
        properties: Dict[str, Any],
        created_resources: Dict[str, str],
        parameters: Dict[str, str]
    ) -> Dict[str, Any]:
        """Resolve Ref and GetAtt in properties."""
        def resolve_value(obj: Any) -> Any:
            if isinstance(obj, dict):
                # Handle Ref
                if "Ref" in obj:
                    ref_target = obj["Ref"]
                    if ref_target in created_resources:
                        return created_resources[ref_target]
                    elif ref_target in parameters:
                        return parameters[ref_target]
                    else:
                        return ref_target
                
                # Handle GetAtt
                if "Fn::GetAtt" in obj:
                    get_att = obj["Fn::GetAtt"]
                    if isinstance(get_att, list) and len(get_att) >= 1:
                        resource_id = get_att[0]
                        if resource_id in created_resources:
                            return created_resources[resource_id]
                
                # Recurse into nested dicts
                return {k: resolve_value(v) for k, v in obj.items()}
            
            elif isinstance(obj, list):
                return [resolve_value(item) for item in obj]
            
            else:
                return obj
        
        return resolve_value(properties)
    
    def _provision_ec2_instance(self, account_id: str, properties: Dict[str, Any]) -> str:
        """Provision an EC2 instance."""
        compute_service = InstanceService(self.db)
        
        instance = compute_service.create_instance(
            account_id=account_id,
            image=properties.get("ImageId", "ubuntu:22.04"),
            instance_type=properties.get("InstanceType", "t2.micro"),
            tags=properties.get("Tags", {}),
            user_data=properties.get("UserData")
        )
        
        return instance.instance_id
    
    def _provision_s3_bucket(self, account_id: str, properties: Dict[str, Any]) -> str:
        """Provision an S3 bucket."""
        s3_service = S3Service(self.db)
        
        bucket_name = properties.get("BucketName", f"cfn-bucket-{uuid.uuid4().hex[:8]}")
        
        bucket = s3_service.create_bucket(
            account_id=account_id,
            bucket_name=bucket_name
        )
        
        return bucket.bucket_name
    
    def _provision_rds_instance(self, account_id: str, properties: Dict[str, Any]) -> str:
        """Provision an RDS instance."""
        rds_service = RDSService(self.db)
        
        import base64
        
        db_instance = rds_service.create_db_instance(
            account_id=account_id,
            db_instance_identifier=properties.get("DBInstanceIdentifier", f"cfn-db-{uuid.uuid4().hex[:8]}"),
            db_instance_class=properties.get("DBInstanceClass", "db.t2.micro"),
            engine=properties.get("Engine", "mysql"),
            master_username=properties.get("MasterUsername", "admin"),
            master_user_password=properties.get("MasterUserPassword", "password123"),
            allocated_storage=properties.get("AllocatedStorage", 20)
        )
        
        return db_instance.db_instance_identifier
    
    def _provision_lambda_function(self, account_id: str, properties: Dict[str, Any]) -> str:
        """Provision a Lambda function."""
        lambda_service = LambdaService(self.db)
        
        # Create simple code if not provided
        import base64
        import zipfile
        from io import BytesIO
        
        code = properties.get("Code", {})
        zip_file_b64 = code.get("ZipFile")
        
        if not zip_file_b64:
            # Create default handler
            handler_code = "def handler(event, context): return {'statusCode': 200}"
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr('index.py', handler_code)
            zip_file_b64 = base64.b64encode(zip_buffer.getvalue()).decode()
        
        function = lambda_service.create_function(
            account_id=account_id,
            function_name=properties.get("FunctionName", f"cfn-function-{uuid.uuid4().hex[:8]}"),
            runtime=properties.get("Runtime", "python3.11"),
            role=properties.get("Role", f"arn:aws:iam::{account_id}:role/lambda-role"),
            handler=properties.get("Handler", "index.handler"),
            zip_file=base64.b64decode(zip_file_b64),
            timeout=properties.get("Timeout", 3),
            memory_size=properties.get("MemorySize", 128),
            environment=properties.get("Environment", {}).get("Variables")
        )
        
        return function.function_name
    
    def _process_outputs(
        self,
        outputs: Dict[str, Any],
        created_resources: Dict[str, str]
    ) -> Dict[str, Dict[str, str]]:
        """Process stack outputs."""
        result = {}
        
        for output_name, output_def in outputs.items():
            value = output_def.get("Value")
            
            # Resolve Ref
            if isinstance(value, dict) and "Ref" in value:
                ref_target = value["Ref"]
                if ref_target in created_resources:
                    value = created_resources[ref_target]
            
            result[output_name] = {
                "Value": str(value),
                "Description": output_def.get("Description", "")
            }
        
        return result
    
    def _rollback_stack(self, stack: CloudFormationStack, error_message: str) -> None:
        """Rollback stack creation on failure."""
        stack.stack_status = "ROLLBACK_IN_PROGRESS"
        stack.stack_status_reason = error_message
        self.db.commit()
        
        # Get all created resources
        resources = self.db.query(CloudFormationStackResource).filter_by(
            stack_name=stack.stack_name
        ).filter(
            CloudFormationStackResource.resource_status == "CREATE_COMPLETE"
        ).all()
        
        # Delete resources in reverse order
        for resource in reversed(resources):
            try:
                self._delete_resource(stack.account_id, resource)
                resource.resource_status = "DELETE_COMPLETE"
                self.db.commit()
            except Exception as e:
                resource.resource_status = "DELETE_FAILED"
                resource.resource_status_reason = str(e)
                self.db.commit()
        
        stack.stack_status = "ROLLBACK_COMPLETE"
        self.db.commit()
    
    def _delete_resource(self, account_id: str, resource: CloudFormationStackResource) -> None:
        """Delete a provisioned resource."""
        resource_type = resource.resource_type
        physical_id = resource.physical_resource_id
        
        if not physical_id:
            return
        
        try:
            if resource_type == "AWS::EC2::Instance":
                compute_service = InstanceService(self.db)
                compute_service.terminate_instance(account_id, physical_id)
            
            elif resource_type == "AWS::S3::Bucket":
                s3_service = S3Service(self.db)
                s3_service.delete_bucket(account_id, physical_id)
            
            elif resource_type == "AWS::RDS::DBInstance":
                rds_service = RDSService(self.db)
                rds_service.delete_db_instance(account_id, physical_id, skip_final_snapshot=True)
            
            elif resource_type == "AWS::Lambda::Function":
                lambda_service = LambdaService(self.db)
                lambda_service.delete_function(account_id, physical_id)
        
        except Exception as e:
            # Log error but continue rollback
            print(f"Failed to delete resource {physical_id}: {e}")
    
    def get_stack(self, account_id: str, stack_name: str) -> CloudFormationStack:
        """Get a stack by name."""
        stack = self.db.query(CloudFormationStack).filter_by(
            stack_name=stack_name,
            account_id=account_id
        ).first()
        
        if not stack:
            raise ResourceNotFoundError(f"Stack not found: {stack_name}")
        
        return stack
    
    def list_stacks(self, account_id: str) -> List[CloudFormationStack]:
        """List all stacks for an account."""
        return self.db.query(CloudFormationStack).filter_by(
            account_id=account_id
        ).all()
    
    def delete_stack(self, account_id: str, stack_name: str) -> None:
        """Delete a stack and all its resources."""
        stack = self.get_stack(account_id, stack_name)
        
        stack.stack_status = "DELETE_IN_PROGRESS"
        self.db.commit()
        
        # Get all resources
        resources = self.db.query(CloudFormationStackResource).filter_by(
            stack_name=stack_name
        ).all()
        
        # Delete resources in reverse order
        for resource in reversed(resources):
            try:
                self._delete_resource(account_id, resource)
                resource.resource_status = "DELETE_COMPLETE"
                self.db.commit()
            except Exception as e:
                resource.resource_status = "DELETE_FAILED"
                resource.resource_status_reason = str(e)
                self.db.commit()
        
        # Mark stack as deleted
        stack.stack_status = "DELETE_COMPLETE"
        stack.deletion_time = datetime.utcnow()
        self.db.commit()
    
    def validate_template(self, template_body: str) -> Dict[str, Any]:
        """Validate a CloudFormation template."""
        try:
            template, template_format = self._parse_template(template_body)
            self._validate_template(template)
            
            # Extract parameters
            parameters = []
            if "Parameters" in template:
                for param_name, param_def in template["Parameters"].items():
                    parameters.append({
                        "ParameterKey": param_name,
                        "Description": param_def.get("Description", ""),
                        "DefaultValue": param_def.get("Default"),
                        "ParameterType": param_def.get("Type", "String")
                    })
            
            return {
                "Valid": True,
                "Format": template_format,
                "Parameters": parameters,
                "ResourceTypes": list(set(r["Type"] for r in template.get("Resources", {}).values()))
            }
        
        except Exception as e:
            return {
                "Valid": False,
                "Error": str(e)
            }


