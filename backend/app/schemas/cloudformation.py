"""
CloudFormation Schemas
Request and response models for CloudFormation API
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


# Create Stack
class Parameter(BaseModel):
    """Stack parameter."""
    parameter_key: str
    parameter_value: str


class Tag(BaseModel):
    """Stack tag."""
    key: str
    value: str


class CreateStackRequest(BaseModel):
    """Request to create a CloudFormation stack."""
    stack_name: str = Field(..., min_length=1, max_length=128)
    template_body: str = Field(..., description="CloudFormation template (JSON or YAML)")
    parameters: Optional[List[Parameter]] = None
    disable_rollback: bool = False
    timeout_in_minutes: Optional[int] = None
    capabilities: Optional[List[str]] = None
    tags: Optional[List[Tag]] = None


class StackInfo(BaseModel):
    """CloudFormation stack information."""
    stack_name: str
    stack_id: str
    stack_status: str
    stack_status_reason: Optional[str]
    creation_time: str
    last_updated_time: Optional[str]
    deletion_time: Optional[str]
    disable_rollback: bool
    outputs: Optional[Dict[str, Any]]
    parameters: Optional[Dict[str, str]]
    tags: Optional[Dict[str, str]]


class CreateStackResponse(BaseModel):
    """Response from creating a stack."""
    stack_id: str
    stack_name: str


# Describe Stacks
class DescribeStacksRequest(BaseModel):
    """Request to describe stacks."""
    stack_name: Optional[str] = None


class DescribeStacksResponse(BaseModel):
    """Response from describing stacks."""
    stacks: List[StackInfo]


# Delete Stack
class DeleteStackRequest(BaseModel):
    """Request to delete a stack."""
    stack_name: str = Field(..., min_length=1, max_length=128)


# List Stack Resources
class ListStackResourcesRequest(BaseModel):
    """Request to list stack resources."""
    stack_name: str = Field(..., min_length=1, max_length=128)


class StackResourceInfo(BaseModel):
    """Stack resource information."""
    logical_resource_id: str
    physical_resource_id: Optional[str]
    resource_type: str
    resource_status: str
    resource_status_reason: Optional[str]
    timestamp: str
    last_updated_timestamp: Optional[str]


class ListStackResourcesResponse(BaseModel):
    """Response from listing stack resources."""
    stack_resources: List[StackResourceInfo]


# Validate Template
class ValidateTemplateRequest(BaseModel):
    """Request to validate a template."""
    template_body: str = Field(..., description="CloudFormation template (JSON or YAML)")


class TemplateParameter(BaseModel):
    """Template parameter definition."""
    parameter_key: str
    description: Optional[str]
    default_value: Optional[str]
    parameter_type: str


class ValidateTemplateResponse(BaseModel):
    """Response from validating a template."""
    valid: bool
    format: Optional[str] = None
    parameters: Optional[List[TemplateParameter]] = None
    resource_types: Optional[List[str]] = None
    error: Optional[str] = None


# Get Template
class GetTemplateRequest(BaseModel):
    """Request to get stack template."""
    stack_name: str = Field(..., min_length=1, max_length=128)


class GetTemplateResponse(BaseModel):
    """Response from getting template."""
    template_body: str
    template_format: str
