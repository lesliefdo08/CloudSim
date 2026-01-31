"""
REST API routes for CloudWatch metrics.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError
)
from app.middleware.auth import get_current_user
from app.models.iam_user import User
from app.services.cloudwatch_service import CloudWatchService
from app.schemas.cloudwatch import (
    PutMetricDataRequest,
    PutMetricDataResponse,
    GetMetricStatisticsRequest,
    GetMetricStatisticsResponse,
    ListMetricsRequest,
    ListMetricsResponse,
    MetricDefinition,
    CollectInstanceMetricsRequest,
    CollectInstanceMetricsResponse
)

router = APIRouter(prefix="/cloudwatch", tags=["CloudWatch"])
cloudwatch_service = CloudWatchService()


# ==================== Put Metric Data ====================

@router.post(
    "/metrics",
    response_model=PutMetricDataResponse,
    summary="Put metric data",
    description="Store metric data points in CloudWatch"
)
def put_metric_data(
    request: PutMetricDataRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Store metric data points.
    
    Requires IAM permission: cloudwatch:PutMetricData
    """
    try:
        # Convert request to service format
        metric_data = [
            {
                "metric_name": datum.metric_name,
                "value": datum.value,
                "unit": datum.unit,
                "timestamp": datum.timestamp,
                "dimensions": datum.dimensions
            }
            for datum in request.metric_data
        ]
        
        # Store metrics
        metrics = cloudwatch_service.put_metric_data_batch(
            db,
            current_user.account_id,
            request.namespace,
            metric_data
        )
        
        return PutMetricDataResponse(
            message="Metrics stored successfully",
            metrics_stored=len(metrics)
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== Get Metric Statistics ====================

@router.post(
    "/metrics/statistics",
    response_model=GetMetricStatisticsResponse,
    summary="Get metric statistics",
    description="Get aggregated statistics for a metric over a time range"
)
def get_metric_statistics(
    request: GetMetricStatisticsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get metric statistics.
    
    Requires IAM permission: cloudwatch:GetMetricStatistics
    """
    try:
        result = cloudwatch_service.get_metric_statistics(
            db,
            current_user.account_id,
            request.namespace,
            request.metric_name,
            request.start_time,
            request.end_time,
            request.period,
            request.statistics,
            request.dimensions
        )
        
        return GetMetricStatisticsResponse(
            label=result["label"],
            datapoints=result["datapoints"]
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== List Metrics ====================

@router.get(
    "/metrics",
    response_model=ListMetricsResponse,
    summary="List metrics",
    description="List available metrics with optional filters"
)
def list_metrics(
    namespace: Optional[str] = Query(None, description="Namespace filter"),
    metric_name: Optional[str] = Query(None, description="Metric name filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List available metrics.
    
    Requires IAM permission: cloudwatch:ListMetrics
    """
    try:
        # Note: dimensions filter not supported via query params
        # Use POST endpoint if dimension filtering needed
        metrics = cloudwatch_service.list_metrics(
            db,
            current_user.account_id,
            namespace,
            metric_name,
            dimensions=None
        )
        
        metric_defs = [
            MetricDefinition(
                namespace=m["namespace"],
                metric_name=m["metric_name"],
                dimensions=m["dimensions"]
            )
            for m in metrics
        ]
        
        return ListMetricsResponse(metrics=metric_defs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post(
    "/metrics/list",
    response_model=ListMetricsResponse,
    summary="List metrics (with dimension filters)",
    description="List available metrics with dimension filters"
)
def list_metrics_post(
    request: ListMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List available metrics with dimension filters.
    
    Requires IAM permission: cloudwatch:ListMetrics
    """
    try:
        metrics = cloudwatch_service.list_metrics(
            db,
            current_user.account_id,
            request.namespace,
            request.metric_name,
            request.dimensions
        )
        
        metric_defs = [
            MetricDefinition(
                namespace=m["namespace"],
                metric_name=m["metric_name"],
                dimensions=m["dimensions"]
            )
            for m in metrics
        ]
        
        return ListMetricsResponse(metrics=metric_defs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ==================== Collect Instance Metrics ====================

@router.post(
    "/metrics/collect",
    response_model=CollectInstanceMetricsResponse,
    summary="Collect instance metrics",
    description="Manually trigger metric collection for an instance"
)
def collect_instance_metrics(
    request: CollectInstanceMetricsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually collect metrics from an instance.
    
    This is done automatically by the background worker,
    but can be triggered manually for testing.
    
    Requires IAM permission: ec2:DescribeInstances
    """
    try:
        metrics = cloudwatch_service.collect_instance_metrics(
            db,
            current_user.account_id,
            request.instance_id
        )
        
        return CollectInstanceMetricsResponse(
            message="Metrics collected successfully",
            instance_id=request.instance_id,
            metrics_collected=len(metrics)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

