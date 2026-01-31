"""
EC2 Instance Model

Represents AWS-like EC2 instances backed by Docker containers.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.subnet import Subnet
    from app.models.iam_account import Account


class Instance(Base):
    """
    EC2 Instance Model
    
    AWS-compatible EC2 instance backed by Docker container.
    """
    __tablename__ = "instances"
    
    # Primary key
    instance_id: Mapped[str] = mapped_column(String(19), primary_key=True)  # i-abc123def456
    
    # Foreign keys
    subnet_id: Mapped[str] = mapped_column(String(24), ForeignKey("subnets.subnet_id", ondelete="CASCADE"))
    account_id: Mapped[str] = mapped_column(String(12), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    
    # Instance configuration
    instance_type: Mapped[str] = mapped_column(String(20))  # t2.micro, t2.small, etc.
    image_id: Mapped[str] = mapped_column(String(100))  # ubuntu:22.04, amazonlinux:2, etc.
    
    # State
    state: Mapped[str] = mapped_column(String(20))  # pending, running, stopping, stopped, terminated
    state_reason: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Networking
    private_ip_address: Mapped[str] = mapped_column(String(15), nullable=True)  # 10.0.1.10
    public_ip_address: Mapped[str] = mapped_column(String(15), nullable=True)  # For future elastic IPs
    
    # Security groups (comma-separated group IDs)
    security_group_ids: Mapped[str] = mapped_column(Text, nullable=True)  # "sg-abc123,sg-def456"
    
    # Docker integration
    docker_container_id: Mapped[str] = mapped_column(String(64), nullable=True)
    docker_container_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Metadata
    key_name: Mapped[str] = mapped_column(String(255), nullable=True)  # SSH key pair name
    user_data: Mapped[str] = mapped_column(Text, nullable=True)  # User data script
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    
    # Timestamps
    launch_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subnet: Mapped["Subnet"] = relationship("Subnet")
    account: Mapped["Account"] = relationship("Account")
    
    # Indexes
    __table_args__ = (
        Index("idx_instance_account_id", "account_id"),
        Index("idx_instance_subnet_id", "subnet_id"),
        Index("idx_instance_state", "state"),
    )
    
    def __repr__(self) -> str:
        return f"<Instance(id={self.instance_id}, state={self.state}, type={self.instance_type})>"
