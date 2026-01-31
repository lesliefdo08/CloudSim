"""
Lambda API Routes
IAM-protected endpoints for Lambda function management
"""
import base64
import json
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.lambda_schemas import (
    CreateFunctionRequest,
    CreateFunctionResponse,
    GetFunctionRequest,
    GetFunctionResponse,
    ListFunctionsRequest,
    ListFunctionsResponse,
    DeleteFunctionRequest,
    UpdateFunctionCodeRequest,
    UpdateFunctionCodeResponse,
    UpdateFunctionConfigurationRequest,
    UpdateFunctionConfigurationResponse,
    InvokeFunctionRequest,
    InvokeFunctionResponse,
    FunctionConfiguration
)
from app.services.lambda_service import LambdaService
from app.services.cloudwatch_logs_service import CloudWatchLogsService
from app.services.cloudwatch_service import CloudWatchService as CloudWatchMetricsService
from app.core.exceptions import ResourceNotFoundError, ValidationError

router = APIRouter(prefix="/lambda", tags=["Lambda"])


def _build_function_configuration(function) -> FunctionConfiguration:
    """Build FunctionConfiguration from LambdaFunction model."""
    environment = None
    if function.environment_variables:
        environment = json.loads(function.environment_variables)
    
    return FunctionConfiguration(
        function_name=function.function_name,
        function_arn=function.function_arn,
        runtime=function.runtime,
        role=function.role,
        handler=function.handler,
        code_sha256=function.code_sha256,
        code_size=function.code_size,
        description=function.description,
        timeout=function.timeout,
        memory_size=function.memory_size,
        last_modified=function.last_modified.isoformat(),
        version=function.version,
        state=function.state,
        state_reason=function.state_reason,
        environment=environment
    )


