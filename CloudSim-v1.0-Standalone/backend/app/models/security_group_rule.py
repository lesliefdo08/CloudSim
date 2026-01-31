"""
Security Group Rule Model

Represents individual firewall rules within a security group.
Each rule defines protocol, port range, and source/destination.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.security_group import SecurityGroup


class SecurityGroupRule(Base):
    """
    Security Group Rule Model
    
    Individual rule for controlling traffic (ingress or egress).
    """
    __tablename__ = "security_group_rules"
    
    # Primary key
    rule_id: Mapped[str] = mapped_column(String(32), primary_key=True)  # sgr-abc123def456
    
    # Foreign key
    group_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("security_groups.group_id", ondelete="CASCADE")
    )
    
    # Rule type
    rule_type: Mapped[str] = mapped_column(String(10))  # 'ingress' or 'egress'
    
    # Protocol and ports
    ip_protocol: Mapped[str] = mapped_column(String(10))  # 'tcp', 'udp', 'icmp', '-1' (all)
    from_port: Mapped[int] = mapped_column(Integer, nullable=True)  # Start port (null for ICMP/all)
    to_port: Mapped[int] = mapped_column(Integer, nullable=True)    # End port (null for ICMP/all)
    
    # Source/Destination
    cidr_ipv4: Mapped[str] = mapped_column(String(18), nullable=True)  # CIDR block (e.g., 0.0.0.0/0)
    source_security_group_id: Mapped[str] = mapped_column(String(24), nullable=True)  # Reference to another SG
    
    # Metadata
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    security_group: Mapped["SecurityGroup"] = relationship(
        "SecurityGroup",
        back_populates="rules"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_sgr_group_id", "group_id"),
        Index("idx_sgr_rule_type", "rule_type"),
    )
    
    def __repr__(self) -> str:
        return f"<SecurityGroupRule(id={self.rule_id}, type={self.rule_type}, protocol={self.ip_protocol})>"
