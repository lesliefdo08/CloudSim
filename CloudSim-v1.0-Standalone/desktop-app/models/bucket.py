"""
Bucket Model - Represents an S3-like storage bucket with IAM support
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict
import os


@dataclass
class Bucket:
    """Storage bucket (S3-like) with region and owner tracking"""
    
    name: str
    created_at: str
    object_count: int = 0
    total_size: int = 0  # Size in bytes
    region: str = "us-east-1"  # AWS-style region
    owner: Optional[str] = None  # IAM username
    tags: Dict[str, str] = field(default_factory=dict)
    
    @staticmethod
    def create_new(name: str) -> 'Bucket':
        """Create a new bucket"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return Bucket(
            name=name,
            created_at=created_at,
            object_count=0,
            total_size=0,
            region="us-east-1",
            tags={}
        )
    
    def arn(self) -> str:
        """Generate AWS-style ARN for bucket"""
        return f"arn:cloudsim:storage:{self.region}:bucket/{self.name}"
    
    def to_dict(self) -> dict:
        """Convert bucket to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Bucket':
        """Create bucket from dictionary with backward compatibility"""
        # Backward compatibility for old buckets without region/owner
        if 'region' not in data:
            data['region'] = "us-east-1"
        if 'owner' not in data:
            data['owner'] = None
        if 'tags' not in data:
            data['tags'] = {}
        return Bucket(**data)


@dataclass
class S3Object:
    """Object stored in a bucket"""
    
    key: str  # Object name/path
    size: int  # Size in bytes
    last_modified: str
    bucket_name: str
    
    @staticmethod
    def create_new(key: str, size: int, bucket_name: str) -> 'S3Object':
        """Create a new object metadata"""
        last_modified = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return S3Object(
            key=key,
            size=size,
            last_modified=last_modified,
            bucket_name=bucket_name
        )
    
    def to_dict(self) -> dict:
        """Convert object to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'S3Object':
        """Create object from dictionary"""
        return S3Object(**data)
