"""
IAM User Model
Represents an IAM user with password and access key authentication
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.iam_group import Group
    from app.models.iam_policy import Policy
    from app.models.iam_access_key import AccessKey


# Association table for User ↔ Group (many-to-many)
user_groups = Table(
    "user_groups",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("group_id", String, ForeignKey("groups.group_id", ondelete="CASCADE"), primary_key=True),
    Column("added_at", DateTime, nullable=False, default=datetime.utcnow),
)


# Association table for User ↔ Policy (many-to-many for attached policies)
user_policies = Table(
    "user_policies",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
    Column("policy_id", String, ForeignKey("policies.policy_id", ondelete="CASCADE"), primary_key=True),
    Column("attached_at", DateTime, nullable=False, default=datetime.utcnow),
)


class User(Base, TimestampMixin):
    """
    IAM User
    
    Represents a person or service with persistent credentials.
    Supports both password-based (console) and access key-based (API) authentication.
    """
    
    __tablename__ = "users"
    
    # Primary key - AWS user ID format
    user_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="Unique user ID"
    )
    
    # Foreign key to account
    account_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Account this user belongs to"
    )
    
    # User identification
    username: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="IAM username (unique within account)"
    )
    
    # ARN
    arn: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="User ARN: arn:aws:iam::123456789012:user/alice"
    )
    
    # Path (for organizational grouping)
    path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="/",
        comment="Path prefix for organizational structure (e.g., /engineering/)"
    )
    
    # Password authentication
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Bcrypt password hash (null if password auth disabled)"
    )
    
    password_last_changed: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When password was last changed"
    )
    
    require_password_reset: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Force password reset on next login"
    )
    
    # Console access
    console_access_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether user can log into web console"
    )
    
    # MFA (placeholder for future)
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether MFA is enabled"
    )
    
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="TOTP secret for MFA (encrypted)"
    )
    
    # Activity tracking
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )
    
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last API/console activity"
    )
    
    # Inline policy (stored as JSON)
    inline_policy: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Inline IAM policy JSON (optional)"
    )
    
    # Status
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether user is active"
    )
    
    # Tags (JSON)
    tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="User tags as JSON"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship(
        "Account",
        back_populates="users"
    )
    
    groups: Mapped[list["Group"]] = relationship(
        "Group",
        secondary=user_groups,
        back_populates="users"
    )
    
    attached_policies: Mapped[list["Policy"]] = relationship(
        "Policy",
        secondary=user_policies,
        back_populates="attached_to_users"
    )
    
    access_keys: Mapped[list["AccessKey"]] = relationship(
        "AccessKey",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"
