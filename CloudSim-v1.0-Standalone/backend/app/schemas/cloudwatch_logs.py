"""
CloudWatch Logs Schemas
Request/response models for CloudWatch Logs APIs
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== Log Groups ====================

class CreateLogGroupRequest(BaseModel):
    """Request to create a log group."""
    log_group_name: str = Field(..., min_length=1, max_length=512)
    retention_in_days: Optional[int] = Field(None, description="Retention in days (1,3,5,7,14,30,60,90,120,150,180,365,400,545,731,1827,3653)")


class CreateLogGroupResponse(BaseModel):
    """Response from creating a log group."""
    message: str
    log_group_name: str


class DescribeLogGroupsRequest(BaseModel):
    """Request to list log groups."""
    log_group_name_prefix: Optional[str] = None
    limit: int = Field(50, ge=1, le=100)


class LogGroupInfo(BaseModel):
    """Log group information."""
    log_group_name: str
    creation_time: datetime
    retention_in_days: Optional[int]
    stored_bytes: int
    
    class Config:
        from_attributes = True


class DescribeLogGroupsResponse(BaseModel):
    """Response from listing log groups."""
    log_groups: List[LogGroupInfo]


class DeleteLogGroupRequest(BaseModel):
    """Request to delete a log group."""
    log_group_name: str


class DeleteLogGroupResponse(BaseModel):
    """Response from deleting a log group."""
    message: str


class PutRetentionPolicyRequest(BaseModel):
    """Request to set retention policy."""
    log_group_name: str
    retention_in_days: int


class PutRetentionPolicyResponse(BaseModel):
    """Response from setting retention policy."""
    message: str


# ==================== Log Streams ====================

class CreateLogStreamRequest(BaseModel):
    """Request to create a log stream."""
    log_group_name: str
    log_stream_name: str = Field(..., min_length=1, max_length=512)


class CreateLogStreamResponse(BaseModel):
    """Response from creating a log stream."""
    message: str
    stream_id: str
    log_stream_name: str


class DescribeLogStreamsRequest(BaseModel):
    """Request to list log streams."""
    log_group_name: str
    log_stream_name_prefix: Optional[str] = None
    order_by: str = Field("LastEventTime", description="LastEventTime or LogStreamName")
    descending: bool = Field(True)
    limit: int = Field(50, ge=1, le=100)


class LogStreamInfo(BaseModel):
    """Log stream information."""
    stream_id: str
    log_stream_name: str
    creation_time: datetime
    first_event_timestamp: Optional[datetime]
    last_event_timestamp: Optional[datetime]
    last_ingestion_time: Optional[datetime]
    stored_bytes: int
    
    class Config:
        from_attributes = True


class DescribeLogStreamsResponse(BaseModel):
    """Response from listing log streams."""
    log_streams: List[LogStreamInfo]


class DeleteLogStreamRequest(BaseModel):
    """Request to delete a log stream."""
    log_group_name: str
    log_stream_name: str


class DeleteLogStreamResponse(BaseModel):
    """Response from deleting a log stream."""
    message: str


# ==================== Log Events ====================

class LogEventInput(BaseModel):
    """Log event input."""
    timestamp: datetime
    message: str = Field(..., max_length=262144)  # 256KB


class PutLogEventsRequest(BaseModel):
    """Request to put log events."""
    log_group_name: str
    log_stream_name: str
    log_events: List[LogEventInput]


class PutLogEventsResponse(BaseModel):
    """Response from putting log events."""
    next_sequence_token: str
    rejected_log_events_info: Optional[dict] = None


class GetLogEventsRequest(BaseModel):
    """Request to get log events."""
    log_group_name: str
    log_stream_name: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    start_from_head: bool = Field(True, description="If true, oldest first; if false, newest first")
    limit: int = Field(100, ge=1, le=10000)


class LogEventOutput(BaseModel):
    """Log event output."""
    timestamp: datetime
    message: str
    ingestion_time: datetime


class GetLogEventsResponse(BaseModel):
    """Response from getting log events."""
    events: List[LogEventOutput]
    next_forward_token: Optional[str] = None
    next_backward_token: Optional[str] = None
