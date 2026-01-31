"""
IAM Role Model
Assumable identity for temporary credentials (future: cross-service auth)
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.iam_policy import Policy


# Association table for Role ↔ Policy (many-to-many)
role_policies = Table(
    "role_policies",
    Base.metadata,
    Column("role_id", String, ForeignKey("roles.role_id", ondelete="CASCADE"), primary_key=True),
    Column("policy_id", String, ForeignKey("policies.policy_id", ondelete="CASCADE"), primary_key=True),
    Column("attached_at", DateTime, nullable=False, default=datetime.utcnow),
)


class Role(Base, TimestampMixin):
    """
    IAM Role
    
    Represents an assumable identity with temporary credentials.
    Used for service-to-service authentication and cross-account access.
    """
    
    __tablename__ = "roles"
    
    # Primary key
    role_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="Unique role ID"
    )
    
    # Foreign key to account
    account_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Account this role belongs to"
    )
    
    # Role identification
    role_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="IAM role name (unique within account)"
    )
    
    # ARN
    arn: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Role ARN: arn:aws:iam::123456789012:role/EC2InstanceRole"
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
        comment="Role description"
    )
    
    # Trust policy (who can assume this role)
    assume_role_policy: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Trust policy JSON defining who can assume this role"
    )
    
    # Inline policy (stored as JSON)
    inline_policy: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Inline IAM policy JSON (optional)"
    )
    
    # Session duration
    max_session_duration: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3600,
        comment="Maximum session duration in seconds (default 1 hour)"
    )
    
    # Tags (JSON)
    tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Role tags as JSON"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="roles"
    )
    
    attached_policies: Mapped[list["Policy"]] = relationship(
        "Policy",
        secondary=role_policies,
        back_populates="attached_to_roles"
    )
    
    def __repr__(self) -> str:
        return f"<Role(role_id='{self.role_id}', name='{self.role_name}')>"
