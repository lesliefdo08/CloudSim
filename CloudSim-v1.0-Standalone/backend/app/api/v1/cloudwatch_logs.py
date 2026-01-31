"""
CloudWatch Logs API Routes
IAM-protected endpoints for log groups, streams, and events
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.core.database import get_db
from app.models.iam_user import User
from app.services.cloudwatch_logs_service import CloudWatchLogsService
from app.schemas.cloudwatch_logs import *
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.api.v1.auth import get_current_user


router = APIRouter()
logs_service = CloudWatchLogsService()


# ==================== Log Groups ====================

@router.post("/logs/groups", response_model=CreateLogGroupResponse)
def create_log_group(
    request: CreateLogGroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a log group.
    Required IAM permission: logs:CreateLogGroup
    """
    try:
        log_group = logs_service.create_log_group(
            db,
            current_user.account_id,
            request.log_group_name,
            request.retention_in_days
        )
        
        return CreateLogGroupResponse(
            message=f"Log group '{request.log_group_name}' created successfully",
            log_group_name=log_group.log_group_name
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/groups/describe", response_model=DescribeLogGroupsResponse)
def describe_log_groups(
    request: DescribeLogGroupsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List log groups.
    Required IAM permission: logs:DescribeLogGroups
    """
    try:
        log_groups = logs_service.describe_log_groups(
            db,
            current_user.account_id,
            request.log_group_name_prefix,
            request.limit
        )
        
        return DescribeLogGroupsResponse(
            log_groups=[
                LogGroupInfo(
                    log_group_name=lg.log_group_name,
                    creation_time=lg.created_at,
                    retention_in_days=lg.retention_in_days,
                    stored_bytes=lg.stored_bytes
                )
                for lg in log_groups
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logs/groups", response_model=DeleteLogGroupResponse)
def delete_log_group(
    request: DeleteLogGroupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a log group.
    Required IAM permission: logs:DeleteLogGroup
    """
    try:
        logs_service.delete_log_group(
            db,
            current_user.account_id,
            request.log_group_name
        )
        
        return DeleteLogGroupResponse(
            message=f"Log group '{request.log_group_name}' deleted successfully"
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/logs/groups/retention", response_model=PutRetentionPolicyResponse)
def put_retention_policy(
    request: PutRetentionPolicyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Set retention policy for a log group.
    Required IAM permission: logs:PutRetentionPolicy
    """
    try:
        logs_service.put_retention_policy(
            db,
            current_user.account_id,
            request.log_group_name,
            request.retention_in_days
        )
        
        return PutRetentionPolicyResponse(
            message=f"Retention policy updated to {request.retention_in_days} days"
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Log Streams ====================

@router.post("/logs/streams", response_model=CreateLogStreamResponse)
def create_log_stream(
    request: CreateLogStreamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a log stream.
    Required IAM permission: logs:CreateLogStream
    """
    try:
        log_stream = logs_service.create_log_stream(
            db,
            current_user.account_id,
            request.log_group_name,
            request.log_stream_name
        )
        
        return CreateLogStreamResponse(
            message=f"Log stream '{request.log_stream_name}' created successfully",
            stream_id=log_stream.stream_id,
            log_stream_name=log_stream.log_stream_name
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/streams/describe", response_model=DescribeLogStreamsResponse)
def describe_log_streams(
    request: DescribeLogStreamsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List log streams.
    Required IAM permission: logs:DescribeLogStreams
    """
    try:
        log_streams = logs_service.describe_log_streams(
            db,
            current_user.account_id,
            request.log_group_name,
            request.log_stream_name_prefix,
            request.order_by,
            request.descending,
            request.limit
        )
        
        return DescribeLogStreamsResponse(
            log_streams=[
                LogStreamInfo(
                    stream_id=ls.stream_id,
                    log_stream_name=ls.log_stream_name,
                    creation_time=ls.created_at,
                    first_event_timestamp=ls.first_event_timestamp,
                    last_event_timestamp=ls.last_event_timestamp,
                    last_ingestion_time=ls.last_ingestion_time,
                    stored_bytes=ls.stored_bytes
                )
                for ls in log_streams
            ]
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/logs/streams", response_model=DeleteLogStreamResponse)
def delete_log_stream(
    request: DeleteLogStreamRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a log stream.
    Required IAM permission: logs:DeleteLogStream
    """
    try:
        logs_service.delete_log_stream(
            db,
            current_user.account_id,
            request.log_group_name,
            request.log_stream_name
        )
        
        return DeleteLogStreamResponse(
            message=f"Log stream '{request.log_stream_name}' deleted successfully"
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Log Events ====================

@router.post("/logs/events", response_model=PutLogEventsResponse)
def put_log_events(
    request: PutLogEventsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Put log events to a stream.
    Required IAM permission: logs:PutLogEvents
    """
    try:
        # Convert to dict format
        log_events = [
            {"timestamp": event.timestamp, "message": event.message}
            for event in request.log_events
        ]
        
        result = logs_service.put_log_events(
            db,
            current_user.account_id,
            request.log_group_name,
            request.log_stream_name,
            log_events
        )
        
        return PutLogEventsResponse(
            next_sequence_token=result["nextSequenceToken"]
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/logs/events/get", response_model=GetLogEventsResponse)
def get_log_events(
    request: GetLogEventsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get log events from a stream.
    Required IAM permission: logs:GetLogEvents
    """
    try:
        events = logs_service.get_log_events(
            db,
            current_user.account_id,
            request.log_group_name,
            request.log_stream_name,
            request.start_time,
            request.end_time,
            request.start_from_head,
            request.limit
        )
        
        return GetLogEventsResponse(
            events=[
                LogEventOutput(
                    timestamp=event["timestamp"],
                    message=event["message"],
                    ingestion_time=event["ingestionTime"]
                )
                for event in events
            ]
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

