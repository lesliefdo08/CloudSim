"""
Instance Schemas

Pydantic models for EC2 instance API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# === Request Schemas ===

class RunInstancesRequest(BaseModel):
    """Request to launch EC2 instances"""
    image_id: Optional[str] = Field(None, description="Docker image (e.g., ubuntu:22.04)")
    ami_id: Optional[str] = Field(None, description="Custom AMI ID to launch from")
    instance_type: str = Field("t2.micro", description="Instance type")
    subnet_id: str = Field(..., description="Subnet ID")
    security_group_ids: Optional[List[str]] = Field(None, description="Security group IDs")
    key_name: Optional[str] = Field(None, description="SSH key pair name")
    user_data: Optional[str] = Field(None, description="User data script (base64 encoded)")
    tags: Optional[dict] = Field(None, description="Tags")
    min_count: int = Field(1, ge=1, le=10, description="Minimum instances to launch")
    max_count: int = Field(1, ge=1, le=10, description="Maximum instances to launch")


class InstanceActionRequest(BaseModel):
    """Request to perform action on instances"""
    instance_ids: List[str] = Field(..., min_length=1, description="List of instance IDs")


# === Response Schemas ===

class InstanceResponse(BaseModel):
    """EC2 instance response"""
    instance_id: str
    instance_type: str
    image_id: str
    state: str
    state_reason: Optional[str]
    subnet_id: str
    private_ip_address: Optional[str]
    public_ip_address: Optional[str]
    security_group_ids: Optional[str]  # Comma-separated
    docker_container_id: Optional[str]
    docker_container_name: Optional[str]
    key_name: Optional[str]
    launch_time: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DescribeInstancesResponse(BaseModel):
    """List instances response"""
    instances: List[InstanceResponse]
    total: int


class RunInstancesResponse(BaseModel):
    """Run instances response"""
    instances: List[InstanceResponse]


class InstanceStateChangeResponse(BaseModel):
    """Instance state change response"""
    instance_id: str
    current_state: str
    previous_state: Optional[str] = None


class InstanceActionResponse(BaseModel):
    """Response for instance actions (start/stop/terminate)"""
    starting_instances: Optional[List[InstanceStateChangeResponse]] = None
    stopping_instances: Optional[List[InstanceStateChangeResponse]] = None
    terminating_instances: Optional[List[InstanceStateChangeResponse]] = None