@router.post("/functions", response_model=CreateFunctionResponse)
async def create_function(
    request: CreateFunctionRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new Lambda function."""
    check_permissions(user, "lambda:CreateFunction")
    
    try:
        # Decode ZIP file
        try:
            zip_bytes = base64.b64decode(request.zip_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {e}")
        
        # Create function
        lambda_service = LambdaService(db)
        function = lambda_service.create_function(
            account_id=user["account_id"],
            function_name=request.function_name,
            runtime=request.runtime,
            role=request.role,
            handler=request.handler,
            zip_file=zip_bytes,
            description=request.description,
            timeout=request.timeout,
            memory_size=request.memory_size,
            environment=request.environment,
            vpc_config=request.vpc_config,
            tags=request.tags
        )
        
        # Build response
        config = _build_function_configuration(function)
        return CreateFunctionResponse(function=config)
    
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/functions/get", response_model=GetFunctionResponse)
async def get_function(
    request: GetFunctionRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a Lambda function configuration."""
    check_permissions(user, "lambda:GetFunction")
    
    try:
        lambda_service = LambdaService(db)
        function = lambda_service.get_function(
            account_id=user["account_id"],
            function_name=request.function_name
        )
        
        # Build response
        config = _build_function_configuration(function)
        
        code_info = {
            "repository_type": "S3",
            "location": function.code_storage_location
        }
        
        return GetFunctionResponse(
            configuration=config,
            code=code_info
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/functions/list", response_model=ListFunctionsResponse)
async def list_functions(
    request: ListFunctionsRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List Lambda functions."""
    check_permissions(user, "lambda:ListFunctions")
    
    try:
        lambda_service = LambdaService(db)
        functions = lambda_service.list_functions(account_id=user["account_id"])
        
        # Build response
        function_configs = [
            _build_function_configuration(f)
            for f in functions[:request.max_items]
        ]
        
        return ListFunctionsResponse(functions=function_configs)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/functions")
async def delete_function(
    request: DeleteFunctionRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a Lambda function."""
    check_permissions(user, "lambda:DeleteFunction")
    
    try:
        lambda_service = LambdaService(db)
        lambda_service.delete_function(
            account_id=user["account_id"],
            function_name=request.function_name
        )
        
        return {"message": f"Function {request.function_name} deleted successfully"}
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/functions/code", response_model=UpdateFunctionCodeResponse)
async def update_function_code(
    request: UpdateFunctionCodeRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Lambda function code."""
    check_permissions(user, "lambda:UpdateFunctionCode")
    
    try:
        # Decode ZIP file
        try:
            zip_bytes = base64.b64decode(request.zip_file)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 encoding: {e}")
        
        lambda_service = LambdaService(db)
        function = lambda_service.update_function_code(
            account_id=user["account_id"],
            function_name=request.function_name,
            zip_file=zip_bytes
        )
        
        # Build response
        config = _build_function_configuration(function)
        return UpdateFunctionCodeResponse(function=config)
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/functions/configuration", response_model=UpdateFunctionConfigurationResponse)
async def update_function_configuration(
    request: UpdateFunctionConfigurationRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update Lambda function configuration."""
    check_permissions(user, "lambda:UpdateFunctionConfiguration")
    
    try:
        lambda_service = LambdaService(db)
        function = lambda_service.update_function_configuration(
            account_id=user["account_id"],
            function_name=request.function_name,
            timeout=request.timeout,
            memory_size=request.memory_size,
            environment=request.environment,
            description=request.description
        )
        
        # Build response
        config = _build_function_configuration(function)
        return UpdateFunctionConfigurationResponse(function=config)
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/functions/invoke", response_model=InvokeFunctionResponse)
async def invoke_function(
    request: InvokeFunctionRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invoke a Lambda function."""
    check_permissions(user, "lambda:InvokeFunction")
    
    try:
        lambda_service = LambdaService(db)
        result = lambda_service.invoke_function(
            account_id=user["account_id"],
            function_name=request.function_name,
            payload=request.payload,
            invocation_type=request.invocation_type,
            log_type=request.log_type
        )
        
        # Send logs to CloudWatch Logs
        if "_cloudwatch_logs" in result:
            cw_logs_data = result.pop("_cloudwatch_logs")
            try:
                cw_logs_service = CloudWatchLogsService(db)
                
                # Create log group if not exists
                try:
                    cw_logs_service.create_log_group(
                        account_id=user["account_id"],
                        log_group_name=cw_logs_data["log_group"]
                    )
                except Exception:
                    pass  # Log group may already exist
                
                # Create log stream if not exists
                try:
                    cw_logs_service.create_log_stream(
                        account_id=user["account_id"],
                        log_group_name=cw_logs_data["log_group"],
                        log_stream_name=cw_logs_data["log_stream"]
                    )
                except Exception:
                    pass  # Log stream may already exist
                
                # Put log events
                if cw_logs_data["logs"]:
                    from datetime import datetime
                    timestamp = int(datetime.utcnow().timestamp() * 1000)
                    
                    # Split logs into lines
                    log_lines = cw_logs_data["logs"].split("\n")
                    events = [
                        {"timestamp": timestamp, "message": f"START RequestId: {cw_logs_data['request_id']}"}
                    ]
                    for line in log_lines:
                        if line.strip():
                            events.append({"timestamp": timestamp, "message": line})
                    events.append({"timestamp": timestamp, "message": f"END RequestId: {cw_logs_data['request_id']}"})
                    
                    cw_logs_service.put_log_events(
                        account_id=user["account_id"],
                        log_group_name=cw_logs_data["log_group"],
                        log_stream_name=cw_logs_data["log_stream"],
                        log_events=events
                    )
            except Exception as e:
                # Log error but don't fail invocation
                print(f"Failed to send logs to CloudWatch: {e}")
        
        # Send metrics to CloudWatch Metrics
        if "_cloudwatch_metrics" in result:
            cw_metrics_data = result.pop("_cloudwatch_metrics")
            try:
                cw_metrics_service = CloudWatchMetricsService(db)
                from datetime import datetime
                
                for metric in cw_metrics_data["metrics"]:
                    cw_metrics_service.put_metric_data(
                        account_id=user["account_id"],
                        namespace=cw_metrics_data["namespace"],
                        metric_name=metric["name"],
                        value=metric["value"],
                        unit=metric["unit"],
                        dimensions=metric["dimensions"],
                        timestamp=datetime.utcnow()
                    )
            except Exception as e:
                # Log error but don't fail invocation
                print(f"Failed to send metrics to CloudWatch: {e}")
        
        # Build response
        return InvokeFunctionResponse(
            status_code=result["StatusCode"],
            function_error=result.get("FunctionError"),
            log_result=result.get("LogResult"),
            payload=result["Payload"],
            executed_version=result["ExecutedVersion"]
        )
    
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

