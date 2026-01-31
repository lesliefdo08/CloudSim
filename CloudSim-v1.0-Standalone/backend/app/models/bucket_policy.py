"""
S3 Bucket Policy Model

Resource-based permissions for bucket access control.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.bucket import Bucket


class BucketPolicy(Base):
    """
    S3 Bucket Policy Model
    
    Resource-based permissions that define who can access a bucket
    and what actions they can perform. Similar to IAM policies but
    attached to buckets instead of users/groups.
    
    Attributes:
        policy_id: Unique policy identifier (bp-abc123def456)
        bucket_name: Bucket this policy applies to
        account_id: Owner account ID
        policy_document: JSON IAM policy document
        created_at: Policy creation timestamp
        updated_at: Last update timestamp
    
    Relationships:
        account: Owner account
        bucket: Target bucket
    
    Example Policy:
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "arn:aws:iam::123456789012:user/alice"},
                    "Action": ["s3:GetObject", "s3:PutObject"],
                    "Resource": "arn:aws:s3:::my-bucket/*"
                }
            ]
        }
    """
    
    __tablename__ = "bucket_policies"
    
    # Primary key
    policy_id: Mapped[str] = mapped_column(
        String(22),
        primary_key=True,
        comment="Unique policy ID (bp-abc123def456)"
    )
    
    # Foreign keys
    bucket_name: Mapped[str] = mapped_column(
        String(63),
        nullable=False,
        unique=True,  # One policy per bucket
        index=True,
        comment="Target bucket"
    )
    
    account_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        index=True,
        comment="Owner account ID"
    )
    
    # Policy content
    policy_document: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="JSON IAM policy document"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        comment="Creation timestamp"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default="CURRENT_TIMESTAMP",
        onupdate=datetime.utcnow,
        comment="Last update timestamp"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="bucket_policies",
        foreign_keys=[account_id]
    )
    
    bucket: Mapped["Bucket"] = relationship(
        "Bucket",
        back_populates="policy",
        foreign_keys=[bucket_name]
    )
    
    def __repr__(self) -> str:
        return f"<BucketPolicy(id={self.policy_id}, bucket={self.bucket_name})>"
