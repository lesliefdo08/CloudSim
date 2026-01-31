"""
IAM Access Key Model
Programmatic access credentials (AWS CLI, SDK, API)
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.iam_user import User


class AccessKey(Base, TimestampMixin):
    """
    IAM Access Key
    
    Programmatic access credentials consisting of:
    - Access Key ID (public identifier)
    - Secret Access Key (private secret)
    
    Users can have up to 2 active access keys (for rotation).
    """
    
    __tablename__ = "access_keys"
    
    # Primary key - Access Key ID (AKIA...)
    access_key_id: Mapped[str] = mapped_column(
        String(20),
        primary_key=True,
        comment="Access Key ID: AKIAIOSFODNN7EXAMPLE"
    )
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this access key belongs to"
    )
    
    # Secret access key (hashed)
    secret_access_key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hash of secret access key (never store plaintext)"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Active",
        comment="Status: Active or Inactive"
    )
    
    # Activity tracking
    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this key was used"
    )
    
    last_used_service: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Last AWS service accessed with this key"
    )
    
    last_used_region: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Last region accessed with this key"
    )
    
    # Rotation
    last_rotated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last time this key was rotated"
    )
    
    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="access_keys"
    )
    
    def __repr__(self) -> str:
        return f"<AccessKey(access_key_id='{self.access_key_id}', user_id='{self.user_id}', status='{self.status}')>"
