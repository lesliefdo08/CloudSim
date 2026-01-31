"""
S3 Bucket Model

Represents an S3-like storage bucket with filesystem backing.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.s3_object import S3Object
    from app.models.bucket_policy import BucketPolicy


class Bucket(Base):
    """
    S3 Bucket Model
    
    Represents a bucket for object storage. Each bucket has a unique name
    within the account and stores objects in the filesystem.
    
    Attributes:
        bucket_name: Unique bucket name (3-63 chars, lowercase, no special chars except -)
        account_id: Owner account ID
        region: AWS region (e.g., us-east-1)
        versioning_enabled: Whether object versioning is enabled
        public_access_blocked: Whether public access is blocked (default True)
        filesystem_path: Absolute path to bucket directory on filesystem
        tags: JSON-encoded tags
        created_at: Bucket creation timestamp
    
    Relationships:
        account: Owner account
        objects: Objects stored in this bucket
    
    Indexes:
        - account_id (for listing user's buckets)
        - bucket_name (for unique constraint and lookups)
    
    Example:
        bucket = Bucket(
            bucket_name="my-data-bucket",
            account_id="acc_abc123",
            region="us-east-1",
            filesystem_path="/var/cloudsim/s3/acc_abc123/my-data-bucket"
        )
    """
    
    __tablename__ = "buckets"
    
    # Primary key
    bucket_name: Mapped[str] = mapped_column(
        String(63), 
        primary_key=True,
        comment="Unique bucket name (3-63 chars)"
    )
    
    # Foreign keys
    account_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        index=True,
        comment="Owner account ID"
    )
    
    # Bucket configuration
    region: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="us-east-1",
        comment="AWS region"
    )
    
    versioning_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether versioning is enabled"
    )
    
    public_access_blocked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Block all public access"
    )
    
    # Lifecycle configuration
    lifecycle_rules: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-encoded lifecycle rules"
    )
    
    # Filesystem backing
    filesystem_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Absolute path to bucket directory"
    )
    
    # Metadata
    tags: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-encoded tags"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        comment="Bucket creation timestamp"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="buckets",
        foreign_keys=[account_id]
    )
    
    objects: Mapped[list["S3Object"]] = relationship(
        "S3Object",
        back_populates="bucket",
        cascade="all, delete-orphan",
        foreign_keys="S3Object.bucket_name"
    )
    
    policy: Mapped["BucketPolicy"] = relationship(
        "BucketPolicy",
        back_populates="bucket",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="BucketPolicy.bucket_name"
    )
    
    def __repr__(self) -> str:
        return f"<Bucket(name={self.bucket_name}, account={self.account_id}, region={self.region})>"
