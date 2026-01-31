"""
CloudFormation API Routes
IAM-protected endpoints for CloudFormation stack management
"""
import json
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.cloudformation import (
    CreateStackRequest,
    CreateStackResponse,
    DescribeStacksRequest,
    DescribeStacksResponse,
    DeleteStackRequest,
    ListStackResourcesRequest,
    ListStackResourcesResponse,
    ValidateTemplateRequest,
    ValidateTemplateResponse,
    GetTemplateRequest,
    GetTemplateResponse,
    StackInfo,
    StackResourceInfo,
    TemplateParameter
)
from app.services.cloudformation_service import CloudFormationService
from app.core.exceptions import ResourceNotFoundError, ValidationError

router = APIRouter(prefix="/cloudformation", tags=["CloudFormation"])


def _build_stack_info(stack) -> StackInfo:
    """Build StackInfo from CloudFormationStack model."""
    parameters = None
    if stack.parameters:
        parameters = json.loads(stack.parameters)
    
    outputs = None
    if stack.outputs:
        outputs = json.loads(stack.outputs)
    
    tags = None
    if stack.tags:
        tags = json.loads(stack.tags)
    
    return StackInfo(
        stack_name=stack.stack_name,
        stack_id=stack.stack_id,
        stack_status=stack.stack_status,
        stack_status_reason=stack.stack_status_reason,
        creation_time=stack.creation_time.isoformat(),
        last_updated_time=stack.last_updated_time.isoformat() if stack.last_updated_time else None,
        deletion_time=stack.deletion_time.isoformat() if stack.deletion_time else None,
        disable_rollback=stack.disable_rollback,
        outputs=outputs,
        parameters=parameters,
        tags=tags
    )


@router.post("/stacks", response_model=CreateStackResponse)
async def create_stack(
    request: CreateStackRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new CloudFormation stack."""
    check_permissions(user, "cloudformation:CreateStack")
    
    try:
        # Convert parameters list to dict
        parameters = None
        if request.parameters:
            parameters = {p.parameter_key: p.parameter_value for p in request.parameters}
        
        # Convert tags list to dict
        tags = None
        if request.tags:
            tags = {t.key: t.value for t in request.tags}
        
        # Create stack
        cfn_service = CloudFormationService(db)
        stack = cfn_service.create_stack(
            account_id=user["account_id"],
            stack_name=request.stack_name,
            template_body=request.template_body,
            parameters=parameters,
            disable_rollback=request.disable_rollback,
            timeout_in_minutes=request.timeout_in_minutes,
            capabilities=request.capabilities,
            tags=tags
        )
        
        return CreateStackResponse(
            stack_id=stack.stack_id,
            stack_name=stack.stack_name
        )
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stacks/describe", response_model=DescribeStacksResponse)
async def describe_stacks(
    request: DescribeStacksRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Describe CloudFormation stacks."""
    check_permissions(user, "cloudformation:DescribeStacks")
    
    try:
        cfn_service = CloudFormationService(db)
        
        if request.stack_name:
            # Get specific stack
            stack = cfn_service.get_stack(user["account_id"], request.stack_name)
            stacks = [stack]
        else:
            # List all stacks
            stacks = cfn_service.list_stacks(user["account_id"])
        
        # Build response
        stack_infos = [_build_stack_info(s) for s in stacks]
        
        return DescribeStacksResponse(stacks=stack_infos)
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stacks")
async def delete_stack(
    request: DeleteStackRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a CloudFormation stack."""
    check_permissions(user, "cloudformation:DeleteStack")
    
    try:
        cfn_service = CloudFormationService(db)
        cfn_service.delete_stack(user["account_id"], request.stack_name)
        
        return {"message": f"Stack {request.stack_name} deletion initiated"}
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stacks/resources", response_model=ListStackResourcesResponse)
async def list_stack_resources(
    request: ListStackResourcesRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List resources in a CloudFormation stack."""
    check_permissions(user, "cloudformation:ListStackResources")
    
    try:
        cfn_service = CloudFormationService(db)
        
        # Get stack to verify ownership
        stack = cfn_service.get_stack(user["account_id"], request.stack_name)
        
        # Build response
        resource_infos = []
        for resource in stack.resources:
            resource_infos.append(StackResourceInfo(
                logical_resource_id=resource.logical_resource_id,
                physical_resource_id=resource.physical_resource_id,
                resource_type=resource.resource_type,
                resource_status=resource.resource_status,
                resource_status_reason=resource.resource_status_reason,
                timestamp=resource.timestamp.isoformat(),
                last_updated_timestamp=resource.last_updated_timestamp.isoformat() if resource.last_updated_timestamp else None
            ))
        
        return ListStackResourcesResponse(stack_resources=resource_infos)
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-template", response_model=ValidateTemplateResponse)
async def validate_template(
    request: ValidateTemplateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a CloudFormation template."""
    check_permissions(user, "cloudformation:ValidateTemplate")
    
    try:
        cfn_service = CloudFormationService(db)
        result = cfn_service.validate_template(request.template_body)
        
        # Build response
        parameters = None
        if result.get("Valid") and "Parameters" in result:
            parameters = [
                TemplateParameter(
                    parameter_key=p["ParameterKey"],
                    description=p.get("Description"),
                    default_value=p.get("DefaultValue"),
                    parameter_type=p.get("ParameterType", "String")
                )
                for p in result["Parameters"]
            ]
        
        return ValidateTemplateResponse(
            valid=result["Valid"],
            format=result.get("Format"),
            parameters=parameters,
            resource_types=result.get("ResourceTypes"),
            error=result.get("Error")
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stacks/template", response_model=GetTemplateResponse)
async def get_template(
    request: GetTemplateRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get the template for a CloudFormation stack."""
    check_permissions(user, "cloudformation:GetTemplate")
    
    try:
        cfn_service = CloudFormationService(db)
        stack = cfn_service.get_stack(user["account_id"], request.stack_name)
        
        return GetTemplateResponse(
            template_body=stack.template_body,
            template_format=stack.template_format
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

