"""
Usage Metering - AWS-style usage tracking and billing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class MetricType(Enum):
    """Types of usage metrics"""
    # Compute metrics
    COMPUTE_HOURS = "compute.hours"
    COMPUTE_VCPU_HOURS = "compute.vcpu_hours"
    
    # Storage metrics
    STORAGE_GB_MONTH = "storage.gb_month"
    STORAGE_REQUESTS = "storage.requests"
    STORAGE_DATA_TRANSFER = "storage.data_transfer_gb"
    
    # Database metrics
    DATABASE_HOURS = "database.hours"
    DATABASE_IO_REQUESTS = "database.io_requests"
    DATABASE_STORAGE_GB = "database.storage_gb"
    
    # Serverless metrics
    FUNCTION_INVOCATIONS = "serverless.invocations"
    FUNCTION_DURATION_MS = "serverless.duration_ms"
    FUNCTION_MEMORY_MB_MS = "serverless.memory_mb_ms"


@dataclass
class UsageRecord:
    """Single usage record"""
    metric_type: MetricType
    resource_id: str
    resource_arn: str
    region: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    user: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "metricType": self.metric_type.value,
            "resourceId": self.resource_id,
            "resourceArn": self.resource_arn,
            "region": self.region,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "user": self.user,
            "tags": self.tags
        }


@dataclass
class UsageSummary:
    """Aggregated usage summary"""
    metric_type: MetricType
    region: str
    total_value: float
    unit: str
    resource_count: int
    start_time: datetime
    end_time: datetime
    breakdown: Dict[str, float] = field(default_factory=dict)  # By resource


class UsageMeter:
    """Tracks and aggregates usage metrics"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize usage meter"""
        self._records: List[UsageRecord] = []
        self._max_records = 10000  # Keep last 10k records
        
        # Active resource tracking for hourly metrics
        self._active_resources: Dict[str, datetime] = {}
    
    def record_usage(
        self,
        metric_type: MetricType,
        resource_id: str,
        resource_arn: str,
        region: str,
        value: float,
        unit: str,
        user: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ):
        """Record a usage metric"""
        record = UsageRecord(
            metric_type=metric_type,
            resource_id=resource_id,
            resource_arn=resource_arn,
            region=region,
            value=value,
            unit=unit,
            user=user,
            tags=tags or {}
        )
        
        self._records.append(record)
        
        # Maintain max records limit
        if len(self._records) > self._max_records:
            self._records.pop(0)
    
    def start_tracking(self, resource_id: str):
        """Start tracking a resource (for hourly metrics)"""
        self._active_resources[resource_id] = datetime.now()
    
    def stop_tracking(self, resource_id: str) -> Optional[float]:
        """Stop tracking a resource and return hours elapsed"""
        if resource_id in self._active_resources:
            start_time = self._active_resources.pop(resource_id)
            duration = datetime.now() - start_time
            return duration.total_seconds() / 3600  # Hours
        return None
    
    def get_usage_summary(
        self,
        metric_type: Optional[MetricType] = None,
        region: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[UsageSummary]:
        """Get aggregated usage summary"""
        # Filter records
        records = self._records
        
        if metric_type:
            records = [r for r in records if r.metric_type == metric_type]
        
        if region:
            records = [r for r in records if r.region == region]
        
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        
        # Group by metric type and region
        summaries = {}
        for record in records:
            key = (record.metric_type, record.region)
            if key not in summaries:
                summaries[key] = {
                    "total": 0,
                    "count": 0,
                    "resources": set(),
                    "breakdown": {}
                }
            
            summaries[key]["total"] += record.value
            summaries[key]["count"] += 1
            summaries[key]["resources"].add(record.resource_id)
            
            # Breakdown by resource
            if record.resource_id not in summaries[key]["breakdown"]:
                summaries[key]["breakdown"][record.resource_id] = 0
            summaries[key]["breakdown"][record.resource_id] += record.value
        
        # Convert to UsageSummary objects
        result = []
        for (metric_type, region), data in summaries.items():
            summary = UsageSummary(
                metric_type=metric_type,
                region=region,
                total_value=data["total"],
                unit=records[0].unit if records else "",
                resource_count=len(data["resources"]),
                start_time=start_time or (records[0].timestamp if records else datetime.now()),
                end_time=end_time or (records[-1].timestamp if records else datetime.now()),
                breakdown=data["breakdown"]
            )
            result.append(summary)
        
        return result
    
    def get_resource_usage(
        self,
        resource_id: str,
        metric_type: Optional[MetricType] = None
    ) -> List[UsageRecord]:
        """Get usage records for a specific resource"""
        records = [r for r in self._records if r.resource_id == resource_id]
        
        if metric_type:
            records = [r for r in records if r.metric_type == metric_type]
        
        return sorted(records, key=lambda r: r.timestamp, reverse=True)
    
    def get_current_month_usage(self, region: Optional[str] = None) -> List[UsageSummary]:
        """Get usage for current month"""
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        return self.get_usage_summary(region=region, start_time=start_of_month)
    
    def estimate_cost(self, usage_summary: UsageSummary) -> float:
        """
        Estimate cost for usage (simplified pricing model).
        In a real system, this would use actual AWS pricing.
        """
        # Simplified pricing
        pricing = {
            MetricType.COMPUTE_HOURS: 0.10,  # $0.10 per hour
            MetricType.STORAGE_GB_MONTH: 0.023,  # $0.023 per GB-month
            MetricType.DATABASE_HOURS: 0.15,  # $0.15 per hour
            MetricType.FUNCTION_INVOCATIONS: 0.0000002,  # $0.20 per 1M invocations
        }
        
        rate = pricing.get(usage_summary.metric_type, 0)
        return usage_summary.total_value * rate
    
    def clear_records(self):
        """Clear all usage records"""
        self._records.clear()
        self._active_resources.clear()


# Helper functions
def record_compute_usage(instance_id: str, region: str, vcpu: int, hours: float):
    """Record compute instance usage"""
    meter = UsageMeter()
    arn = f"arn:cloudsim:compute:{region}:instance/{instance_id}"
    
    meter.record_usage(
        MetricType.COMPUTE_HOURS,
        instance_id,
        arn,
        region,
        hours,
        "hours"
    )
    
    meter.record_usage(
        MetricType.COMPUTE_VCPU_HOURS,
        instance_id,
        arn,
        region,
        hours * vcpu,
        "vcpu-hours"
    )


def record_storage_usage(bucket_name: str, region: str, size_gb: float):
    """Record storage bucket usage"""
    meter = UsageMeter()
    arn = f"arn:cloudsim:storage:{region}:bucket/{bucket_name}"
    
    meter.record_usage(
        MetricType.STORAGE_GB_MONTH,
        bucket_name,
        arn,
        region,
        size_gb,
        "gb-month"
    )


def record_function_invocation(function_name: str, region: str, duration_ms: float, memory_mb: int):
    """Record serverless function invocation"""
    meter = UsageMeter()
    arn = f"arn:cloudsim:serverless:{region}:function/{function_name}"
    
    meter.record_usage(
        MetricType.FUNCTION_INVOCATIONS,
        function_name,
        arn,
        region,
        1,
        "invocations"
    )
    
    meter.record_usage(
        MetricType.FUNCTION_DURATION_MS,
        function_name,
        arn,
        region,
        duration_ms,
        "milliseconds"
    )
    
    meter.record_usage(
        MetricType.FUNCTION_MEMORY_MB_MS,
        function_name,
        arn,
        region,
        memory_mb * duration_ms,
        "mb-milliseconds"
    )
