"""
Pydantic schemas for CloudWatch metrics.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==================== Metric Data Schemas ====================

class MetricDatum(BaseModel):
    """Single metric data point for PutMetricData."""
    metric_name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str = Field(..., description="Unit (Percent, Bytes, Count, etc.)")
    timestamp: Optional[datetime] = Field(None, description="Timestamp (defaults to now)")
    dimensions: Optional[Dict[str, str]] = Field(None, description="Metric dimensions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "CPUUtilization",
                "value": 45.5,
                "unit": "Percent",
                "timestamp": "2024-01-31T12:00:00Z",
                "dimensions": {
                    "InstanceId": "i-abc123",
                    "InstanceType": "t2.micro"
                }
            }
        }


class PutMetricDataRequest(BaseModel):
    """Request to put metric data."""
    namespace: str = Field(..., description="Metric namespace (e.g., AWS/EC2)")
    metric_data: List[MetricDatum] = Field(..., description="List of metric data points")
    
    class Config:
        json_schema_extra = {
            "example": {
                "namespace": "AWS/EC2",
                "metric_data": [
                    {
                        "metric_name": "CPUUtilization",
                        "value": 45.5,
                        "unit": "Percent",
                        "dimensions": {
                            "InstanceId": "i-abc123"
                        }
                    }
                ]
            }
        }


class PutMetricDataResponse(BaseModel):
    """Response for PutMetricData."""
    message: str = Field(..., description="Success message")
    metrics_stored: int = Field(..., description="Number of metrics stored")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Metrics stored successfully",
                "metrics_stored": 1
            }
        }


# ==================== Get Statistics Schemas ====================

class GetMetricStatisticsRequest(BaseModel):
    """Request to get metric statistics."""
    namespace: str = Field(..., description="Metric namespace")
    metric_name: str = Field(..., description="Metric name")
    start_time: datetime = Field(..., description="Start of time range")
    end_time: datetime = Field(..., description="End of time range")
    period: int = Field(..., description="Period in seconds (60, 300, 3600, etc.)", ge=60)
    statistics: List[str] = Field(..., description="Statistics to compute")
    dimensions: Optional[Dict[str, str]] = Field(None, description="Dimension filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "namespace": "AWS/EC2",
                "metric_name": "CPUUtilization",
                "start_time": "2024-01-31T12:00:00Z",
                "end_time": "2024-01-31T13:00:00Z",
                "period": 300,
                "statistics": ["Average", "Maximum"],
                "dimensions": {
                    "InstanceId": "i-abc123"
                }
            }
        }


class Datapoint(BaseModel):
    """Single datapoint in metric statistics."""
    timestamp: str = Field(..., description="Datapoint timestamp")
    unit: str = Field(..., description="Metric unit")
    average: Optional[float] = Field(None, description="Average value")
    sum: Optional[float] = Field(None, description="Sum of values")
    minimum: Optional[float] = Field(None, description="Minimum value")
    maximum: Optional[float] = Field(None, description="Maximum value")
    sample_count: Optional[int] = Field(None, description="Number of samples")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-31T12:00:00",
                "unit": "Percent",
                "average": 45.5,
                "maximum": 67.2,
                "sample_count": 5
            }
        }


class GetMetricStatisticsResponse(BaseModel):
    """Response for GetMetricStatistics."""
    label: str = Field(..., description="Metric label")
    datapoints: List[Datapoint] = Field(..., description="List of datapoints")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "CPUUtilization",
                "datapoints": [
                    {
                        "timestamp": "2024-01-31T12:00:00",
                        "unit": "Percent",
                        "average": 45.5,
                        "maximum": 67.2,
                        "sample_count": 5
                    },
                    {
                        "timestamp": "2024-01-31T12:05:00",
                        "unit": "Percent",
                        "average": 52.3,
                        "maximum": 71.8,
                        "sample_count": 5
                    }
                ]
            }
        }


# ==================== List Metrics Schemas ====================

class ListMetricsRequest(BaseModel):
    """Request to list metrics."""
    namespace: Optional[str] = Field(None, description="Namespace filter")
    metric_name: Optional[str] = Field(None, description="Metric name filter")
    dimensions: Optional[Dict[str, str]] = Field(None, description="Dimension filters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "namespace": "AWS/EC2",
                "dimensions": {
                    "InstanceId": "i-abc123"
                }
            }
        }


class MetricDefinition(BaseModel):
    """Metric definition."""
    namespace: str = Field(..., description="Metric namespace")
    metric_name: str = Field(..., description="Metric name")
    dimensions: Dict[str, str] = Field(..., description="Metric dimensions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "namespace": "AWS/EC2",
                "metric_name": "CPUUtilization",
                "dimensions": {
                    "InstanceId": "i-abc123",
                    "InstanceType": "t2.micro"
                }
            }
        }


class ListMetricsResponse(BaseModel):
    """Response for ListMetrics."""
    metrics: List[MetricDefinition] = Field(..., description="List of metrics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metrics": [
                    {
                        "namespace": "AWS/EC2",
                        "metric_name": "CPUUtilization",
                        "dimensions": {
                            "InstanceId": "i-abc123"
                        }
                    },
                    {
                        "namespace": "AWS/EC2",
                        "metric_name": "MemoryUtilization",
                        "dimensions": {
                            "InstanceId": "i-abc123"
                        }
                    }
                ]
            }
        }


# ==================== Collect Metrics Schemas ====================

class CollectInstanceMetricsRequest(BaseModel):
    """Request to manually collect metrics for an instance."""
    instance_id: str = Field(..., description="Instance ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "instance_id": "i-abc123def456"
            }
        }


class CollectInstanceMetricsResponse(BaseModel):
    """Response for collect instance metrics."""
    message: str = Field(..., description="Success message")
    instance_id: str = Field(..., description="Instance ID")
    metrics_collected: int = Field(..., description="Number of metrics collected")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Metrics collected successfully",
                "instance_id": "i-abc123def456",
                "metrics_collected": 6
            }
        }
