"""
CloudWatch Alarm Model
Represents a metric alarm with threshold and actions
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CloudWatchAlarm(Base):
    """
    CloudWatch alarm for metric monitoring.
    
    Alarms watch a metric and trigger actions when the metric
    breaches a threshold for a specified evaluation period.
    """
    
    __tablename__ = "cloudwatch_alarms"
    
    # Primary key
    alarm_id: Mapped[str] = mapped_column(String(30), primary_key=True)
    
    # Alarm identification
    alarm_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    alarm_description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Account ownership
    account_id: Mapped[str] = mapped_column(
        String(12),
        ForeignKey("iam_accounts.account_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Metric configuration
    namespace: Mapped[str] = mapped_column(String(255), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dimensions: Mapped[str] = mapped_column(Text, nullable=True)  # JSON encoded
    
    # Alarm configuration
    statistic: Mapped[str] = mapped_column(String(50), nullable=False)  # Average, Sum, Minimum, Maximum
    period: Mapped[int] = mapped_column(Integer, nullable=False)  # Seconds
    evaluation_periods: Mapped[int] = mapped_column(Integer, nullable=False)  # Number of periods
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    comparison_operator: Mapped[str] = mapped_column(String(50), nullable=False)  # GreaterThanThreshold, etc.
    
    # Optional settings
    treat_missing_data: Mapped[str] = mapped_column(String(50), nullable=False, default="missing")  # missing, notBreaching, breaching, ignore
    datapoints_to_alarm: Mapped[int] = mapped_column(Integer, nullable=True)  # M of N evaluation
    
    # Actions (JSON encoded list of action ARNs)
    alarm_actions: Mapped[str] = mapped_column(Text, nullable=True)  # Actions when ALARM state
    ok_actions: Mapped[str] = mapped_column(Text, nullable=True)  # Actions when OK state
    insufficient_data_actions: Mapped[str] = mapped_column(Text, nullable=True)  # Actions when INSUFFICIENT_DATA
    
    # State
    state_value: Mapped[str] = mapped_column(String(50), nullable=False, default="INSUFFICIENT_DATA")  # OK, ALARM, INSUFFICIENT_DATA
    state_reason: Mapped[str] = mapped_column(Text, nullable=True)
    state_updated_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Metadata
    actions_enabled: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite indexes
    __table_args__ = (
        Index('ix_cloudwatch_alarms_account_name', 'account_id', 'alarm_name', unique=True),
        Index('ix_cloudwatch_alarms_namespace_metric', 'namespace', 'metric_name'),
        Index('ix_cloudwatch_alarms_state', 'state_value'),
    )
    
    def __repr__(self):
        return f"<CloudWatchAlarm(name={self.alarm_name}, state={self.state_value})>"
