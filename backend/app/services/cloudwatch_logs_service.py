"""
CloudWatch Logs Service
Handles log groups, streams, and events
"""
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.log_group import LogGroup
from app.models.log_stream import LogStream, LogEvent
from app.models.instance import Instance
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.core.resource_ids import generate_id, ResourceType
import docker


class CloudWatchLogsService:
    """Service for CloudWatch Logs operations."""
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None
    
    # ==================== Log Groups ====================
    
    def create_log_group(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        retention_in_days: Optional[int] = None
    ) -> LogGroup:
        """
        Create a log group.
        
        Args:
            db: Database session
            account_id: Account ID
            log_group_name: Log group name (1-512 chars)
            retention_in_days: Retention period (1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653)
        
        Returns:
            Created log group
        
        Raises:
            ValidationError: If parameters invalid
            ResourceAlreadyExistsError: If log group exists
        """
        # Validate
        if not log_group_name or len(log_group_name) > 512:
            raise ValidationError("Log group name must be 1-512 characters")
        
        # Check if exists
        existing = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name,
            LogGroup.account_id == account_id
        ).first()
        
        if existing:
            raise ValidationError(f"Log group '{log_group_name}' already exists")
        
        # Validate retention
        if retention_in_days is not None:
            valid_retention = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]
            if retention_in_days not in valid_retention:
                raise ValidationError(f"Invalid retention period: {retention_in_days}")
        
        # Create log group
        log_group = LogGroup(
            log_group_name=log_group_name,
            account_id=account_id,
            retention_in_days=retention_in_days,
            created_at=datetime.utcnow(),
            stored_bytes=0
        )
        
        db.add(log_group)
        db.commit()
        db.refresh(log_group)
        
        return log_group
    
    def describe_log_groups(
        self,
        db: Session,
        account_id: str,
        log_group_name_prefix: Optional[str] = None,
        limit: int = 50
    ) -> List[LogGroup]:
        """List log groups."""
        query = db.query(LogGroup).filter(
            LogGroup.account_id == account_id
        )
        
        if log_group_name_prefix:
            query = query.filter(LogGroup.log_group_name.startswith(log_group_name_prefix))
        
        return query.limit(limit).all()
    
    def delete_log_group(
        self,
        db: Session,
        account_id: str,
        log_group_name: str
    ):
        """Delete a log group and all its streams."""
        log_group = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name,
            LogGroup.account_id == account_id
        ).first()
        
        if not log_group:
            raise ResourceNotFoundError(f"Log group '{log_group_name}' not found")
        
        db.delete(log_group)
        db.commit()
    
    def put_retention_policy(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        retention_in_days: int
    ) -> LogGroup:
        """Set retention policy for log group."""
        log_group = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name,
            LogGroup.account_id == account_id
        ).first()
        
        if not log_group:
            raise ResourceNotFoundError(f"Log group '{log_group_name}' not found")
        
        valid_retention = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653]
        if retention_in_days not in valid_retention:
            raise ValidationError(f"Invalid retention period: {retention_in_days}")
        
        log_group.retention_in_days = retention_in_days
        db.commit()
        db.refresh(log_group)
        
        return log_group
    
    # ==================== Log Streams ====================
    
    def create_log_stream(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        log_stream_name: str
    ) -> LogStream:
        """Create a log stream."""
        # Check log group exists
        log_group = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name,
            LogGroup.account_id == account_id
        ).first()
        
        if not log_group:
            raise ResourceNotFoundError(f"Log group '{log_group_name}' not found")
        
        # Check if stream exists
        existing = db.query(LogStream).filter(
            LogStream.log_group_name == log_group_name,
            LogStream.log_stream_name == log_stream_name
        ).first()
        
        if existing:
            raise ValidationError(f"Log stream '{log_stream_name}' already exists")
        
        # Create stream
        stream_id = generate_id(ResourceType.LOG_STREAM)
        
        log_stream = LogStream(
            stream_id=stream_id,
            log_group_name=log_group_name,
            log_stream_name=log_stream_name,
            account_id=account_id,
            created_at=datetime.utcnow(),
            stored_bytes=0
        )
        
        db.add(log_stream)
        db.commit()
        db.refresh(log_stream)
        
        return log_stream
    
    def describe_log_streams(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        log_stream_name_prefix: Optional[str] = None,
        order_by: str = "LastEventTime",
        descending: bool = True,
        limit: int = 50
    ) -> List[LogStream]:
        """List log streams in a group."""
        # Check log group exists
        log_group = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name,
            LogGroup.account_id == account_id
        ).first()
        
        if not log_group:
            raise ResourceNotFoundError(f"Log group '{log_group_name}' not found")
        
        query = db.query(LogStream).filter(
            LogStream.log_group_name == log_group_name
        )
        
        if log_stream_name_prefix:
            query = query.filter(LogStream.log_stream_name.startswith(log_stream_name_prefix))
        
        # Order by
        if order_by == "LastEventTime":
            if descending:
                query = query.order_by(LogStream.last_event_timestamp.desc())
            else:
                query = query.order_by(LogStream.last_event_timestamp.asc())
        elif order_by == "LogStreamName":
            if descending:
                query = query.order_by(LogStream.log_stream_name.desc())
            else:
                query = query.order_by(LogStream.log_stream_name.asc())
        
        return query.limit(limit).all()
    
    def delete_log_stream(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        log_stream_name: str
    ):
        """Delete a log stream."""
        log_stream = db.query(LogStream).filter(
            LogStream.log_group_name == log_group_name,
            LogStream.log_stream_name == log_stream_name,
            LogStream.account_id == account_id
        ).first()
        
        if not log_stream:
            raise ResourceNotFoundError(f"Log stream '{log_stream_name}' not found")
        
        db.delete(log_stream)
        db.commit()
    
    # ==================== Log Events ====================
    
    def put_log_events(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        log_stream_name: str,
        log_events: List[Dict[str, any]]
    ) -> Dict[str, str]:
        """
        Put log events into a stream.
        
        Args:
            db: Database session
            account_id: Account ID
            log_group_name: Log group name
            log_stream_name: Log stream name
            log_events: List of {"timestamp": datetime, "message": str}
        
        Returns:
            {"nextSequenceToken": str}
        """
        # Get log stream
        log_stream = db.query(LogStream).filter(
            LogStream.log_group_name == log_group_name,
            LogStream.log_stream_name == log_stream_name,
            LogStream.account_id == account_id
        ).first()
        
        if not log_stream:
            raise ResourceNotFoundError(f"Log stream '{log_stream_name}' not found")
        
        # Add events
        now = datetime.utcnow()
        total_bytes = 0
        
        for event_data in log_events:
            event_id = generate_id(ResourceType.LOG_GROUP)  # Reuse prefix
            
            event = LogEvent(
                event_id=event_id,
                stream_id=log_stream.stream_id,
                timestamp=event_data["timestamp"],
                message=event_data["message"],
                ingestion_time=now
            )
            
            db.add(event)
            
            # Calculate size
            message_bytes = len(event_data["message"].encode('utf-8'))
            total_bytes += message_bytes + 26  # +26 for overhead
            
            # Update stream timestamps
            if not log_stream.first_event_timestamp or event_data["timestamp"] < log_stream.first_event_timestamp:
                log_stream.first_event_timestamp = event_data["timestamp"]
            
            if not log_stream.last_event_timestamp or event_data["timestamp"] > log_stream.last_event_timestamp:
                log_stream.last_event_timestamp = event_data["timestamp"]
        
        log_stream.last_ingestion_time = now
        log_stream.stored_bytes += total_bytes
        
        # Update log group bytes
        log_group = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name
        ).first()
        if log_group:
            log_group.stored_bytes += total_bytes
        
        db.commit()
        
        return {"nextSequenceToken": "next-token"}
    
    def get_log_events(
        self,
        db: Session,
        account_id: str,
        log_group_name: str,
        log_stream_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        start_from_head: bool = True,
        limit: int = 10000
    ) -> List[Dict[str, any]]:
        """Get log events from a stream."""
        # Get log stream
        log_stream = db.query(LogStream).filter(
            LogStream.log_group_name == log_group_name,
            LogStream.log_stream_name == log_stream_name,
            LogStream.account_id == account_id
        ).first()
        
        if not log_stream:
            raise ResourceNotFoundError(f"Log stream '{log_stream_name}' not found")
        
        # Build query
        query = db.query(LogEvent).filter(
            LogEvent.stream_id == log_stream.stream_id
        )
        
        if start_time:
            query = query.filter(LogEvent.timestamp >= start_time)
        
        if end_time:
            query = query.filter(LogEvent.timestamp <= end_time)
        
        # Order
        if start_from_head:
            query = query.order_by(LogEvent.timestamp.asc())
        else:
            query = query.order_by(LogEvent.timestamp.desc())
        
        events = query.limit(limit).all()
        
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "message": event.message,
                "ingestionTime": event.ingestion_time.isoformat()
            }
            for event in events
        ]
    
    # ==================== Container Log Streaming ====================
    
    def stream_container_logs(
        self,
        db: Session,
        account_id: str,
        instance_id: str,
        follow: bool = False
    ):
        """
        Stream logs from a container to CloudWatch Logs.
        
        Creates log group/stream if they don't exist.
        
        Args:
            db: Database session
            account_id: Account ID
            instance_id: Instance ID
            follow: Whether to follow logs (streaming)
        
        Yields:
            Log lines
        """
        # Get instance
        instance = db.query(Instance).filter(
            Instance.instance_id == instance_id,
            Instance.account_id == account_id
        ).first()
        
        if not instance:
            raise ResourceNotFoundError(f"Instance {instance_id} not found")
        
        if instance.state != "running":
            raise ValidationError(f"Instance {instance_id} is not running")
        
        # Get container
        try:
            container = self.docker_client.containers.get(instance.container_id)
        except docker.errors.NotFound:
            raise ResourceNotFoundError(f"Container {instance.container_id} not found")
        
        # Ensure log group exists
        log_group_name = f"/aws/ec2/instances"
        log_group = db.query(LogGroup).filter(
            LogGroup.log_group_name == log_group_name,
            LogGroup.account_id == account_id
        ).first()
        
        if not log_group:
            log_group = self.create_log_group(db, account_id, log_group_name, retention_in_days=7)
        
        # Ensure log stream exists
        log_stream_name = instance_id
        log_stream = db.query(LogStream).filter(
            LogStream.log_group_name == log_group_name,
            LogStream.log_stream_name == log_stream_name
        ).first()
        
        if not log_stream:
            log_stream = self.create_log_stream(db, account_id, log_group_name, log_stream_name)
        
        # Stream logs
        for log_line in container.logs(stream=True, follow=follow, timestamps=True):
            line = log_line.decode('utf-8').strip()
            
            # Parse timestamp from Docker log format
            # Format: "2024-01-31T12:00:00.123456789Z message"
            try:
                timestamp_str, message = line.split(' ', 1)
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = datetime.utcnow()
                message = line
            
            # Store in database
            self.put_log_events(
                db,
                account_id,
                log_group_name,
                log_stream_name,
                [{"timestamp": timestamp, "message": message}]
            )
            
            yield line



