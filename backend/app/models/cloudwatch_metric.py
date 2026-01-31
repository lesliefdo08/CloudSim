"""
CloudWatch Metric Model
Stores time-series metric data points
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Text, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CloudWatchMetric(Base):
    """
    CloudWatch metric data point.
    
    Stores time-series metrics with namespace, metric name, dimensions,
    timestamp, value, and unit.
    """
    
    __tablename__ = "cloudwatch_metrics"
    
    # Primary key
    metric_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    
    # Metric identification
    namespace: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    
    # Dimensions (JSON encoded: {"InstanceId": "i-abc123", "Region": "us-east-1"})
    dimensions: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamp and value
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Unit (Seconds, Bytes, Percent, Count, etc.)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Account ownership
    account_id: Mapped[str] = mapped_column(String(12), nullable=False, index=True)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Composite indexes for efficient querying
    __table_args__ = (
        Index('ix_cloudwatch_metrics_namespace_name', 'namespace', 'metric_name'),
        Index('ix_cloudwatch_metrics_namespace_name_time', 'namespace', 'metric_name', 'timestamp'),
        Index('ix_cloudwatch_metrics_account_namespace', 'account_id', 'namespace'),
    )
    
    def __repr__(self):
        return f"<CloudWatchMetric(id={self.metric_id}, namespace={self.namespace}, metric={self.metric_name}, value={self.value}, time={self.timestamp})>"
