"""
Pydantic schemas for S3 advanced features (versioning, lifecycle, policies).
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==================== Versioning Schemas ====================

class VersioningConfiguration(BaseModel):
    """Bucket versioning configuration."""
    status: str = Field(..., description="Versioning status: Enabled or Suspended")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "Enabled"
            }
        }


class VersioningConfigurationResponse(BaseModel):
    """Response for get versioning configuration."""
    status: str = Field(..., description="Current versioning status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "Enabled"
            }
        }


class ObjectVersion(BaseModel):
    """Single object version information."""
    version_id: str = Field(..., description="Version ID")
    object_key: str = Field(..., description="Object key")
    is_latest: bool = Field(..., description="Whether this is the latest version")
    is_delete_marker: bool = Field(..., description="Whether this is a delete marker")
    size_bytes: int = Field(..., description="Object size in bytes")
    etag: str = Field(..., description="Object ETag")
    last_modified: datetime = Field(..., description="Last modification time")
    storage_class: str = Field(..., description="Storage class")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version_id": "3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d",
                "object_key": "documents/report.pdf",
                "is_latest": True,
                "is_delete_marker": False,
                "size_bytes": 1024000,
                "etag": "5d41402abc4b2a76b9719d911017c592",
                "last_modified": "2024-01-15T10:30:00Z",
                "storage_class": "STANDARD"
            }
        }


class ListObjectVersionsResponse(BaseModel):
    """Response for list object versions."""
    versions: List[ObjectVersion] = Field(default_factory=list, description="List of versions")
    object_key: str = Field(..., description="Object key")
    
    class Config:
        json_schema_extra = {
            "example": {
                "object_key": "documents/report.pdf",
                "versions": [
                    {
                        "version_id": "3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d",
                        "object_key": "documents/report.pdf",
                        "is_latest": True,
                        "is_delete_marker": False,
                        "size_bytes": 1024000,
                        "etag": "5d41402abc4b2a76b9719d911017c592",
                        "last_modified": "2024-01-15T10:30:00Z",
                        "storage_class": "STANDARD"
                    }
                ]
            }
        }


class DeleteVersionRequest(BaseModel):
    """Request to delete specific version."""
    version_id: str = Field(..., description="Version ID to delete")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version_id": "3a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d"
            }
        }


# ==================== Lifecycle Schemas ====================

class LifecycleExpiration(BaseModel):
    """Lifecycle expiration configuration."""
    days: int = Field(..., description="Days after creation to expire object", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "days": 90
            }
        }


class LifecycleTransition(BaseModel):
    """Lifecycle storage class transition."""
    days: int = Field(..., description="Days after creation to transition", gt=0)
    storage_class: str = Field(..., description="Target storage class")
    
    class Config:
        json_schema_extra = {
            "example": {
                "days": 30,
                "storage_class": "GLACIER"
            }
        }


class NoncurrentVersionExpiration(BaseModel):
    """Lifecycle expiration for noncurrent versions."""
    noncurrent_days: int = Field(..., description="Days after becoming noncurrent to expire", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "noncurrent_days": 30
            }
        }


class LifecycleRule(BaseModel):
    """Lifecycle rule definition."""
    id: str = Field(..., description="Rule ID")
    status: str = Field(..., description="Rule status: Enabled or Disabled")
    prefix: Optional[str] = Field(None, description="Object key prefix filter")
    expiration: Optional[LifecycleExpiration] = Field(None, description="Expiration action")
    transitions: Optional[List[LifecycleTransition]] = Field(None, description="Transition actions")
    noncurrent_version_expiration: Optional[NoncurrentVersionExpiration] = Field(
        None,
        description="Noncurrent version expiration"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "delete-old-logs",
                "status": "Enabled",
                "prefix": "logs/",
                "expiration": {
                    "days": 90
                }
            }
        }


class LifecycleConfiguration(BaseModel):
    """Bucket lifecycle configuration."""
    rules: List[LifecycleRule] = Field(..., description="Lifecycle rules")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rules": [
                    {
                        "id": "delete-old-logs",
                        "status": "Enabled",
                        "prefix": "logs/",
                        "expiration": {
                            "days": 90
                        }
                    },
                    {
                        "id": "archive-old-backups",
                        "status": "Enabled",
                        "prefix": "backups/",
                        "transitions": [
                            {
                                "days": 30,
                                "storage_class": "GLACIER"
                            }
                        ]
                    }
                ]
            }
        }


class LifecycleConfigurationResponse(BaseModel):
    """Response for get lifecycle configuration."""
    rules: List[LifecycleRule] = Field(default_factory=list, description="Lifecycle rules")
    
    class Config:
        json_schema_extra = {
            "example": {
                "rules": [
                    {
                        "id": "delete-old-logs",
                        "status": "Enabled",
                        "prefix": "logs/",
                        "expiration": {
                            "days": 90
                        }
                    }
                ]
            }
        }


class LifecycleEvaluationResult(BaseModel):
    """Result of lifecycle rule evaluation."""
    expired: List[str] = Field(default_factory=list, description="Object IDs to expire")
    transitioned: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Objects to transition with storage class"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "expired": ["obj-abc123", "obj-def456"],
                "transitioned": [
                    {
                        "object_id": "obj-ghi789",
                        "storage_class": "GLACIER"
                    }
                ]
            }
        }


# ==================== Bucket Policy Schemas ====================

class PolicyPrincipal(BaseModel):
    """IAM policy principal."""
    AWS: Optional[List[str]] = Field(None, description="AWS principal ARNs")
    
    class Config:
        json_schema_extra = {
            "example": {
                "AWS": ["arn:aws:iam::123456789012:user/alice"]
            }
        }


class PolicyStatement(BaseModel):
    """IAM policy statement."""
    Effect: str = Field(..., description="Statement effect: Allow or Deny")
    Principal: Any = Field(..., description="Principal (AWS ARNs or *)")
    Action: Any = Field(..., description="Action or actions (s3:* or list)")
    Resource: Any = Field(..., description="Resource ARN or ARNs")
    Condition: Optional[Dict[str, Any]] = Field(None, description="Optional conditions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "Effect": "Allow",
                "Principal": {
                    "AWS": "arn:aws:iam::123456789012:user/alice"
                },
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::my-bucket/*"
            }
        }


class BucketPolicyDocument(BaseModel):
    """Bucket policy document."""
    Version: str = Field(..., description="Policy version (2012-10-17)")
    Statement: List[PolicyStatement] = Field(..., description="Policy statements")
    
    class Config:
        json_schema_extra = {
            "example": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": "arn:aws:iam::123456789012:user/alice"
                        },
                        "Action": [
                            "s3:GetObject",
                            "s3:ListBucket"
                        ],
                        "Resource": [
                            "arn:aws:s3:::my-bucket",
                            "arn:aws:s3:::my-bucket/*"
                        ]
                    }
                ]
            }
        }


class BucketPolicyRequest(BaseModel):
    """Request to put bucket policy."""
    policy: BucketPolicyDocument = Field(..., description="Policy document")
    
    class Config:
        json_schema_extra = {
            "example": {
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": "arn:aws:iam::123456789012:user/alice"
                            },
                            "Action": "s3:GetObject",
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }
                    ]
                }
            }
        }


class BucketPolicyResponse(BaseModel):
    """Response for get bucket policy."""
    policy_id: str = Field(..., description="Policy ID")
    bucket_name: str = Field(..., description="Bucket name")
    policy: BucketPolicyDocument = Field(..., description="Policy document")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        json_schema_extra = {
            "example": {
                "policy_id": "bp-abc123def456",
                "bucket_name": "my-bucket",
                "policy": {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {
                                "AWS": "arn:aws:iam::123456789012:user/alice"
                            },
                            "Action": "s3:GetObject",
                            "Resource": "arn:aws:s3:::my-bucket/*"
                        }
                    ]
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class EvaluatePolicyRequest(BaseModel):
    """Request to evaluate bucket policy."""
    principal_arn: str = Field(..., description="Principal ARN to evaluate")
    action: str = Field(..., description="Action to check (e.g., s3:GetObject)")
    resource: str = Field(..., description="Resource ARN")
    
    class Config:
        json_schema_extra = {
            "example": {
                "principal_arn": "arn:aws:iam::123456789012:user/alice",
                "action": "s3:GetObject",
                "resource": "arn:aws:s3:::my-bucket/documents/report.pdf"
            }
        }


class EvaluatePolicyResponse(BaseModel):
    """Response for policy evaluation."""
    allowed: bool = Field(..., description="Whether the action is allowed")
    reason: Optional[str] = Field(None, description="Reason for the decision")
    
    class Config:
        json_schema_extra = {
            "example": {
                "allowed": True,
                "reason": "Explicit allow matched"
            }
        }
