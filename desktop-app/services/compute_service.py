"""
Compute Service - Manages compute instances (EC2-like) with Docker container backing
"""

from typing import List, Optional
from models.instance import Instance
from utils.storage import Storage
from core.region import get_current_region, RegionRegistry
from core.iam import IAMManager, Action
from core.events import EventBus, EventType, emit_event
from core.metering import UsageMeter, record_compute_usage
from services.billing_service import billing_service
from services.docker_compute_service import docker_service


class ComputeService:
    """Service for managing compute instances with region and IAM support
    
    *** SHARED LOCAL STORAGE ***
    Uses: data/instances.json (single namespace, not per-user)
    """
    
    def __init__(self):
        """Initialize compute service with AWS-style architecture"""
        # Shared storage: data/instances.json
        self.storage = Storage("instances.json")
        self._instances = {}
        self._load_instances()
        
        # Get singletons
        self.region_registry = RegionRegistry()
        self.iam_manager = IAMManager()
        self.event_bus = EventBus()
        self.usage_meter = UsageMeter()
        
        # Docker service for container backing
        self.docker_service = docker_service
        
        # Reconnect to existing containers after app restart
        self._reconnect_containers()
    
    def _load_instances(self):
        """Load instances from storage"""
        data = self.storage.load()
        for instance_data in data:
            instance = Instance.from_dict(instance_data)
            self._instances[instance.id] = instance
    
    def _reconnect_containers(self):
        """Reconnect to existing Docker containers after app restart"""
        if not self.docker_service.is_available():
            return
        
        for instance in self._instances.values():
            if instance.container_id:
                # Verify container still exists
                if self.docker_service.reconnect_to_container(instance.container_id):
                    # Update instance status based on container status
                    container_status = self.docker_service.get_container_status(instance.container_id)
                    if container_status == "running" and instance.status != "running":
                        instance.status = "running"
                        instance.state = "running"
                    elif container_status == "exited" and instance.status == "running":
                        instance.status = "stopped"
                        instance.state = "stopped"
                else:
                    # Container no longer exists, clear container_id
                    instance.container_id = None
                    if instance.status == "running":
                        instance.status = "stopped"
                        instance.state = "stopped"
        
        # Save any status changes
        self._save_instances()
    
    def _save_instances(self):
        """Save instances to storage"""
        data = [instance.to_dict() for instance in self._instances.values()]
        self.storage.save(data)
    
    def _check_permission(self, action: str, resource_id: Optional[str] = None):
        """Check IAM permission for action"""
        resource_arn = f"arn:cloudsim:compute:*:instance/*"
        if resource_id:
            instance = self._instances.get(resource_id)
            if instance:
                resource_arn = instance.arn()
        
        if not self.iam_manager.check_permission(action, resource_arn):
            raise PermissionError(f"User does not have permission for action: {action}")
    
    def create_instance(self, name: str, cpu: int = 1, memory: int = 512, 
                       image: str = "ubuntu:22.04", region: Optional[str] = None,
                       tags: Optional[dict] = None) -> Instance:
        """
        Create a new compute instance with Docker container backing
        
        Args:
            name: Instance name
            cpu: Number of virtual CPUs
            memory: Memory in MB
            image: Docker image (ubuntu:22.04, amazonlinux:2, debian:latest)
            region: AWS region (defaults to current region)
            tags: AWS-style tags
            
        Returns:
            Created instance
        """
        # Check IAM permission
        self._check_permission(Action.COMPUTE_CREATE.value)
        
        # Use current region if not specified
        if region is None:
            region = get_current_region()
        
        # Validate region
        if not self.region_registry.is_valid_region(region):
            raise ValueError(f"Invalid region: {region}")
        # Validate inputs
        if not name or not name.strip():
            raise ValueError("Instance name cannot be empty")
        
        if cpu < 1 or cpu > 8:
            raise ValueError("CPU must be between 1 and 8")
        
        if memory < 256 or memory > 8192:
            raise ValueError("Memory must be between 256 MB and 8192 MB")
        
        # Use local user (auth disabled)
        owner = "local-user"
        
        # Simulate realistic API delay for instance creation (1.5-2s)
        import time
        import random
        time.sleep(random.uniform(1.5, 2.0))
        
        # Create instance with region and owner
        instance = Instance.create_new(name, cpu, memory, image, region, owner, tags)
        
        # Create Docker container if Docker is available
        if self.docker_service.is_available():
            container_id = self.docker_service.create_container(instance.id, name, image)
            if container_id:
                instance.container_id = container_id
        
        self._instances[instance.id] = instance
        self._save_instances()
        
        # Estimate instance type and cost
        instance_type = self._estimate_instance_type(cpu, memory)
        cost, explanation = billing_service.calculate_resource_cost(
            "ec2_instance",
            instance_type=instance_type,
            hours_running=0.0  # Just created
        )
        
        # Log activity with cost
        billing_service.log_activity(
            user="local-user",
            service="EC2",
            action="CreateInstance",
            resource_type="ec2_instance",
            resource_id=instance.id,
            resource_name=name,
            region=region,
            status="success",
            details={
                "instanceType": instance_type,
                "cpu": cpu,
                "memory": memory,
                "image": image,
                "pricePerHour": f"${cost:.4f}"
            },
            cost_impact=0.0  # No cost until running
        )
        
        # Emit event (user context added automatically)
        emit_event(
            EventType.INSTANCE_CREATED,
            "compute",
            region,
            instance.id,
            instance.arn(),
            {"name": name, "cpu": cpu, "memory": memory}
        )
        
        return instance
    
    def get_instance(self, instance_id: str) -> Optional[Instance]:
        """
        Get instance by ID
        
        Args:
            instance_id: Instance ID
            
        Returns:
            Instance or None if not found
        """
        return self._instances.get(instance_id)
    
    def list_instances(self, region: Optional[str] = None) -> List[Instance]:
        """
        Get all instances, optionally filtered by region
        
        Args:
            region: Filter by region (None = current region)
            
        Returns:
            List of instances in the specified region
        """
        # Check IAM permission
        self._check_permission(Action.COMPUTE_LIST.value)
        
        # Use current region if not specified
        if region is None:
            region = get_current_region()
        
        # Filter by region
        return [inst for inst in self._instances.values() if inst.region == region]
    
    def start_instance(self, instance_id: str) -> bool:
        """
        Start an instance and its Docker container
        
        Args:
            instance_id: Instance ID
            
        Returns:
            True if started successfully, False otherwise
        """
        # Simulate realistic API delay (1-2s)
        import time
        import random
        time.sleep(random.uniform(1.0, 2.0))
        
        # Check IAM permission
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            username = "local-user"
            
            # Start Docker container if available
            if instance.container_id and self.docker_service.is_available():
                if not self.docker_service.start_container(instance.container_id):
                    return False
            
            if instance.start(username):
                self._save_instances()
                
                # Start usage tracking
                self.usage_meter.start_tracking(instance_id)
                
                # Track resource start for billing
                billing_service.track_resource_start(instance_id)
                
                # Log activity
                billing_service.log_activity(
                    user="local-user",
                    service="EC2",
                    action="StartInstance",
                    resource_type="ec2_instance",
                    resource_id=instance.id,
                    resource_name=instance.name,
                    region=instance.region,
                    status="success",
                    details={"previousState": "stopped", "newState": "running"},
                    cost_impact=0.0
                )
                
                # Emit event
                emit_event(
                    EventType.INSTANCE_STARTED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"previous_state": "stopped", "new_state": "running"}
                )
                
                return True
        return False
    
    def stop_instance(self, instance_id: str) -> bool:
        """
        Stop an instance and its Docker container
        
        Args:
            instance_id: Instance ID
            
        Returns:
            True if stopped successfully, False otherwise
        """
        # Simulate realistic API delay (1-2s)
        import time
        import random
        time.sleep(random.uniform(1.0, 1.5))
        
        # Check IAM permission
        self._check_permission(Action.COMPUTE_STOP.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            username = "local-user"
            
            # Stop Docker container if available
            if instance.container_id and self.docker_service.is_available():
                self.docker_service.stop_container(instance.container_id)
            
            if instance.stop(username):
                # Record usage and update billing
                hours = self.usage_meter.stop_tracking(instance_id)
                if hours:
                    instance.update_billing(hours)
                    record_compute_usage(instance.id, instance.region, instance.cpu, hours)
                
                self._save_instances()
                
                # Track resource stop for billing
                billing_service.track_resource_stop(instance_id)
                
                # Calculate cost for this run
                instance_type = self._estimate_instance_type(instance.cpu, instance.memory)
                cost, explanation = billing_service.calculate_resource_cost(
                    "ec2_instance",
                    instance_type=instance_type,
                    hours_running=hours or 0.0
                )
                
                # Log activity
                billing_service.log_activity(
                    user="local-user",
                    service="EC2",
                    action="StopInstance",
                    resource_type="ec2_instance",
                    resource_id=instance.id,
                    resource_name=instance.name,
                    region=instance.region,
                    status="success",
                    details={
                        "previousState": "running",
                        "newState": "stopped",
                        "hoursRun": f"{hours:.2f}" if hours else "0",
                        "costExplanation": explanation
                    },
                    cost_impact=cost
                )
                
                # Emit event
                emit_event(
                    EventType.INSTANCE_STOPPED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"previous_state": "running", "new_state": "stopped", "hours_run": hours, "billing_cost": instance.get_billing_cost()}
                )
                
                return True
        return False
    
    def terminate_instance(self, instance_id: str) -> bool:
        """
        Terminate an instance and remove its Docker container
        
        Args:
            instance_id: Instance ID
            
        Returns:
            True if terminated successfully
        """
        # Check IAM permission
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            username = "local-user"
            
            # Remove Docker container if available
            if instance.container_id and self.docker_service.is_available():
                self.docker_service.remove_container(instance.container_id)
            
            # Track resource stop for billing
            billing_service.track_resource_stop(instance_id)
            
            # Calculate final cost
            instance_type = self._estimate_instance_type(instance.cpu, instance.memory)
            hours = self.usage_meter.get_tracked_hours(instance_id) or 0.0
            cost, explanation = billing_service.calculate_resource_cost(
                "ec2_instance",
                instance_type=instance_type,
                hours_running=hours
            )
            
            # Terminate instance
            if instance.terminate(username):
                self._save_instances()
                
                # Log activity
                billing_service.log_activity(
                    user="local-user",
                    service="EC2",
                    action="TerminateInstance",
                    resource_type="ec2_instance",
                    resource_id=instance.id,
                    resource_name=instance.name,
                    region=instance.region,
                    status="success",
                    details={
                        "previousState": instance.status,
                        "finalCost": f"${cost:.4f}",
                        "totalHours": f"{hours:.2f}" if hours else "0"
                    },
                    cost_impact=cost
                )
                
                # Emit event
                emit_event(
                    EventType.INSTANCE_TERMINATED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "terminate", "final_billing": instance.get_billing_cost()}
                )
                
                return True
        return False
    
    def reboot_instance(self, instance_id: str) -> bool:
        """Reboot an instance"""
        # Check IAM permission
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            username = "local-user"
            
            if instance.reboot(username):
                self._save_instances()
                
                # Log activity
                billing_service.log_activity(
                    user="local-user",
                    service="EC2",
                    action="RebootInstance",
                    resource_type="ec2_instance",
                    resource_id=instance.id,
                    resource_name=instance.name,
                    region=instance.region,
                    status="success",
                    details={"action": "reboot", "state": "running"},
                    cost_impact=0.0
                )
                
                # Emit event
                emit_event(
                    EventType.INSTANCE_STARTED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "reboot", "state": "running"}
                )
                
                return True
        return False
    
    def attach_volume(self, instance_id: str, volume_name: str, size_gb: int, device: str, volume_type: str = "gp3") -> bool:
        """Attach a new volume to an instance"""
        from models.instance import Volume
        
        # Check IAM permission
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            volume = Volume.create_new(volume_name, size_gb, volume_type)
            
            if instance.attach_volume(volume, device):
                self._save_instances()
                
                # Emit event
                emit_event(
                    EventType.INSTANCE_STARTED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "attach_volume", "volume_id": volume.id, "device": device, "size_gb": size_gb}
                )
                
                return True
        return False
    
    def detach_volume(self, instance_id: str, volume_id: str) -> bool:
        """Detach a volume from an instance"""
        # Check IAM permission
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            if instance.detach_volume(volume_id):
                self._save_instances()
                
                # Emit event
                emit_event(
                    EventType.INSTANCE_STOPPED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "detach_volume", "volume_id": volume_id}
                )
                
                return True
        return False
    
    def update_instance_tags(self, instance_id: str, tags: dict) -> bool:
        """Update instance tags"""
        # Check IAM permission
        self._check_permission(Action.COMPUTE_LIST.value, instance_id)
        
        instance = self.get_instance(instance_id)
        if instance:
            instance.tags = tags
            self._save_instances()
            
            # Emit event
            emit_event(
                EventType.INSTANCE_STARTED,
                "compute",
                instance.region,
                instance.id,
                instance.arn(),
                {"action": "update_tags", "tag_count": len(tags)}
            )
            
            return True
        return False
    
    def delete_instance(self, instance_id: str) -> bool:
        """Delete an instance permanently (backward compatibility - use terminate_instance instead)"""
        return self.terminate_instance(instance_id)
    
    def get_stats(self) -> dict:
        """
        Get compute statistics
        
        Returns:
            Dictionary with statistics
        """
        instances = self.list_instances()
        running = sum(1 for i in instances if i.status == "running")
        stopped = sum(1 for i in instances if i.status == "stopped")
        total_cpu = sum(i.cpu for i in instances if i.status == "running")
        total_memory = sum(i.memory for i in instances if i.status == "running")
        
        return {
            "total": len(instances),
            "running": running,
            "stopped": stopped,
            "total_cpu": total_cpu,
            "total_memory_mb": total_memory
        }
    
    def _estimate_instance_type(self, cpu: int, memory: int) -> str:
        """Estimate AWS instance type based on CPU and memory"""
        # Simple mapping based on specs
        if cpu == 1 and memory <= 1024:
            return "t2.micro"
        elif cpu == 1 and memory <= 2048:
            return "t2.small"
        elif cpu == 2 and memory <= 4096:
            return "t2.medium"
        elif cpu == 2 and memory <= 8192:
            return "t3.medium"
        elif cpu == 4:
            return "m5.large"
        elif cpu >= 8:
            return "m5.xlarge"
        else:
            return "t3.small"

