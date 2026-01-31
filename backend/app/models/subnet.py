"""
Subnet Model
"""

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Subnet(Base):
    """
    Subnet within a VPC
    Subdivides VPC CIDR block into smaller networks
    """
    
    __tablename__ = "subnets"
    
    # Primary Key
    subnet_id: Mapped[str] = mapped_column(String(24), primary_key=True)  # subnet-abc123def456
    
    # Foreign Keys
    vpc_id: Mapped[str] = mapped_column(String(21), ForeignKey("vpcs.vpc_id", ondelete="CASCADE"))
    account_id: Mapped[str] = mapped_column(String(12), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    
    # Subnet Configuration
    cidr_block: Mapped[str] = mapped_column(String(18), nullable=False)  # e.g., "10.0.1.0/24"
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    state: Mapped[str] = mapped_column(String(20), default="available")  # pending, available
    availability_zone: Mapped[str] = mapped_column(String(20), default="us-east-1a")
    
    # IP Configuration
    available_ip_address_count: Mapped[int] = mapped_column(Integer, nullable=False)
    map_public_ip_on_launch: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Tags
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vpc: Mapped["VPC"] = relationship("VPC", back_populates="subnets")
    account: Mapped["Account"] = relationship("Account")
    
    # Indexes
    __table_args__ = (
        Index("idx_subnet_vpc_id", "vpc_id"),
        Index("idx_subnet_account_id", "account_id"),
        Index("idx_subnet_cidr_block", "cidr_block"),
        Index("idx_subnet_state", "state"),
    )
    
    def __repr__(self) -> str:
        return f"<Subnet(subnet_id='{self.subnet_id}', vpc_id='{self.vpc_id}', cidr='{self.cidr_block}')>"
