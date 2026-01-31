"""
IAM Group Model
Collection of users for easier permission management
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, ForeignKey, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.iam_user import User
    from app.models.iam_policy import Policy


# Association table for Group ↔ Policy (many-to-many)
group_policies = Table(
    "group_policies",
    Base.metadata,
    Column("group_id", String, ForeignKey("groups.group_id", ondelete="CASCADE"), primary_key=True),
    Column("policy_id", String, ForeignKey("policies.policy_id", ondelete="CASCADE"), primary_key=True),
    Column("attached_at", DateTime, nullable=False, default=datetime.utcnow),
)


class Group(Base, TimestampMixin):
    """
    IAM Group
    
    Collection of users with shared permissions.
    Simplifies permission management by applying policies to groups instead of individual users.
    """
    
    __tablename__ = "groups"
    
    # Primary key
    group_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="Unique group ID"
    )
    
    # Foreign key to account
    account_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Account this group belongs to"
    )
    
    # Group identification
    group_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="IAM group name (unique within account)"
    )
    
    # ARN
    arn: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Group ARN: arn:aws:iam::123456789012:group/Developers"
    )
    
    # Path (for organizational grouping)
    path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="/",
        comment="Path prefix for organizational structure"
    )
    
    # Inline policy (stored as JSON)
    inline_policy: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Inline IAM policy JSON (optional)"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="groups"
    )
    
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_groups",
        back_populates="groups"
    )
    
    attached_policies: Mapped[list["Policy"]] = relationship(
        "Policy",
        secondary=group_policies,
        back_populates="attached_to_groups"
    )
    
    def __repr__(self) -> str:
        return f"<Group(group_id='{self.group_id}', name='{self.group_name}')>"
