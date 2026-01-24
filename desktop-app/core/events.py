"""
Event System - AWS-style event-driven architecture
"""

from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class EventType(Enum):
    """Types of resource events"""
    # Compute events
    INSTANCE_CREATED = "compute.instance.created"
    INSTANCE_STARTED = "compute.instance.started"
    INSTANCE_STOPPED = "compute.instance.stopped"
    INSTANCE_TERMINATED = "compute.instance.terminated"
    INSTANCE_STATE_CHANGED = "compute.instance.state_changed"
    
    # Storage events (S3-like)
    BUCKET_CREATED = "storage.bucket.created"
    BUCKET_DELETED = "storage.bucket.deleted"
    OBJECT_CREATED = "storage.object.created"
    OBJECT_DELETED = "storage.object.deleted"
    
    # Volume events (EBS-like)
    VOLUME_CREATED = "storage.volume.created"
    VOLUME_ATTACHED = "storage.volume.attached"
    VOLUME_DETACHED = "storage.volume.detached"
    VOLUME_DELETED = "storage.volume.deleted"
    SNAPSHOT_CREATED = "storage.snapshot.created"
    SNAPSHOT_DELETED = "storage.snapshot.deleted"
    
    # Database events
    DATABASE_CREATED = "database.database.created"
    DATABASE_DELETED = "database.database.deleted"
    TABLE_CREATED = "database.table.created"
    TABLE_DELETED = "database.table.deleted"
    QUERY_EXECUTED = "database.query.executed"
    
    # Serverless events
    FUNCTION_CREATED = "serverless.function.created"
    FUNCTION_INVOKED = "serverless.function.invoked"
    FUNCTION_DELETED = "serverless.function.deleted"
    FUNCTION_ERROR = "serverless.function.error"
    
    # IAM events
    USER_CREATED = "iam.user.created"
    POLICY_ATTACHED = "iam.policy.attached"


@dataclass
class Event:
    """Represents a system event with user context for activity logging"""
    event_type: EventType
    source: str  # Service name (e.g., "compute", "storage")
    region: str  # Region where event occurred
    resource_id: Optional[str] = None
    resource_arn: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Activity logging fields
    username: Optional[str] = None  # Who performed the action
    session_id: Optional[str] = None  # Session ID for tracking
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for logging"""
        return {
            "event_type": self.event_type.value,
            "source": self.source,
            "region": self.region,
            "resource_id": self.resource_id,
            "resource_arn": self.resource_arn,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "username": self.username,
            "session_id": self.session_id
        }
    
    def to_activity_log(self) -> str:
        """Generate human-readable activity log entry"""
        action = self.event_type.value.split('.')[-1]  # e.g., "created", "started"
        resource_type = self.event_type.value.split('.')[1]  # e.g., "instance", "bucket"
        user_info = f"{self.username}" if self.username else "unknown user"
        
        return f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {user_info} {action} {resource_type} {self.resource_id} in {self.region}"
    resource_id: str  # ID of affected resource
    resource_arn: str  # ARN of affected resource
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: f"evt-{datetime.now().timestamp()}")
    user: Optional[str] = None  # User who triggered the event
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        return {
            "eventId": self.event_id,
            "eventType": self.event_type.value,
            "source": self.source,
            "region": self.region,
            "resourceId": self.resource_id,
            "resourceArn": self.resource_arn,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "user": self.user
        }
    
    def to_json(self) -> str:
        """Convert event to JSON"""
        return json.dumps(self.to_dict(), indent=2)


EventHandler = Callable[[Event], None]


class EventBus:
    """Central event bus for event-driven architecture"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize event bus"""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000  # Keep last 1000 events
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe a handler from an event type"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    def publish(self, event: Event):
        """Publish an event to all subscribers"""
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notify handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    handler(event)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def get_events(
        self,
        event_type: Optional[EventType] = None,
        region: Optional[str] = None,
        resource_id: Optional[str] = None,
        username: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """Query event history with optional filtering by user"""
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if region:
            events = [e for e in events if e.region == region]
        
        if resource_id:
            events = [e for e in events if e.resource_id == resource_id]
        
        if username:
            events = [e for e in events if e.username == username]
        
        # Return most recent events
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_activity_log(
        self,
        username: Optional[str] = None,
        limit: int = 100
    ) -> List[str]:
        """Get human-readable activity log"""
        events = self.get_events(username=username, limit=limit)
        return [e.to_activity_log() for e in events]
    
    def clear_history(self):
        """Clear event history"""
        self._event_history.clear()


def emit_event(
    event_type: EventType,
    source: str,
    region: str,
    resource_id: str,
    resource_arn: str,
    details: Optional[Dict[str, Any]] = None
):
    """Convenience function to emit an event with automatic user context"""
    # Get current user context from IAM
    from core.iam import IAMManager
    iam = IAMManager()
    session = iam.get_session_context()
    
    event = Event(
        event_type=event_type,
        source=source,
        region=region,
        resource_id=resource_id,
        resource_arn=resource_arn,
        details=details or {},
        username=session.username if session else None,
        session_id=session.session_id if session else None
    )
    EventBus().publish(event)


# Example event handlers for logging
def log_event_handler(event: Event):
    """Simple logging handler"""
    print(f"[EVENT] {event.event_type.value} - {event.resource_id} in {event.region}")


def usage_tracking_handler(event: Event):
    """Handler for usage tracking"""
    # This would integrate with the metering system
    pass
