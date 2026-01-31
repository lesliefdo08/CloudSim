"""
VPC and Subnet Schemas
Request/response models for VPC and Subnet operations
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class CreateVPCRequest(BaseModel):
    """Request to create VPC"""
    
    cidr_block: str = Field(..., description="VPC CIDR block (e.g., 10.0.0.0/16)")
    name: Optional[str] = Field(None, max_length=255)
    enable_dns_support: bool = Field(default=True)
    enable_dns_hostnames: bool = Field(default=False)
    tags: Optional[dict] = Field(default=None)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cidr_block": "10.0.0.0/16",
                "name": "production-vpc",
                "enable_dns_support": True,
                "enable_dns_hostnames": True,
                "tags": {"Environment": "Production"}
            }
        }
    )


class VPCResponse(BaseModel):
    """VPC response"""
    
    vpc_id: str
    cidr_block: str
    name: Optional[str] = None
    state: str
    is_default: bool
    enable_dns_support: bool
    enable_dns_hostnames: bool
    docker_network_id: Optional[str] = None
    docker_network_name: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ListVPCsResponse(BaseModel):
    """List VPCs response"""
    
    vpcs: List[VPCResponse]
    total: int


class CreateSubnetRequest(BaseModel):
    """Request to create subnet"""
    
    vpc_id: str = Field(..., description="VPC ID")
    cidr_block: str = Field(..., description="Subnet CIDR block (e.g., 10.0.1.0/24)")
    name: Optional[str] = Field(None, max_length=255)
    availability_zone: str = Field(default="us-east-1a")
    map_public_ip_on_launch: bool = Field(default=False)
    tags: Optional[dict] = Field(default=None)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vpc_id": "vpc-abc123def456",
                "cidr_block": "10.0.1.0/24",
                "name": "public-subnet-1a",
                "availability_zone": "us-east-1a",
                "map_public_ip_on_launch": True,
                "tags": {"Type": "Public"}
            }
        }
    )


class SubnetResponse(BaseModel):
    """Subnet response"""
    
    subnet_id: str
    vpc_id: str
    cidr_block: str
    name: Optional[str] = None
    state: str
    availability_zone: str
    available_ip_address_count: int
    map_public_ip_on_launch: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ListSubnetsResponse(BaseModel):
    """List subnets response"""
    
    subnets: List[SubnetResponse]
    total: int
