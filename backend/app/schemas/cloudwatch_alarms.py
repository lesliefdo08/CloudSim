"""
CloudWatch Alarms Schemas
Request/response models for CloudWatch Alarms APIs
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime


# ==================== Metric Alarms ====================

class PutMetricAlarmRequest(BaseModel):
    """Request to create or update a metric alarm."""
    alarm_name: str = Field(..., min_length=1, max_length=255)
    alarm_description: Optional[str] = Field(None, max_length=1024)
    actions_enabled: bool = Field(True)
    alarm_actions: Optional[List[str]] = Field(None, description="Actions when ALARM")
    ok_actions: Optional[List[str]] = Field(None, description="Actions when OK")
    insufficient_data_actions: Optional[List[str]] = Field(None, description="Actions when INSUFFICIENT_DATA")
    
    # Metric
    metric_name: str = Field(..., max_length=255)
    namespace: str = Field(..., max_length=255)
    dimensions: Optional[Dict[str, str]] = None
    
    # Alarm config
    statistic: str = Field(..., description="Average, Sum, Minimum, Maximum, SampleCount")
    period: int = Field(..., ge=60, description="Period in seconds (minimum 60)")
    evaluation_periods: int = Field(..., ge=1)
    threshold: float
    comparison_operator: str = Field(..., description="GreaterThanThreshold, LessThanThreshold, etc.")
    
    # Advanced
    datapoints_to_alarm: Optional[int] = Field(None, description="M of N evaluation")
    treat_missing_data: str = Field("missing", description="missing, notBreaching, breaching, ignore")


class PutMetricAlarmResponse(BaseModel):
    """Response from creating or updating an alarm."""
    message: str
    alarm_id: str
    alarm_name: str


class DescribeAlarmsRequest(BaseModel):
    """Request to describe alarms."""
    alarm_names: Optional[List[str]] = None
    alarm_name_prefix: Optional[str] = None
    state_value: Optional[str] = Field(None, description="OK, ALARM, or INSUFFICIENT_DATA")
    max_records: int = Field(100, ge=1, le=100)


class AlarmInfo(BaseModel):
    """Alarm information."""
    alarm_id: str
    alarm_name: str
    alarm_description: Optional[str]
    
    # Metric
    namespace: str
    metric_name: str
    dimensions: Optional[Dict[str, str]]
    
    # Config
    statistic: str
    period: int
    evaluation_periods: int
    threshold: float
    comparison_operator: str
    treat_missing_data: str
    datapoints_to_alarm: Optional[int]
    
    # Actions
    actions_enabled: bool
    alarm_actions: Optional[List[str]]
    ok_actions: Optional[List[str]]
    insufficient_data_actions: Optional[List[str]]
    
    # State
    state_value: str
    state_reason: Optional[str]
    state_updated_timestamp: datetime
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DescribeAlarmsResponse(BaseModel):
    """Response from describing alarms."""
    metric_alarms: List[AlarmInfo]


class DeleteAlarmsRequest(BaseModel):
    """Request to delete alarms."""
    alarm_names: List[str] = Field(..., min_items=1)


class DeleteAlarmsResponse(BaseModel):
    """Response from deleting alarms."""
    message: str
    deleted_count: int


class SetAlarmStateRequest(BaseModel):
    """Request to set alarm state."""
    alarm_name: str
    state_value: str = Field(..., description="OK, ALARM, or INSUFFICIENT_DATA")
    state_reason: str = Field(..., max_length=1024)


class SetAlarmStateResponse(BaseModel):
    """Response from setting alarm state."""
    message: str
    alarm_name: str
    state_value: str
