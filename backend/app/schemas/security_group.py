"""
Security Group Schemas

Pydantic models for security group API requests and responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# === Request Schemas ===

class CreateSecurityGroupRequest(BaseModel):
    """Request to create a security group"""
    vpc_id: str = Field(..., description="VPC ID")
    group_name: str = Field(..., min_length=1, max_length=255, description="Security group name")
    description: Optional[str] = Field(None, max_length=500, description="Security group description")
    tags: Optional[dict] = Field(None, description="Tags")


class AuthorizeSecurityGroupRuleRequest(BaseModel):
    """Request to add a security group rule"""
    ip_protocol: str = Field(..., description="Protocol: tcp, udp, icmp, or -1 (all)")
    from_port: Optional[int] = Field(None, ge=1, le=65535, description="Start port (required for tcp/udp)")
    to_port: Optional[int] = Field(None, ge=1, le=65535, description="End port (required for tcp/udp)")
    cidr_ipv4: Optional[str] = Field(None, description="CIDR block (e.g., 0.0.0.0/0)")
    source_security_group_id: Optional[str] = Field(None, description="Source security group ID")
    description: Optional[str] = Field(None, max_length=500, description="Rule description")


# === Response Schemas ===

class SecurityGroupRuleResponse(BaseModel):
    """Security group rule response"""
    rule_id: str
    group_id: str
    rule_type: str  # 'ingress' or 'egress'
    ip_protocol: str
    from_port: Optional[int]
    to_port: Optional[int]
    cidr_ipv4: Optional[str]
    source_security_group_id: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SecurityGroupResponse(BaseModel):
    """Security group response"""
    group_id: str
    vpc_id: str
    group_name: str
    description: Optional[str]
    is_default: bool
    created_at: datetime
    rules: list[SecurityGroupRuleResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class ListSecurityGroupsResponse(BaseModel):
    """List security groups response"""
    security_groups: list[SecurityGroupResponse]
    total: int
