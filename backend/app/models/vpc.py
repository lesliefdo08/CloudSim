"""
VPC (Virtual Private Cloud) Model
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.iam_account import Account
    from app.models.subnet import Subnet
    from app.models.security_group import SecurityGroup


class VPC(Base):
    """
    Virtual Private Cloud
    Isolated network container for cloud resources
    """
    
    __tablename__ = "vpcs"
    
    # Primary Key
    vpc_id: Mapped[str] = mapped_column(String(21), primary_key=True)  # vpc-abc123def456
    
    # Foreign Keys
    account_id: Mapped[str] = mapped_column(String(12), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    
    # VPC Configuration
    cidr_block: Mapped[str] = mapped_column(String(18), nullable=False)  # e.g., "10.0.0.0/16"
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="available")  # pending, available
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # DNS Configuration
    enable_dns_support: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_dns_hostnames: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Docker Network Integration
    docker_network_id: Mapped[str] = mapped_column(String(64), nullable=True)  # Docker network ID
    docker_network_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Tags
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="vpcs")
    subnets: Mapped[list["Subnet"]] = relationship(
        "Subnet",
        back_populates="vpc",
        cascade="all, delete-orphan"
    )
    security_groups: Mapped[list["SecurityGroup"]] = relationship(
        "SecurityGroup",
        back_populates="vpc",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_vpc_account_id", "account_id"),
        Index("idx_vpc_cidr_block", "cidr_block"),
        Index("idx_vpc_state", "state"),
    )
    
    def __repr__(self) -> str:
        return f"<VPC(vpc_id='{self.vpc_id}', cidr='{self.cidr_block}', state='{self.state}')>"
