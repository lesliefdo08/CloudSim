"""
Volume Model

EBS-like persistent block storage volumes.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account


class Volume(Base):
    """
    EBS Volume Model
    
    Represents a persistent block storage volume that can be attached to instances.
    Backed by Docker volumes for data persistence.
    """
    
    __tablename__ = "volumes"
    
    # Primary key
    volume_id: Mapped[str] = mapped_column(
        String(21),
        primary_key=True,
        comment="Volume ID (vol-abc123def456)"
    )
    
    # Foreign keys
    account_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        index=True,
        comment="Account ID"
    )
    
    # Volume configuration
    size_gb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Volume size in GB"
    )
    
    volume_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="gp2",
        comment="Volume type: gp2, gp3, io1, io2, st1, sc1"
    )
    
    # State
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="available",
        index=True,
        comment="Volume state: creating, available, in-use, deleting, deleted, error"
    )
    
    # Attachment
    attached_instance_id: Mapped[str] = mapped_column(
        String(19),
        nullable=True,
        comment="Instance ID if attached"
    )
    
    device_name: Mapped[str] = mapped_column(
        String(32),
        nullable=True,
        comment="Device name when attached (e.g., /dev/sdf)"
    )
    
    # Location
    availability_zone: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="Availability zone"
    )
    
    # Docker integration
    docker_volume_name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Docker volume name"
    )
    
    # Metadata
    tags: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="JSON tags"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Creation timestamp"
    )
    
    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="volumes")
    
    def __repr__(self) -> str:
        return f"<Volume(volume_id='{self.volume_id}', size={self.size_gb}GB, state='{self.state}')>"
