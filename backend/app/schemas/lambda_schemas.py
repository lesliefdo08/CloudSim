"""
Lambda Schemas
Request and response models for Lambda API
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# Create Function
class CreateFunctionRequest(BaseModel):
    """Request to create a Lambda function."""
    function_name: str = Field(..., min_length=1, max_length=64)
    runtime: str = Field(..., description="Runtime environment (e.g., python3.11, nodejs20.x)")
    role: str = Field(..., description="ARN of execution role")
    handler: str = Field(..., max_length=128, description="Handler in format module.function")
    zip_file: str = Field(..., description="Base64-encoded ZIP file containing function code")
    description: Optional[str] = None
    timeout: int = Field(default=3, ge=1, le=900, description="Timeout in seconds")
    memory_size: int = Field(default=128, ge=128, le=10240, description="Memory in MB (multiple of 64)")
    environment: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    vpc_config: Optional[Dict[str, List[str]]] = Field(default=None, description="VPC configuration")
    tags: Optional[Dict[str, str]] = None


class FunctionConfiguration(BaseModel):
    """Lambda function configuration."""
    function_name: str
    function_arn: str
    runtime: str
    role: str
    handler: str
    code_sha256: str
    code_size: int
    description: Optional[str]
    timeout: int
    memory_size: int
    last_modified: str
    version: str
    state: str
    state_reason: Optional[str]
    environment: Optional[Dict[str, str]]


class CreateFunctionResponse(BaseModel):
    """Response from creating a function."""
    function: FunctionConfiguration


# Get Function
class GetFunctionRequest(BaseModel):
    """Request to get a function."""
    function_name: str = Field(..., min_length=1, max_length=64)


class GetFunctionResponse(BaseModel):
    """Response from getting a function."""
    configuration: FunctionConfiguration
    code: Dict[str, Any]


# List Functions
class ListFunctionsRequest(BaseModel):
    """Request to list functions."""
    max_items: Optional[int] = Field(default=50, ge=1, le=1000)


class ListFunctionsResponse(BaseModel):
    """Response from listing functions."""
    functions: List[FunctionConfiguration]


# Delete Function
class DeleteFunctionRequest(BaseModel):
    """Request to delete a function."""
    function_name: str = Field(..., min_length=1, max_length=64)


# Update Function Code
class UpdateFunctionCodeRequest(BaseModel):
    """Request to update function code."""
    function_name: str = Field(..., min_length=1, max_length=64)
    zip_file: str = Field(..., description="Base64-encoded ZIP file containing function code")


class UpdateFunctionCodeResponse(BaseModel):
    """Response from updating function code."""
    function: FunctionConfiguration


# Update Function Configuration
class UpdateFunctionConfigurationRequest(BaseModel):
    """Request to update function configuration."""
    function_name: str = Field(..., min_length=1, max_length=64)
    timeout: Optional[int] = Field(default=None, ge=1, le=900)
    memory_size: Optional[int] = Field(default=None, ge=128, le=10240)
    environment: Optional[Dict[str, str]] = None
    description: Optional[str] = None


class UpdateFunctionConfigurationResponse(BaseModel):
    """Response from updating function configuration."""
    function: FunctionConfiguration


# Invoke Function
class InvokeFunctionRequest(BaseModel):
    """Request to invoke a function."""
    function_name: str = Field(..., min_length=1, max_length=64)
    invocation_type: str = Field(default="RequestResponse", description="RequestResponse or Event")
    log_type: str = Field(default="None", description="None or Tail")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Input payload as JSON")


class InvokeFunctionResponse(BaseModel):
    """Response from invoking a function."""
    status_code: int
    function_error: Optional[str] = None
    log_result: Optional[str] = None
    payload: Any
    executed_version: str
