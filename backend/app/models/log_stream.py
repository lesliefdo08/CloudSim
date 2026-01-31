"""
CloudWatch Log Stream Model
Represents a log stream within a log group
"""
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.log_group import LogGroup


class LogStream(Base):
    """
    CloudWatch log stream.
    
    A log stream is a sequence of log events from a single source
    (e.g., a specific EC2 instance or container).
    """
    
    __tablename__ = "log_streams"
    
    # Primary key
    stream_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Log stream identification
    log_group_name: Mapped[str] = mapped_column(
        String(512),
        ForeignKey("log_groups.log_group_name", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    log_stream_name: Mapped[str] = mapped_column(String(512), nullable=False)
    
    # Account ownership
    account_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("iam_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    first_event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_event_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    last_ingestion_time: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Storage
    stored_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    log_group: Mapped["LogGroup"] = relationship(
        "LogGroup",
        back_populates="log_streams"
    )
    
    # Composite indexes
    __table_args__ = (
        Index('ix_log_streams_group_stream', 'log_group_name', 'log_stream_name', unique=True),
        Index('ix_log_streams_account_group', 'account_id', 'log_group_name'),
    )
    
    def __repr__(self):
        return f"<LogStream(group={self.log_group_name}, stream={self.log_stream_name})>"


class LogEvent(Base):
    """
    Individual log event within a stream.
    """
    
    __tablename__ = "log_events"
    
    # Primary key
    event_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Log stream reference
    stream_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("log_streams.stream_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Event data
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Ingestion metadata
    ingestion_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Composite index for time-range queries
    __table_args__ = (
        Index('ix_log_events_stream_time', 'stream_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<LogEvent(stream={self.stream_id}, time={self.timestamp})>"
