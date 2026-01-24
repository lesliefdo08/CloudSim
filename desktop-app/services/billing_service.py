"""
Billing Service - CloudTrail-style activity logging and cost estimation
Educational AWS-style billing with realistic pricing
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from utils.data_path import get_data_dir


class ResourceType(Enum):
    """Types of billable resources"""
    EC2_INSTANCE = "ec2_instance"
    EBS_VOLUME = "ebs_volume"
    S3_BUCKET = "s3_bucket"
    S3_STORAGE = "s3_storage"
    RDS_DATABASE = "rds_database"
    LAMBDA_FUNCTION = "lambda_function"
    DATA_TRANSFER = "data_transfer"


# Realistic AWS-style pricing (simplified for education)
PRICING = {
    # EC2 Instances (per hour)
    "ec2_t2.micro": 0.0116,
    "ec2_t2.small": 0.023,
    "ec2_t2.medium": 0.0464,
    "ec2_t3.micro": 0.0104,
    "ec2_t3.small": 0.0208,
    "ec2_t3.medium": 0.0416,
    "ec2_m5.large": 0.096,
    "ec2_m5.xlarge": 0.192,
    "ec2_c5.large": 0.085,
    
    # EBS Volumes (per GB per month)
    "ebs_gp2": 0.10,  # General Purpose SSD
    "ebs_gp3": 0.08,  # General Purpose SSD (newer)
    "ebs_io1": 0.125, # Provisioned IOPS SSD
    "ebs_st1": 0.045, # Throughput Optimized HDD
    
    # S3 Storage (per GB per month)
    "s3_standard": 0.023,
    "s3_intelligent_tiering": 0.0125,
    "s3_glacier": 0.004,
    
    # S3 Requests (per 1000 requests)
    "s3_put_request": 0.005,
    "s3_get_request": 0.0004,
    
    # RDS Databases (per hour)
    "rds_t2.micro": 0.017,
    "rds_t2.small": 0.034,
    "rds_t3.micro": 0.016,
    "rds_m5.large": 0.192,
    
    # Lambda (per invocation and GB-second)
    "lambda_request": 0.0000002,  # per request
    "lambda_duration": 0.0000166667,  # per GB-second
    
    # Data Transfer (per GB)
    "data_transfer_out": 0.09,  # First 10 TB/month
    "data_transfer_in": 0.0,  # Free
}


@dataclass
class ActivityLog:
    """CloudTrail-style activity log entry"""
    event_id: str
    timestamp: datetime
    user: str
    service: str
    action: str
    resource_type: str
    resource_id: str
    resource_name: str
    region: str
    status: str  # success, failed, denied
    details: Dict = field(default_factory=dict)
    cost_impact: float = 0.0  # Estimated cost impact of this action
    
    def to_dict(self) -> Dict:
        return {
            "eventId": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "user": self.user,
            "service": self.service,
            "action": self.action,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "resourceName": self.resource_name,
            "region": self.region,
            "status": self.status,
            "details": self.details,
            "costImpact": self.cost_impact
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActivityLog':
        return cls(
            event_id=data["eventId"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user=data["user"],
            service=data["service"],
            action=data["action"],
            resource_type=data["resourceType"],
            resource_id=data["resourceId"],
            resource_name=data["resourceName"],
            region=data["region"],
            status=data["status"],
            details=data.get("details", {}),
            cost_impact=data.get("costImpact", 0.0)
        )


@dataclass
class CostBreakdown:
    """Cost breakdown by service and resource"""
    service: str
    resource_type: str
    resource_count: int
    total_cost: float
    unit_cost: float
    usage_amount: float
    usage_unit: str
    details: List[Dict] = field(default_factory=list)


@dataclass
class BillingSummary:
    """Monthly billing summary"""
    month: str
    total_cost: float
    breakdown_by_service: Dict[str, float]
    breakdown_by_resource: List[CostBreakdown]
    total_resources: int
    billing_period_start: datetime
    billing_period_end: datetime
    forecasted_monthly_cost: float = 0.0


class BillingService:
    """Service for tracking costs and activity logs"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize billing service"""
        self.data_dir = get_data_dir()
        
        self.activity_log_file = self.data_dir / "activity_logs.json"
        self.cost_tracking_file = self.data_dir / "cost_tracking.json"
        
        self.activity_logs: List[ActivityLog] = []
        self.resource_start_times: Dict[str, datetime] = {}  # Track when resources started
        
        self._load_data()
    
    def _load_data(self):
        """Load activity logs and cost data"""
        # Load activity logs
        if self.activity_log_file.exists():
            try:
                with open(self.activity_log_file, 'r') as f:
                    data = json.load(f)
                    self.activity_logs = [ActivityLog.from_dict(log) for log in data]
            except Exception as e:
                print(f"Error loading activity logs: {e}")
                self.activity_logs = []
        
        # Load resource tracking
        if self.cost_tracking_file.exists():
            try:
                with open(self.cost_tracking_file, 'r') as f:
                    data = json.load(f)
                    self.resource_start_times = {
                        k: datetime.fromisoformat(v) 
                        for k, v in data.get("resourceStartTimes", {}).items()
                    }
            except Exception as e:
                print(f"Error loading cost tracking: {e}")
                self.resource_start_times = {}
    
    def _save_data(self):
        """Save activity logs and cost data"""
        # Save activity logs (keep last 1000 entries)
        logs_to_save = self.activity_logs[-1000:]
        with open(self.activity_log_file, 'w') as f:
            json.dump([log.to_dict() for log in logs_to_save], f, indent=2)
        
        # Save cost tracking
        with open(self.cost_tracking_file, 'w') as f:
            json.dump({
                "resourceStartTimes": {
                    k: v.isoformat() for k, v in self.resource_start_times.items()
                }
            }, f, indent=2)
    
    def log_activity(
        self,
        user: str,
        service: str,
        action: str,
        resource_type: str,
        resource_id: str,
        resource_name: str,
        region: str,
        status: str = "success",
        details: Optional[Dict] = None,
        cost_impact: float = 0.0
    ) -> ActivityLog:
        """Log an activity (CloudTrail-style)"""
        import secrets
        
        log = ActivityLog(
            event_id=f"event-{secrets.token_hex(8)}",
            timestamp=datetime.now(),
            user=user,
            service=service,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            region=region,
            status=status,
            details=details or {},
            cost_impact=cost_impact
        )
        
        self.activity_logs.append(log)
        self._save_data()
        
        return log
    
    def get_activity_logs(
        self,
        service: Optional[str] = None,
        user: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ActivityLog]:
        """Get filtered activity logs"""
        logs = self.activity_logs.copy()
        
        # Apply filters
        if service:
            logs = [log for log in logs if log.service.lower() == service.lower()]
        
        if user:
            logs = [log for log in logs if log.user == user]
        
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]
        
        # Sort by timestamp descending and limit
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]
    
    def track_resource_start(self, resource_id: str):
        """Track when a resource starts (for cost calculation)"""
        self.resource_start_times[resource_id] = datetime.now()
        self._save_data()
    
    def track_resource_stop(self, resource_id: str):
        """Track when a resource stops"""
        if resource_id in self.resource_start_times:
            del self.resource_start_times[resource_id]
            self._save_data()
    
    def calculate_resource_cost(
        self,
        resource_type: str,
        instance_type: Optional[str] = None,
        size_gb: Optional[float] = None,
        hours_running: Optional[float] = None,
        invocations: Optional[int] = None,
        gb_seconds: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Calculate cost for a resource
        Returns (cost, explanation)
        """
        if resource_type == "ec2_instance" and instance_type and hours_running:
            price_key = f"ec2_{instance_type}"
            if price_key in PRICING:
                cost = PRICING[price_key] * hours_running
                explanation = f"${PRICING[price_key]:.4f}/hour × {hours_running:.2f} hours"
                return cost, explanation
        
        elif resource_type == "ebs_volume" and instance_type and size_gb:
            price_key = f"ebs_{instance_type}"
            if price_key in PRICING:
                # Calculate monthly cost
                monthly_cost = PRICING[price_key] * size_gb
                explanation = f"${PRICING[price_key]:.4f}/GB/month × {size_gb} GB"
                return monthly_cost, explanation
        
        elif resource_type == "s3_storage" and size_gb:
            monthly_cost = PRICING["s3_standard"] * size_gb
            explanation = f"${PRICING['s3_standard']:.4f}/GB/month × {size_gb} GB"
            return monthly_cost, explanation
        
        elif resource_type == "rds_database" and instance_type and hours_running:
            price_key = f"rds_{instance_type}"
            if price_key in PRICING:
                cost = PRICING[price_key] * hours_running
                explanation = f"${PRICING[price_key]:.4f}/hour × {hours_running:.2f} hours"
                return cost, explanation
        
        elif resource_type == "lambda_function" and invocations and gb_seconds:
            request_cost = invocations * PRICING["lambda_request"]
            duration_cost = gb_seconds * PRICING["lambda_duration"]
            total_cost = request_cost + duration_cost
            explanation = f"{invocations} requests + {gb_seconds:.2f} GB-seconds"
            return total_cost, explanation
        
        return 0.0, "No cost data available"
    
    def get_current_month_summary(self) -> BillingSummary:
        """Get billing summary for current month"""
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Get all logs for this month
        month_logs = [
            log for log in self.activity_logs
            if log.timestamp >= start_of_month
        ]
        
        # Calculate costs by service
        breakdown_by_service = {}
        for log in month_logs:
            service = log.service
            if service not in breakdown_by_service:
                breakdown_by_service[service] = 0.0
            breakdown_by_service[service] += log.cost_impact
        
        total_cost = sum(breakdown_by_service.values())
        
        # Calculate forecasted monthly cost (simple projection)
        days_elapsed = (now - start_of_month).days + 1
        days_in_month = 30  # Simplified
        forecasted_cost = (total_cost / days_elapsed) * days_in_month if days_elapsed > 0 else 0
        
        return BillingSummary(
            month=now.strftime("%B %Y"),
            total_cost=total_cost,
            breakdown_by_service=breakdown_by_service,
            breakdown_by_resource=[],
            total_resources=len(self.resource_start_times),
            billing_period_start=start_of_month,
            billing_period_end=now,
            forecasted_monthly_cost=forecasted_cost
        )
    
    def get_service_activity_count(self) -> Dict[str, int]:
        """Get count of activities by service"""
        counts = {}
        for log in self.activity_logs:
            service = log.service
            counts[service] = counts.get(service, 0) + 1
        return counts
    
    def get_daily_costs(self, days: int = 30) -> List[Tuple[datetime, float]]:
        """Get daily cost breakdown for the last N days"""
        now = datetime.now()
        start_date = now - timedelta(days=days)
        
        # Group logs by day
        daily_costs = {}
        for log in self.activity_logs:
            if log.timestamp >= start_date:
                day = log.timestamp.date()
                if day not in daily_costs:
                    daily_costs[day] = 0.0
                daily_costs[day] += log.cost_impact
        
        # Convert to list of tuples
        result = []
        for i in range(days):
            day = (start_date + timedelta(days=i)).date()
            cost = daily_costs.get(day, 0.0)
            result.append((datetime.combine(day, datetime.min.time()), cost))
        
        return result


# Global singleton instance
billing_service = BillingService()


# Educational cost explanations
COST_EXPLANATIONS = {
    "ec2": """
    **EC2 Instance Pricing**
    
    Charges are calculated per-second with a 60-second minimum.
    Different instance types have different hourly rates based on:
    - CPU cores (vCPUs)
    - Memory (RAM)
    - Network performance
    - Instance generation (t2, t3, m5, etc.)
    
    💡 **Tip**: t3 instances are generally cheaper than t2 for same specs
    """,
    
    "ebs": """
    **EBS Volume Pricing**
    
    Charged per GB per month based on provisioned storage:
    - **gp3**: General Purpose SSD (newest, best value)
    - **gp2**: General Purpose SSD (older)
    - **io1**: Provisioned IOPS SSD (high performance)
    - **st1**: Throughput Optimized HDD (large sequential data)
    
    💡 **Tip**: You pay for provisioned space, not actual usage
    """,
    
    "s3": """
    **S3 Storage Pricing**
    
    Charged for:
    1. **Storage**: Per GB per month
    2. **Requests**: PUT, GET, DELETE operations
    3. **Data Transfer**: Outbound data transfer
    
    Storage classes have different rates:
    - Standard: Frequent access
    - Intelligent-Tiering: Automatic cost optimization
    - Glacier: Long-term archival (cheapest)
    
    💡 **Tip**: Data transfer IN is free, OUT is charged
    """,
    
    "rds": """
    **RDS Database Pricing**
    
    Charged per hour for running database instances:
    - Instance type determines hourly rate
    - Storage charged separately (per GB/month)
    - Backup storage (free up to DB size)
    - Multi-AZ doubles the cost
    
    💡 **Tip**: Stop dev/test databases when not in use
    """,
    
    "lambda": """
    **Lambda Pricing**
    
    Charged for:
    1. **Requests**: Per million requests
    2. **Duration**: Compute time in GB-seconds
       - Memory allocated × execution time
    
    First 1M requests and 400,000 GB-seconds are FREE each month!
    
    💡 **Tip**: Optimize memory allocation and execution time
    """,
    
    "data_transfer": """
    **Data Transfer Pricing**
    
    - **Inbound**: FREE
    - **Outbound**: Tiered pricing
      - First 10 TB/month: $0.09/GB
      - Next 40 TB/month: $0.085/GB
      - Higher volume: Even cheaper
    
    💡 **Tip**: Keep data in same region to avoid transfer costs
    """
}
