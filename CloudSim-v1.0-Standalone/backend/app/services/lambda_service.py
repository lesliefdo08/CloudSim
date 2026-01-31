"""
Lambda Service
Manages serverless functions with Docker runtime isolation
"""
import os
import json
import hashlib
import zipfile
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import docker
from sqlalchemy.orm import Session

from app.models.lambda_function import LambdaFunction
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.core.resource_ids import generate_resource_id, ResourceType


class LambdaService:
    """Service for managing Lambda functions."""
    
    # Supported runtimes with Docker images
    RUNTIME_IMAGES = {
        "python3.9": "public.ecr.aws/lambda/python:3.9",
        "python3.10": "public.ecr.aws/lambda/python:3.10",
        "python3.11": "public.ecr.aws/lambda/python:3.11",
        "python3.12": "public.ecr.aws/lambda/python:3.12",
        "nodejs18.x": "public.ecr.aws/lambda/nodejs:18",
        "nodejs20.x": "public.ecr.aws/lambda/nodejs:20",
    }
    
    def __init__(self, db: Session):
        self.db = db
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None
        self.code_storage_path = Path("lambda_code_storage")
        self.code_storage_path.mkdir(exist_ok=True)
    
    def create_function(
        self,
        account_id: str,
        function_name: str,
        runtime: str,
        role: str,
        handler: str,
        zip_file: bytes,
        description: Optional[str] = None,
        timeout: int = 3,
        memory_size: int = 128,
        environment: Optional[Dict[str, str]] = None,
        vpc_config: Optional[Dict[str, List[str]]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> LambdaFunction:
        """Create a new Lambda function."""
        # Validate function name
        if not (1 <= len(function_name) <= 64):
            raise ValidationError("Function name must be 1-64 characters")
        
        # Check if function exists
        existing = self.db.query(LambdaFunction).filter_by(
            function_name=function_name,
            account_id=account_id
        ).first()
        if existing:
            raise ValidationError(f"Function already exists: {function_name}")
        
        # Validate runtime
        if runtime not in self.RUNTIME_IMAGES:
            raise ValidationError(
                f"Unsupported runtime: {runtime}. "
                f"Supported: {', '.join(self.RUNTIME_IMAGES.keys())}"
            )
        
        # Validate timeout (1-900 seconds)
        if not (1 <= timeout <= 900):
            raise ValidationError("Timeout must be between 1 and 900 seconds")
        
        # Validate memory (128-10240 MB, must be multiple of 64)
        if not (128 <= memory_size <= 10240) or memory_size % 64 != 0:
            raise ValidationError("Memory must be 128-10240 MB and multiple of 64")
        
        # Calculate code hash
        code_sha256 = hashlib.sha256(zip_file).hexdigest()
        code_size = len(zip_file)
        
        # Store code
        function_dir = self.code_storage_path / account_id / function_name
        function_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = function_dir / "function.zip"
        with open(zip_path, "wb") as f:
            f.write(zip_file)
        
        # Extract code
        code_dir = function_dir / "code"
        code_dir.mkdir(exist_ok=True)
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(code_dir)
        except zipfile.BadZipFile:
            raise ValidationError("Invalid ZIP file")
        
        # Generate ARN
        function_arn = f"arn:aws:lambda:us-east-1:{account_id}:function:{function_name}"
        
        # Create function record
        function = LambdaFunction(
            function_name=function_name,
            function_arn=function_arn,
            account_id=account_id,
            runtime=runtime,
            handler=handler,
            code_storage_location=str(code_dir),
            code_sha256=code_sha256,
            code_size=code_size,
            description=description,
            timeout=timeout,
            memory_size=memory_size,
            environment_variables=json.dumps(environment) if environment else None,
            role=role,
            vpc_config=json.dumps(vpc_config) if vpc_config else None,
            state="Active",
            last_update_status="Successful",
            container_image=self.RUNTIME_IMAGES[runtime],
            tags=json.dumps(tags) if tags else None
        )
        
        self.db.add(function)
        self.db.commit()
        self.db.refresh(function)
        
        return function
    
    def get_function(self, account_id: str, function_name: str) -> LambdaFunction:
        """Get a Lambda function."""
        function = self.db.query(LambdaFunction).filter_by(
            function_name=function_name,
            account_id=account_id
        ).first()
        
        if not function:
            raise ResourceNotFoundError(f"Function not found: {function_name}")
        
        return function
    
    def list_functions(self, account_id: str) -> List[LambdaFunction]:
        """List all Lambda functions for an account."""
        return self.db.query(LambdaFunction).filter_by(
            account_id=account_id
        ).all()
    
    def delete_function(self, account_id: str, function_name: str) -> None:
        """Delete a Lambda function."""
        function = self.get_function(account_id, function_name)
        
        # Remove code storage
        function_dir = Path(function.code_storage_location).parent
        if function_dir.exists():
            import shutil
            shutil.rmtree(function_dir)
        
        # Delete function
        self.db.delete(function)
        self.db.commit()
    
    def update_function_code(
        self,
        account_id: str,
        function_name: str,
        zip_file: bytes
    ) -> LambdaFunction:
        """Update function code."""
        function = self.get_function(account_id, function_name)
        
        # Calculate new code hash
        code_sha256 = hashlib.sha256(zip_file).hexdigest()
        code_size = len(zip_file)
        
        # Store new code
        function_dir = Path(function.code_storage_location).parent
        zip_path = function_dir / "function.zip"
        
        with open(zip_path, "wb") as f:
            f.write(zip_file)
        
        # Extract code
        code_dir = Path(function.code_storage_location)
        # Remove old code
        import shutil
        if code_dir.exists():
            shutil.rmtree(code_dir)
        code_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(code_dir)
        except zipfile.BadZipFile:
            raise ValidationError("Invalid ZIP file")
        
        # Update function
        function.code_sha256 = code_sha256
        function.code_size = code_size
        function.last_modified = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(function)
        
        return function
    
    def update_function_configuration(
        self,
        account_id: str,
        function_name: str,
        timeout: Optional[int] = None,
        memory_size: Optional[int] = None,
        environment: Optional[Dict[str, str]] = None,
        description: Optional[str] = None
    ) -> LambdaFunction:
        """Update function configuration."""
        function = self.get_function(account_id, function_name)
        
        if timeout is not None:
            if not (1 <= timeout <= 900):
                raise ValidationError("Timeout must be between 1 and 900 seconds")
            function.timeout = timeout
        
        if memory_size is not None:
            if not (128 <= memory_size <= 10240) or memory_size % 64 != 0:
                raise ValidationError("Memory must be 128-10240 MB and multiple of 64")
            function.memory_size = memory_size
        
        if environment is not None:
            function.environment_variables = json.dumps(environment)
        
        if description is not None:
            function.description = description
        
        function.last_modified = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(function)
        
        return function
    
    def invoke_function(
        self,
        account_id: str,
        function_name: str,
        payload: Dict[str, Any],
        invocation_type: str = "RequestResponse",
        log_type: str = "None"
    ) -> Dict[str, Any]:
        """Invoke a Lambda function with runtime isolation."""
        function = self.get_function(account_id, function_name)
        
        if function.state != "Active":
            raise ValidationError(f"Function is not active: {function.state}")
        
        # Generate invocation ID
        request_id = str(uuid.uuid4())
        
        # Prepare environment variables
        env_vars = {
            "AWS_LAMBDA_FUNCTION_NAME": function_name,
            "AWS_LAMBDA_FUNCTION_VERSION": function.version,
            "AWS_LAMBDA_FUNCTION_MEMORY_SIZE": str(function.memory_size),
            "AWS_REGION": "us-east-1",
            "AWS_REQUEST_ID": request_id,
        }
        
        # Add user environment variables
        if function.environment_variables:
            user_env = json.loads(function.environment_variables)
            env_vars.update(user_env)
        
        # Prepare payload
        payload_json = json.dumps(payload)
        
        # Determine runtime handler
        handler_module, handler_function = function.handler.rsplit(".", 1)
        
        # Create invocation wrapper script
        if function.runtime.startswith("python"):
            wrapper_script = self._create_python_wrapper(
                handler_module,
                handler_function,
                payload_json
            )
            entry_command = ["python", "-c", wrapper_script]
        elif function.runtime.startswith("nodejs"):
            wrapper_script = self._create_nodejs_wrapper(
                handler_module,
                handler_function,
                payload_json
            )
            entry_command = ["node", "-e", wrapper_script]
        else:
            raise ValidationError(f"Runtime not supported: {function.runtime}")
        
        # Create container for invocation
        container_name = f"lambda-{function_name}-{request_id[:8]}"
        
        start_time = time.time()
        status_code = 200
        function_error = None
        log_result = ""
        
        try:
            # Run container
            container = self.docker_client.containers.run(
                function.container_image,
                command=entry_command,
                name=container_name,
                environment=env_vars,
                volumes={
                    str(Path(function.code_storage_location).absolute()): {
                        "bind": "/var/task",
                        "mode": "ro"
                    }
                },
                working_dir="/var/task",
                detach=False,
                remove=True,
                mem_limit=f"{function.memory_size}m",
                network_mode="none",  # Isolated
                stdout=True,
                stderr=True
            )
            
            # Get output
            output = container.decode("utf-8")
            
            # Parse result (last line should be JSON result)
            lines = output.strip().split("\n")
            result_json = lines[-1] if lines else "{}"
            log_lines = lines[:-1] if len(lines) > 1 else []
            
            log_result = "\n".join(log_lines)
            
            try:
                result = json.loads(result_json)
            except json.JSONDecodeError:
                result = {"error": "Invalid JSON response", "output": output}
                function_error = "Unhandled"
                status_code = 500
        
        except docker.errors.ContainerError as e:
            # Function error
            status_code = 500
            function_error = "Unhandled"
            result = {
                "errorMessage": str(e),
                "errorType": "ContainerError"
            }
            log_result = e.stderr.decode("utf-8") if e.stderr else str(e)
        
        except Exception as e:
            # System error
            status_code = 500
            function_error = "Unhandled"
            result = {
                "errorMessage": str(e),
                "errorType": type(e).__name__
            }
            log_result = str(e)
        
        finally:
            # Clean up container if still exists
            try:
                container_obj = self.docker_client.containers.get(container_name)
                container_obj.remove(force=True)
            except docker.errors.NotFound:
                pass
        
        duration = int((time.time() - start_time) * 1000)  # milliseconds
        
        # Update metrics
        function.invocations += 1
        if function_error:
            function.errors += 1
        self.db.commit()
        
        # Prepare response
        response = {
            "StatusCode": status_code,
            "ExecutedVersion": function.version,
            "Payload": result
        }
        
        if function_error:
            response["FunctionError"] = function_error
        
        if log_type == "Tail":
            # Return last 4KB of logs (base64 encoded)
            import base64
            log_tail = log_result[-4096:] if log_result else ""
            response["LogResult"] = base64.b64encode(log_tail.encode()).decode()
        
        # CloudWatch integration (to be called by API layer)
        response["_cloudwatch_logs"] = {
            "log_group": f"/aws/lambda/{function_name}",
            "log_stream": f"{datetime.utcnow().strftime('%Y/%m/%d')}/[$LATEST]{request_id}",
            "logs": log_result,
            "request_id": request_id
        }
        
        response["_cloudwatch_metrics"] = {
            "namespace": "AWS/Lambda",
            "metrics": [
                {
                    "name": "Invocations",
                    "value": 1,
                    "unit": "Count",
                    "dimensions": {"FunctionName": function_name}
                },
                {
                    "name": "Duration",
                    "value": duration,
                    "unit": "Milliseconds",
                    "dimensions": {"FunctionName": function_name}
                },
                {
                    "name": "Errors",
                    "value": 1 if function_error else 0,
                    "unit": "Count",
                    "dimensions": {"FunctionName": function_name}
                }
            ]
        }
        
        return response
    
    def _create_python_wrapper(
        self,
        module: str,
        function: str,
        payload_json: str
    ) -> str:
        """Create Python wrapper script for invocation."""
        return f"""
import json
import sys

# Import handler
try:
    from {module} import {function} as handler
except ImportError as e:
    print(json.dumps({{"errorMessage": f"Unable to import module: {{e}}", "errorType": "ImportError"}}))
    sys.exit(1)

# Parse event
event = json.loads('''{payload_json}''')

# Invoke handler
try:
    result = handler(event, {{}})
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"errorMessage": str(e), "errorType": type(e).__name__}}))
    sys.exit(1)
"""
    
    def _create_nodejs_wrapper(
        self,
        module: str,
        function: str,
        payload_json: str
    ) -> str:
        """Create Node.js wrapper script for invocation."""
        return f"""
const handler = require('./{module}').{function};
const event = {payload_json};

handler(event, {{}}, (error, result) => {{
    if (error) {{
        console.log(JSON.stringify({{
            errorMessage: error.message,
            errorType: error.name
        }}));
        process.exit(1);
    }}
    console.log(JSON.stringify(result));
}});
"""


