"""
IAM Policy Model
JSON document defining permissions (Allow/Deny actions on resources)
"""

from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.iam_user import User
    from app.models.iam_group import Group
    from app.models.iam_role import Role


class Policy(Base, TimestampMixin):
    """
    IAM Policy
    
    Defines permissions as JSON document with Allow/Deny statements.
    Can be attached to users, groups, or roles.
    Supports both AWS-managed (read-only templates) and customer-managed policies.
    """
    
    __tablename__ = "policies"
    
    # Primary key
    policy_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="Unique policy ID"
    )
    
    # Foreign key to account (null for AWS-managed policies)
    account_id: Mapped[Optional[str]] = mapped_column(
        String(12),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Account this policy belongs to (null for AWS-managed)"
    )
    
    # Policy identification
    policy_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="IAM policy name"
    )
    
    # ARN
    arn: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Policy ARN: arn:aws:iam::123456789012:policy/MyPolicy or arn:aws:iam::aws:policy/ReadOnlyAccess"
    )
    
    # Path (for organizational grouping)
    path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="/",
        comment="Path prefix for organizational structure"
    )
    
    # Description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Policy description"
    )
    
    # Policy document (JSON)
    policy_document: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="IAM policy JSON document with Version and Statement"
    )
    
    # Policy type
    is_aws_managed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is an AWS-managed policy (read-only template)"
    )
    
    # Version tracking
    version_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="v1",
        comment="Policy version identifier"
    )
    
    is_default_version: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this is the default (active) version"
    )
    
    # Attachment count (for tracking usage)
    attachment_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of entities this policy is attached to"
    )
    
    # Relationships
    account: Mapped[Optional["Account"]] = relationship(
        "Account",
        back_populates="policies"
    )
    
    attached_to_users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_policies",
        back_populates="attached_policies"
    )
    
    attached_to_groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary="group_policies",
        back_populates="attached_policies"
    )
    
    attached_to_roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary="role_policies",
        back_populates="attached_policies"
    )
    
    def __repr__(self) -> str:
        return f"<Policy(policy_id='{self.policy_id}', name='{self.policy_name}')>"
