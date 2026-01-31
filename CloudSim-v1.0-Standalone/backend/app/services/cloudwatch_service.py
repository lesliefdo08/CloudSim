"""
CloudWatch Service
Handles metric collection, storage, and retrieval
"""
import json
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.cloudwatch_metric import CloudWatchMetric
from app.models.instance import Instance
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.core.resource_ids import generate_id, ResourceType
import docker


class CloudWatchService:
    """Service for CloudWatch metrics operations."""
    
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
        except Exception:
            # Docker not available, will skip container metrics
            self.docker_client = None
    
    # ==================== Metric Storage ====================
    
    def put_metric_data(
        self,
        db: Session,
        account_id: str,
        namespace: str,
        metric_name: str,
        value: float,
        unit: str,
        timestamp: Optional[datetime] = None,
        dimensions: Optional[Dict[str, str]] = None
    ) -> CloudWatchMetric:
        """
        Put a single metric data point.
        
        Args:
            db: Database session
            account_id: Account ID
            namespace: Metric namespace (e.g., "AWS/EC2")
            metric_name: Metric name (e.g., "CPUUtilization")
            value: Metric value
            unit: Unit (e.g., "Percent", "Bytes", "Count")
            timestamp: Metric timestamp (defaults to now)
            dimensions: Optional dimensions dict
        
        Returns:
            Created metric
        
        Raises:
            ValidationError: If parameters invalid
        """
        # Validate
        if not namespace or len(namespace) > 255:
            raise ValidationError("Namespace must be 1-255 characters")
        
        if not metric_name or len(metric_name) > 255:
            raise ValidationError("Metric name must be 1-255 characters")
        
        valid_units = ["Seconds", "Microseconds", "Milliseconds", "Bytes", "Kilobytes", 
                      "Megabytes", "Gigabytes", "Terabytes", "Bits", "Kilobits", 
                      "Megabits", "Gigabits", "Terabits", "Percent", "Count", 
                      "Bytes/Second", "Kilobytes/Second", "Megabytes/Second", 
                      "Gigabytes/Second", "Terabytes/Second", "Bits/Second", 
                      "Kilobits/Second", "Megabits/Second", "Gigabits/Second", 
                      "Terabits/Second", "Count/Second", "None"]
        
        if unit not in valid_units:
            raise ValidationError(f"Invalid unit: {unit}")
        
        # Create metric
        metric_id = generate_id(ResourceType.CLOUDWATCH_METRIC)
        
        metric = CloudWatchMetric(
            metric_id=metric_id,
            namespace=namespace,
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=timestamp or datetime.utcnow(),
            dimensions=json.dumps(dimensions) if dimensions else None,
            account_id=account_id,
            created_at=datetime.utcnow()
        )
        
        db.add(metric)
        db.commit()
        db.refresh(metric)
        
        return metric
    
    def put_metric_data_batch(
        self,
        db: Session,
        account_id: str,
        namespace: str,
        metric_data: List[Dict[str, Any]]
    ) -> List[CloudWatchMetric]:
        """
        Put multiple metric data points in batch.
        
        Args:
            db: Database session
            account_id: Account ID
            namespace: Metric namespace
            metric_data: List of metric dictionaries
        
        Returns:
            List of created metrics
        """
        metrics = []
        
        for data in metric_data:
            metric = self.put_metric_data(
                db,
                account_id,
                namespace,
                data["metric_name"],
                data["value"],
                data["unit"],
                data.get("timestamp"),
                data.get("dimensions")
            )
            metrics.append(metric)
        
        return metrics
    
    # ==================== Metric Retrieval ====================
    
    def get_metric_statistics(
        self,
        db: Session,
        account_id: str,
        namespace: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        period: int,
        statistics: List[str],
        dimensions: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get metric statistics over a time range.
        
        Args:
            db: Database session
            account_id: Account ID
            namespace: Metric namespace
            metric_name: Metric name
            start_time: Start of time range
            end_time: End of time range
            period: Period in seconds (60, 300, 3600, etc.)
            statistics: Statistics to compute (Average, Sum, Minimum, Maximum, SampleCount)
            dimensions: Optional dimension filters
        
        Returns:
            Statistics result with datapoints
        
        Raises:
            ValidationError: If parameters invalid
        """
        # Validate
        if start_time >= end_time:
            raise ValidationError("start_time must be before end_time")
        
        if period < 60:
            raise ValidationError("Period must be at least 60 seconds")
        
        valid_stats = ["Average", "Sum", "Minimum", "Maximum", "SampleCount"]
        for stat in statistics:
            if stat not in valid_stats:
                raise ValidationError(f"Invalid statistic: {stat}")
        
        # Build query
        query = db.query(CloudWatchMetric).filter(
            CloudWatchMetric.account_id == account_id,
            CloudWatchMetric.namespace == namespace,
            CloudWatchMetric.metric_name == metric_name,
            CloudWatchMetric.timestamp >= start_time,
            CloudWatchMetric.timestamp <= end_time
        )
        
        # Filter by dimensions
        if dimensions:
            dimensions_json = json.dumps(dimensions, sort_keys=True)
            query = query.filter(CloudWatchMetric.dimensions == dimensions_json)
        
        # Get metrics
        metrics = query.order_by(CloudWatchMetric.timestamp).all()
        
        if not metrics:
            return {
                "label": metric_name,
                "datapoints": []
            }
        
        # Aggregate by period
        datapoints = []
        current_period_start = start_time
        
        while current_period_start < end_time:
            current_period_end = current_period_start + timedelta(seconds=period)
            
            # Get metrics in this period
            period_metrics = [
                m for m in metrics 
                if current_period_start <= m.timestamp < current_period_end
            ]
            
            if period_metrics:
                values = [m.value for m in period_metrics]
                
                datapoint = {
                    "timestamp": current_period_start.isoformat(),
                    "unit": period_metrics[0].unit
                }
                
                if "Average" in statistics:
                    datapoint["average"] = sum(values) / len(values)
                
                if "Sum" in statistics:
                    datapoint["sum"] = sum(values)
                
                if "Minimum" in statistics:
                    datapoint["minimum"] = min(values)
                
                if "Maximum" in statistics:
                    datapoint["maximum"] = max(values)
                
                if "SampleCount" in statistics:
                    datapoint["sample_count"] = len(values)
                
                datapoints.append(datapoint)
            
            current_period_start = current_period_end
        
        return {
            "label": metric_name,
            "datapoints": datapoints
        }
    
    def list_metrics(
        self,
        db: Session,
        account_id: str,
        namespace: Optional[str] = None,
        metric_name: Optional[str] = None,
        dimensions: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List available metrics.
        
        Args:
            db: Database session
            account_id: Account ID
            namespace: Optional namespace filter
            metric_name: Optional metric name filter
            dimensions: Optional dimension filters
        
        Returns:
            List of unique metric definitions
        """
        query = db.query(
            CloudWatchMetric.namespace,
            CloudWatchMetric.metric_name,
            CloudWatchMetric.dimensions
        ).filter(
            CloudWatchMetric.account_id == account_id
        ).distinct()
        
        if namespace:
            query = query.filter(CloudWatchMetric.namespace == namespace)
        
        if metric_name:
            query = query.filter(CloudWatchMetric.metric_name == metric_name)
        
        if dimensions:
            dimensions_json = json.dumps(dimensions, sort_keys=True)
            query = query.filter(CloudWatchMetric.dimensions == dimensions_json)
        
        results = query.all()
        
        metrics = []
        for namespace, metric_name, dimensions_str in results:
            metrics.append({
                "namespace": namespace,
                "metric_name": metric_name,
                "dimensions": json.loads(dimensions_str) if dimensions_str else {}
            })
        
        return metrics
    
    # ==================== Docker Stats Collection ====================
    
    def collect_instance_metrics(
        self,
        db: Session,
        account_id: str,
        instance_id: str
    ) -> List[CloudWatchMetric]:
        """
        Collect metrics from a running EC2 instance (Docker container).
        
        Args:
            db: Database session
            account_id: Account ID
            instance_id: Instance ID
        
        Returns:
            List of collected metrics
        
        Raises:
            ResourceNotFoundError: If instance not found
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
        
        # Get Docker container
        try:
            container = self.docker_client.containers.get(instance.container_id)
        except docker.errors.NotFound:
            raise ResourceNotFoundError(f"Container {instance.container_id} not found")
        
        # Get container stats (single point, no streaming)
        stats = container.stats(stream=False)
        
        # Calculate metrics
        timestamp = datetime.utcnow()
        dimensions = {
            "InstanceId": instance_id,
            "InstanceType": instance.instance_type
        }
        
        metrics = []
        
        # CPU Utilization
        cpu_percent = self._calculate_cpu_percent(stats)
        metrics.append(self.put_metric_data(
            db,
            account_id,
            "AWS/EC2",
            "CPUUtilization",
            cpu_percent,
            "Percent",
            timestamp,
            dimensions
        ))
        
        # Memory Utilization
        memory_percent = self._calculate_memory_percent(stats)
        metrics.append(self.put_metric_data(
            db,
            account_id,
            "AWS/EC2",
            "MemoryUtilization",
            memory_percent,
            "Percent",
            timestamp,
            dimensions
        ))
        
        # Network In
        network_in = self._get_network_bytes_in(stats)
        metrics.append(self.put_metric_data(
            db,
            account_id,
            "AWS/EC2",
            "NetworkIn",
            network_in,
            "Bytes",
            timestamp,
            dimensions
        ))
        
        # Network Out
        network_out = self._get_network_bytes_out(stats)
        metrics.append(self.put_metric_data(
            db,
            account_id,
            "AWS/EC2",
            "NetworkOut",
            network_out,
            "Bytes",
            timestamp,
            dimensions
        ))
        
        # Disk Read Bytes
        disk_read = self._get_disk_read_bytes(stats)
        metrics.append(self.put_metric_data(
            db,
            account_id,
            "AWS/EC2",
            "DiskReadBytes",
            disk_read,
            "Bytes",
            timestamp,
            dimensions
        ))
        
        # Disk Write Bytes
        disk_write = self._get_disk_write_bytes(stats)
        metrics.append(self.put_metric_data(
            db,
            account_id,
            "AWS/EC2",
            "DiskWriteBytes",
            disk_write,
            "Bytes",
            timestamp,
            dimensions
        ))
        
        return metrics
    
    def collect_all_instance_metrics(
        self,
        db: Session
    ) -> Dict[str, List[CloudWatchMetric]]:
        """
        Collect metrics from all running instances across all accounts.
        
        Args:
            db: Database session
        
        Returns:
            Dictionary mapping instance_id to list of metrics
        """
        # Get all running instances
        instances = db.query(Instance).filter(
            Instance.state == "running"
        ).all()
        
        results = {}
        
        for instance in instances:
            try:
                metrics = self.collect_instance_metrics(
                    db,
                    instance.account_id,
                    instance.instance_id
                )
                results[instance.instance_id] = metrics
            except Exception as e:
                # Log error but continue with other instances
                print(f"Error collecting metrics for {instance.instance_id}: {str(e)}")
                continue
        
        return results
    
    # ==================== Helper Methods ====================
    
    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU utilization percentage from Docker stats."""
        try:
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                       stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                          stats["precpu_stats"]["system_cpu_usage"]
            
            if system_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * \
                             len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [1])) * 100.0
                return round(cpu_percent, 2)
        except (KeyError, ZeroDivisionError):
            pass
        
        return 0.0
    
    def _calculate_memory_percent(self, stats: Dict) -> float:
        """Calculate memory utilization percentage from Docker stats."""
        try:
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            
            if memory_limit > 0:
                memory_percent = (memory_usage / memory_limit) * 100.0
                return round(memory_percent, 2)
        except (KeyError, ZeroDivisionError):
            pass
        
        return 0.0
    
    def _get_network_bytes_in(self, stats: Dict) -> float:
        """Get network bytes received from Docker stats."""
        try:
            networks = stats.get("networks", {})
            total = sum(net.get("rx_bytes", 0) for net in networks.values())
            return float(total)
        except (KeyError, TypeError):
            return 0.0
    
    def _get_network_bytes_out(self, stats: Dict) -> float:
        """Get network bytes transmitted from Docker stats."""
        try:
            networks = stats.get("networks", {})
            total = sum(net.get("tx_bytes", 0) for net in networks.values())
            return float(total)
        except (KeyError, TypeError):
            return 0.0
    
    def _get_disk_read_bytes(self, stats: Dict) -> float:
        """Get disk bytes read from Docker stats."""
        try:
            blkio_stats = stats.get("blkio_stats", {})
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])
            
            total = sum(
                entry.get("value", 0) 
                for entry in io_service_bytes 
                if entry.get("op") == "Read"
            )
            return float(total)
        except (KeyError, TypeError):
            return 0.0
    
    def _get_disk_write_bytes(self, stats: Dict) -> float:
        """Get disk bytes written from Docker stats."""
        try:
            blkio_stats = stats.get("blkio_stats", {})
            io_service_bytes = blkio_stats.get("io_service_bytes_recursive", [])
            
            total = sum(
                entry.get("value", 0) 
                for entry in io_service_bytes 
                if entry.get("op") == "Write"
            )
            return float(total)
        except (KeyError, TypeError):
            return 0.0


