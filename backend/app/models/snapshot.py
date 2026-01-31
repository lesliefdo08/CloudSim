"""
Snapshot Model

Volume snapshots for backup and restore.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account


class Snapshot(Base):
    """
    EBS Snapshot Model
    
    Represents a point-in-time backup of a volume.
    """
    
    __tablename__ = "snapshots"
    
    # Primary key
    snapshot_id: Mapped[str] = mapped_column(
        String(22),
        primary_key=True,
        comment="Snapshot ID (snap-abc123def456)"
    )
    
    # Foreign keys
    account_id: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        index=True,
        comment="Account ID"
    )
    
    volume_id: Mapped[str] = mapped_column(
        String(21),
        nullable=False,
        index=True,
        comment="Source volume ID"
    )
    
    # Snapshot details
    size_gb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Snapshot size in GB (from source volume)"
    )
    
    state: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Snapshot state: pending, completed, error, deleting"
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="Snapshot description"
    )
    
    # Docker integration
    docker_volume_backup: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="Docker volume backup name"
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
    account: Mapped["Account"] = relationship("Account", back_populates="snapshots")
    
    def __repr__(self) -> str:
        return f"<Snapshot(snapshot_id='{self.snapshot_id}', volume_id='{self.volume_id}', state='{self.state}')>"
