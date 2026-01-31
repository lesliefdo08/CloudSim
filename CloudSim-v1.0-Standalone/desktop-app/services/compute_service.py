"""
Compute Service - HTTP client for CloudSim backend (metadata only)
"""

import requests
from typing import List, Optional
from models.instance import Instance
from core.region import get_current_region, RegionRegistry
from core.iam import IAMManager, Action
from core.events import EventType, emit_event

# Backend API URL
BACKEND_URL = "http://127.0.0.1:8000/api"


class ComputeService:
    """Service for managing compute instances (metadata only)"""
    
    def __init__(self):
        """Initialize compute service with backend communication"""
        self.region_registry = RegionRegistry()
        self.iam_manager = IAMManager()
        self.backend_available = self._check_backend()
    
    def _check_backend(self) -> bool:
        """Check if backend is available"""
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _check_permission(self, action: str, resource_id: Optional[str] = None):
        """Check IAM permission for action"""
        resource_arn = None
        if resource_id:
            instance = self.get_instance(resource_id)
            if instance:
                resource_arn = instance.arn()
        
        if not self.iam_manager.check_permission(action, resource_arn):
            raise PermissionError(f"User does not have permission for action: {action}")
    
    def create_instance(self, name: str, cpu: int = 1, memory: int = 512, 
                       image: str = "ubuntu:22.04", region: Optional[str] = None,
                       tags: Optional[dict] = None) -> Instance:
        """Create new EC2 instance (metadata only, STOPPED state)"""
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
        
        if not self.backend_available:
            raise RuntimeError("Backend not available. Please start the backend server.")
        
        # Call backend API
        try:
            response = requests.post(
                f"{BACKEND_URL}/instances",
                json={
                    "name": name,
                    "cpu": cpu,
                    "memory": memory,
                    "image": image
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert to Instance model
            instance = Instance(
                id=data["id"],
                name=data["name"],
                status=data["state"].lower(),
                cpu=data["cpu"],
                memory=data["memory"],
                created_at=data["created_at"],
                region=region,
                image=data["image"],
                owner="local-user",
                tags=tags or {},
                state=data["state"].lower()
            )
            
            # Emit event
            emit_event(
                EventType.INSTANCE_CREATED,
                "compute",
                region,
                instance.id,
                instance.arn(),
                {"name": name, "cpu": cpu, "memory": memory}
            )
            
            return instance
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to create instance: {str(e)}")
    
    def get_instance(self, instance_id: str) -> Optional[Instance]:
        """Get instance by ID from backend"""
        if not self.backend_available:
            return None
        
        try:
            response = requests.get(f"{BACKEND_URL}/instances/{instance_id}", timeout=5)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            
            return Instance(
                id=data["id"],
                name=data["name"],
                status=data["state"].lower(),
                cpu=data["cpu"],
                memory=data["memory"],
                created_at=data["created_at"],
                image=data["image"],
                container_id=data.get("container_id")
            )
        except:
            return None
    
    def list_instances(self, region: Optional[str] = None) -> List[Instance]:
        """Get all instances from backend"""
        # Check IAM permission
        self._check_permission(Action.COMPUTE_LIST.value)
        
        if not self.backend_available:
            return []
        
        response = requests.get(f"{BACKEND_URL}/instances", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("Fetched instances:", data)
        
        instances = []
        for item in data:
            instances.append(Instance(
                id=item["id"],
                name=item["name"],
                status=item["state"].lower(),
                cpu=item["cpu"],
                memory=item["memory"],
                created_at=item["created_at"],
                image=item["image"],
                region=region or get_current_region(),
                container_id=item.get("container_id")
            ))
        return instances
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate instance (removes metadata)"""
        # Check IAM permission
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        if not self.backend_available:
            raise RuntimeError("Backend not available")
        
        # Get instance before deletion
        instance = self.get_instance(instance_id)
        
        try:
            response = requests.delete(f"{BACKEND_URL}/instances/{instance_id}", timeout=10)
            response.raise_for_status()
            
            if instance:
                # Emit event
                emit_event(
                    EventType.INSTANCE_TERMINATED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "terminate"}
                )
            return True
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to terminate instance: {str(e)}")
    
    def start_instance(self, instance_id: str) -> bool:
        """Start instance via backend API"""
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        if not self.backend_available:
            raise RuntimeError("Backend not available")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/instances/{instance_id}/start",
                timeout=30
            )
            response.raise_for_status()
            
            # Emit event
            instance = self.get_instance(instance_id)
            if instance:
                emit_event(
                    EventType.INSTANCE_STARTED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "start"}
                )
            return True
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to start instance: {str(e)}")
    
    def stop_instance(self, instance_id: str) -> bool:
        """Stop instance via backend API"""
        self._check_permission(Action.COMPUTE_STOP.value, instance_id)
        
        if not self.backend_available:
            raise RuntimeError("Backend not available")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/instances/{instance_id}/stop",
                timeout=30
            )
            response.raise_for_status()
            
            # Emit event
            instance = self.get_instance(instance_id)
            if instance:
                emit_event(
                    EventType.INSTANCE_STOPPED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "stop"}
                )
            return True
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to stop instance: {str(e)}")
    
    def reboot_instance(self, instance_id: str) -> bool:
        """Reboot instance via backend API"""
        self._check_permission(Action.COMPUTE_START.value, instance_id)
        
        if not self.backend_available:
            raise RuntimeError("Backend not available")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/instances/{instance_id}/reboot",
                timeout=30
            )
            response.raise_for_status()
            
            # Emit event
            instance = self.get_instance(instance_id)
            if instance:
                emit_event(
                    EventType.INSTANCE_STARTED,
                    "compute",
                    instance.region,
                    instance.id,
                    instance.arn(),
                    {"action": "reboot"}
                )
            return True
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to reboot instance: {str(e)}")
    
    def execute_command(self, instance_id: str, command: str) -> dict:
        """Execute command in instance via backend API"""
        if not self.backend_available:
            return {
                "output": "Backend not available",
                "exit_code": 1,
                "error": "Backend service not running"
            }
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/instances/{instance_id}/exec",
                json={"command": command},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "output": "",
                "exit_code": 1,
                "error": f"Failed to execute command: {str(e)}"
            }
    
    def get_stats(self) -> dict:
        """Get compute statistics"""
        instances = self.list_instances()
        return {
            "total": len(instances),
            "running": len([i for i in instances if i.status == "running"]),
            "stopped": len([i for i in instances if i.status == "stopped"])
        }

