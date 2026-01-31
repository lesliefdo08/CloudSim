"""
IAM Account Model
Single account per deployment for now (multi-tenancy ready for future)
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.iam_user import User
    from app.models.iam_group import Group
    from app.models.iam_role import Role
    from app.models.iam_policy import Policy
    from app.models.vpc import VPC
    from app.models.ami import AMI
    from app.models.volume import Volume
    from app.models.snapshot import Snapshot
    from app.models.bucket import Bucket
    from app.models.s3_object import S3Object
    from app.models.bucket_policy import BucketPolicy


class Account(Base, TimestampMixin):
    """
    AWS Account equivalent
    
    Represents a single AWS account (tenant).
    For now, CloudSim runs with a single account, but model supports multi-tenancy.
    """
    
    __tablename__ = "accounts"
    
    # Primary key
    account_id: Mapped[str] = mapped_column(
        String(12),
        primary_key=True,
        comment="12-digit AWS account ID"
    )
    
    # Account details
    account_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        comment="Friendly account name"
    )
    
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Root account email"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="Account status: active, suspended, closed"
    )
    
    # ARN for account (for policy references)
    arn: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Account ARN: arn:aws:iam::123456789012:root"
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    groups: Mapped[list["Group"]] = relationship(
        "Group",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    policies: Mapped[list["Policy"]] = relationship(
        "Policy",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    vpcs: Mapped[list["VPC"]] = relationship(
        "VPC",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    amis: Mapped[list["AMI"]] = relationship(
        "AMI",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    volumes: Mapped[list["Volume"]] = relationship(
        "Volume",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    snapshots: Mapped[list["Snapshot"]] = relationship(
        "Snapshot",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    buckets: Mapped[list["Bucket"]] = relationship(
        "Bucket",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    s3_objects: Mapped[list["S3Object"]] = relationship(
        "S3Object",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    bucket_policies: Mapped[list["BucketPolicy"]] = relationship(
        "BucketPolicy",
        back_populates="account",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Account(account_id='{self.account_id}', name='{self.account_name}')>"
