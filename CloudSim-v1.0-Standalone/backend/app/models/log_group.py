"""
CloudWatch Log Group Model
Represents a log group for organizing log streams
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.log_stream import LogStream


class LogGroup(Base):
    """
    CloudWatch log group.
    
    A log group is a collection of log streams that share the same
    retention, monitoring, and access control settings.
    """
    
    __tablename__ = "log_groups"
    
    # Primary key
    log_group_name: Mapped[str] = mapped_column(String(512), primary_key=True)
    
    # Account ownership
    account_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("iam_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Retention settings (days, None = never expire)
    retention_in_days: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    stored_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    log_streams: Mapped[list["LogStream"]] = relationship(
        "LogStream",
        back_populates="log_group",
        cascade="all, delete-orphan"
    )
    
    # Composite index for account queries
    __table_args__ = (
        Index('ix_log_groups_account_id_name', 'account_id', 'log_group_name'),
    )
    
    def __repr__(self):
        return f"<LogGroup(name={self.log_group_name}, account={self.account_id})>"
