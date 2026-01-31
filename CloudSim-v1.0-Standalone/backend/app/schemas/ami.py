"""
AMI Schemas

Request/response models for AMI endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CreateImageRequest(BaseModel):
    """Request to create AMI from instance"""
    instance_id: str = Field(..., description="Source instance ID")
    name: str = Field(..., min_length=1, max_length=255, description="AMI name")
    description: Optional[str] = Field(None, max_length=500, description="AMI description")
    tags: Optional[dict] = Field(None, description="Tags for the AMI")


class AMIResponse(BaseModel):
    """AMI response"""
    model_config = ConfigDict(from_attributes=True)
    
    ami_id: str
    account_id: str
    name: str
    description: Optional[str]
    source_instance_id: Optional[str]
    docker_image_id: Optional[str]
    docker_image_tag: Optional[str]
    state: str
    tags: Optional[str]
    created_at: datetime


class DescribeImagesResponse(BaseModel):
    """Response for describe images"""
    images: List[AMIResponse]
    total: int
