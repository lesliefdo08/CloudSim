"""
S3 API Schemas

Request and response models for S3 operations.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# Bucket Schemas

class CreateBucketRequest(BaseModel):
    """Request to create a bucket."""
    
    bucket_name: str = Field(
        ...,
        min_length=3,
        max_length=63,
        description="Unique bucket name (3-63 chars, lowercase)"
    )
    region: str = Field(
        default="us-east-1",
        description="AWS region"
    )
    tags: Optional[dict] = Field(
        default=None,
        description="Bucket tags"
    )
    
    @field_validator("bucket_name")
    @classmethod
    def validate_bucket_name(cls, v: str) -> str:
        """Validate bucket name format."""
        if not v.islower():
            raise ValueError("Bucket name must be lowercase")
        if not v[0].isalnum() or not v[-1].isalnum():
            raise ValueError("Bucket name must start and end with letter or number")
        return v


class BucketResponse(BaseModel):
    """Bucket information."""
    
    bucket_name: str
    account_id: str
    region: str
    versioning_enabled: bool
    public_access_blocked: bool
    filesystem_path: str
    tags: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class ListBucketsResponse(BaseModel):
    """Response for list buckets operation."""
    
    buckets: list[BucketResponse]
    total: int


class DeleteBucketRequest(BaseModel):
    """Request to delete a bucket."""
    
    force: bool = Field(
        default=False,
        description="Force delete even if not empty"
    )


# Object Schemas

class PutObjectRequest(BaseModel):
    """Request to upload an object."""
    
    object_key: str = Field(
        ...,
        min_length=1,
        max_length=1024,
        description="Object key/path"
    )
    content_type: Optional[str] = Field(
        default=None,
        description="MIME type (auto-detected if not provided)"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Custom metadata"
    )
    tags: Optional[dict] = Field(
        default=None,
        description="Object tags"
    )


class ObjectResponse(BaseModel):
    """Object information."""
    
    object_id: str
    bucket_name: str
    account_id: str
    object_key: str
    size_bytes: int
    content_type: str
    etag: str
    filesystem_path: str
    storage_class: str
    version_id: Optional[str] = None
    metadata: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime
    last_modified: datetime
    
    model_config = {"from_attributes": True}


class ListObjectsRequest(BaseModel):
    """Request to list objects in a bucket."""
    
    prefix: Optional[str] = Field(
        default=None,
        description="Filter by key prefix (e.g., 'folder/')"
    )
    limit: int = Field(
        default=1000,
        ge=1,
        le=1000,
        description="Maximum results"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Pagination offset"
    )


class ListObjectsResponse(BaseModel):
    """Response for list objects operation."""
    
    objects: list[ObjectResponse]
    total: int
    bucket_name: str


class GetObjectResponse(BaseModel):
    """Response for get object operation (metadata only)."""
    
    object: ObjectResponse
    download_url: Optional[str] = None  # If we add presigned URLs


class DeleteObjectsRequest(BaseModel):
    """Request to delete multiple objects."""
    
    object_keys: list[str] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="List of object keys to delete"
    )


class DeleteObjectsResponse(BaseModel):
    """Response for delete objects operation."""
    
    deleted: list[str]
    errors: list[dict] = []
