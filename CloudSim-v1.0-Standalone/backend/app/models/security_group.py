"""
Security Group Model

Represents AWS-like security groups for controlling instance network traffic.
Each security group belongs to a VPC and contains rules for inbound/outbound traffic.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.vpc import VPC
    from app.models.iam_account import Account
    from app.models.security_group_rule import SecurityGroupRule


class SecurityGroup(Base):
    """
    Security Group Model
    
    AWS-compatible security group for instance-level firewall rules.
    """
    __tablename__ = "security_groups"
    
    # Primary key
    group_id: Mapped[str] = mapped_column(String(24), primary_key=True)  # sg-abc123def456
    
    # Foreign keys
    vpc_id: Mapped[str] = mapped_column(String(21), ForeignKey("vpcs.vpc_id", ondelete="CASCADE"))
    account_id: Mapped[str] = mapped_column(String(12), ForeignKey("accounts.account_id", ondelete="CASCADE"))
    
    # Basic fields
    group_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Metadata
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vpc: Mapped["VPC"] = relationship("VPC", back_populates="security_groups")
    account: Mapped["Account"] = relationship("Account")
    rules: Mapped[list["SecurityGroupRule"]] = relationship(
        "SecurityGroupRule",
        back_populates="security_group",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_sg_vpc_id", "vpc_id"),
        Index("idx_sg_account_id", "account_id"),
        Index("idx_sg_group_name", "group_name"),
    )
    
    def __repr__(self) -> str:
        return f"<SecurityGroup(id={self.group_id}, name={self.group_name}, vpc={self.vpc_id})>"
