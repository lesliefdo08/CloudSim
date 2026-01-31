"""
IAM User Management Schemas
Request/response models for IAM user operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CreateUserRequest(BaseModel):
    """Request to create IAM user"""
    
    username: str = Field(..., min_length=1, max_length=64)
    path: str = Field(default="/")
    password: Optional[str] = Field(None, min_length=8)
    console_access_enabled: bool = Field(default=True)
    require_password_reset: bool = Field(default=False)
    tags: Optional[dict] = Field(default=None)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "alice",
                "password": "TempPassword123!",
                "console_access_enabled": True,
                "require_password_reset": True
            }
        }
    )


class UpdateUserRequest(BaseModel):
    """Request to update IAM user"""
    
    new_username: Optional[str] = Field(None, max_length=64)
    new_path: Optional[str] = Field(None)
    enabled: Optional[bool] = Field(None)
    console_access_enabled: Optional[bool] = Field(None)


class UserResponse(BaseModel):
    """IAM user response"""
    
    user_id: str
    username: str
    arn: str
    path: str
    console_access_enabled: bool
    enabled: bool
    mfa_enabled: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ListUsersResponse(BaseModel):
    """List users response"""
    
    users: List[UserResponse]
    total: int


class CreateGroupRequest(BaseModel):
    """Request to create IAM group"""
    
    group_name: str = Field(..., min_length=1, max_length=128)
    path: str = Field(default="/")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "group_name": "Developers",
                "path": "/engineering/"
            }
        }
    )


class GroupResponse(BaseModel):
    """IAM group response"""
    
    group_id: str
    group_name: str
    arn: str
    path: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ListGroupsResponse(BaseModel):
    """List groups response"""
    
    groups: List[GroupResponse]
    total: int


class AddUserToGroupRequest(BaseModel):
    """Request to add user to group"""
    
    username: str
    group_name: str


class CreateAccessKeyRequest(BaseModel):
    """Request to create access key"""
    
    username: str


class AccessKeyResponse(BaseModel):
    """Access key response"""
    
    access_key_id: str
    secret_access_key: Optional[str] = Field(
        None,
        description="Only returned on creation"
    )
    status: str
    created_at: datetime
    last_used: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ListAccessKeysResponse(BaseModel):
    """List access keys response"""
    
    access_keys: List[AccessKeyResponse]
    total: int


class CreatePolicyRequest(BaseModel):
    """Request to create IAM policy"""
    
    policy_name: str = Field(..., min_length=1, max_length=128)
    path: str = Field(default="/")
    description: Optional[str] = None
    policy_document: dict = Field(..., description="Policy document JSON")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy_name": "EC2ReadOnly",
                "description": "Read-only access to EC2",
                "policy_document": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "ec2:Describe*",
                            "Resource": "*"
                        }
                    ]
                }
            }
        }
    )


class PolicyResponse(BaseModel):
    """IAM policy response"""
    
    policy_id: str
    policy_name: str
    arn: str
    path: str
    description: Optional[str] = None
    is_aws_managed: bool
    attachment_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ListPoliciesResponse(BaseModel):
    """List policies response"""
    
    policies: List[PolicyResponse]
    total: int


class AttachPolicyRequest(BaseModel):
    """Request to attach policy"""
    
    policy_arn: str


class DetachPolicyRequest(BaseModel):
    """Request to detach policy"""
    
    policy_arn: str
