"""
AMI (Amazon Machine Image) Model

Represents custom images created from instances.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account


class AMI(Base):
    """
    AMI Model
    
    Custom machine image created from instance snapshots.
    """
    __tablename__ = "amis"
    
    # Primary key
    ami_id: Mapped[str] = mapped_column(String(21), primary_key=True)  # ami-abc123def456
    
    # Foreign keys
    account_id: Mapped[str] = mapped_column(String(12), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    
    # AMI metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Source
    source_instance_id: Mapped[str] = mapped_column(String(19), nullable=True)  # Instance this was created from
    
    # Docker integration
    docker_image_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Docker image ID from commit
    docker_image_tag: Mapped[str] = mapped_column(String(255), nullable=True)  # cloudsim-ami-{ami_id}
    
    # State
    state: Mapped[str] = mapped_column(String(20), default="available")  # pending, available, failed, deregistered
    
    # Metadata
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account: Mapped["Account"] = relationship("Account")
    
    # Indexes
    __table_args__ = (
        Index("idx_ami_account_id", "account_id"),
        Index("idx_ami_state", "state"),
        Index("idx_ami_name", "name"),
    )
    
    def __repr__(self) -> str:
        return f"<AMI(id={self.ami_id}, name={self.name}, state={self.state})>"
