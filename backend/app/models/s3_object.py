"""
S3 Object Model

Represents an object stored in an S3 bucket with filesystem backing.
Stores metadata in database, actual content in filesystem.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Integer, Text, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.bucket import Bucket


class S3Object(Base):
    """
    S3 Object Model
    
    Represents an object stored in a bucket. The actual content is stored
    in the filesystem, while metadata is kept in the database.
    
    Attributes:
        object_id: Internal unique identifier (obj-abc123def456)
        bucket_name: Bucket containing this object
        object_key: Object key/path within bucket (e.g., folder/file.txt)
        account_id: Owner account ID
        size_bytes: Object size in bytes
        content_type: MIME type (e.g., application/json, image/png)
        etag: Entity tag for version/integrity checking
        filesystem_path: Absolute path to object file on filesystem
        storage_class: Storage class (STANDARD, GLACIER, etc.)
        version_id: Version identifier (if versioning enabled)
        metadata: JSON-encoded custom metadata
        tags: JSON-encoded tags
        created_at: Object upload timestamp
        last_modified: Last modification timestamp
    
    Relationships:
        account: Owner account
        bucket: Parent bucket
    
    Indexes:
        - bucket_name (for listing bucket objects)
        - account_id (for listing user's objects)
        - object_key (for lookups within bucket)
    
    Example:
        obj = S3Object(
            object_id="obj_abc123def456",
            bucket_name="my-data-bucket",
            object_key="data/report.pdf",
            account_id="acc_abc123",
            size_bytes=1024000,
            content_type="application/pdf",
            filesystem_path="/var/cloudsim/s3/.../data/report.pdf"
        )
    """
    
    __tablename__ = "s3_objects"
    
    # Primary key
    object_id: Mapped[str] = mapped_column(
        String(22),
        primary_key=True,
        comment="Unique object ID (obj-abc123def456)"
    )
    
    # Foreign keys
    bucket_name: Mapped[str] = mapped_column(
        String(63),
        nullable=False,
        index=True,
        comment="Bucket name"
    )
    
    account_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        index=True,
        comment="Owner account ID"
    )
    
    # Object identification
    object_key: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        index=True,
        comment="Object key/path (e.g., folder/file.txt)"
    )
    
    # Object properties
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Object size in bytes"
    )
    
    content_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default="application/octet-stream",
        comment="MIME type"
    )
    
    etag: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="Entity tag (MD5 hash)"
    )
    
    # Filesystem backing
    filesystem_path: Mapped[str] = mapped_column(
        String(1500),
        nullable=False,
        comment="Absolute path to object file"
    )
    
    # Storage configuration
    storage_class: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="STANDARD",
        comment="Storage class (STANDARD, GLACIER, etc.)"
    )
    
    version_id: Mapped[str] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="Version identifier"
    )
    
    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="Whether this is the latest version"
    )
    
    is_delete_marker: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether this is a delete marker (versioned delete)"
    )
    
    # Metadata
    object_metadata: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-encoded custom metadata"
    )
    
    tags: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="JSON-encoded tags"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        comment="Upload timestamp"
    )
    
    last_modified: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
        comment="Last modification timestamp"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="s3_objects",
        foreign_keys=[account_id]
    )
    
    bucket: Mapped["Bucket"] = relationship(
        "Bucket",
        back_populates="objects",
        foreign_keys=[bucket_name]
    )
    
    def __repr__(self) -> str:
        return f"<S3Object(id={self.object_id}, bucket={self.bucket_name}, key={self.object_key})>"
