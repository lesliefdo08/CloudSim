"""
Instance Model - Represents a compute instance (EC2-like)
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, List
import uuid


@dataclass
class Volume:
    """Storage volume attached to instance"""
    id: str
    name: str
    size_gb: int
    volume_type: str = "gp3"  # gp3, io2, st1, sc1
    attached_at: Optional[str] = None
    device: Optional[str] = None  # /dev/sda1, /dev/sdb, etc.
    
    @staticmethod
    def create_new(name: str, size_gb: int, volume_type: str = "gp3") -> 'Volume':
        """Create a new volume"""
        volume_id = f"vol-{uuid.uuid4().hex[:8]}"
        return Volume(
            id=volume_id,
            name=name,
            size_gb=size_gb,
            volume_type=volume_type
        )
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Volume':
        return Volume(**data)


@dataclass
class StateTransition:
    """Record of instance state change"""
    timestamp: str
    from_state: str
    to_state: str
    user: Optional[str] = None
    reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'StateTransition':
        return StateTransition(**data)


@dataclass
class Instance:
    """Simulated compute instance with AWS-style attributes"""
    
    id: str
    name: str
    status: str  # "running", "stopped", "pending", "rebooting", "terminated"
    cpu: int  # Number of virtual CPUs
    memory: int  # Memory in MB
    created_at: str
    region: str = "us-east-1"  # AWS-style region
    image: str = "ubuntu:latest"  # Docker image (ubuntu:22.04, amazonlinux:2, debian:latest)
    owner: Optional[str] = None  # IAM user who created the instance
    tags: Dict[str, str] = field(default_factory=dict)  # AWS-style tags
    state: str = "stopped"  # More detailed state (for backward compatibility with status)
    volumes: List[Dict] = field(default_factory=list)  # Attached volumes
    state_transitions: List[Dict] = field(default_factory=list)  # State change history
    billing_hours: float = 0.0  # Simulated hourly billing counter
    last_start_time: Optional[str] = None  # When instance was last started
    instance_type: str = "t3.micro"  # AWS instance type simulation
    container_id: Optional[str] = None  # Docker container ID for real container backing
    
    @staticmethod
    def create_new(name: str, cpu: int = 1, memory: int = 512, image: str = "ubuntu:latest",
                   region: str = "us-east-1", owner: Optional[str] = None,
                   tags: Optional[Dict[str, str]] = None) -> 'Instance':
        """Create a new instance with generated ID and AWS-style attributes"""
        instance_id = f"i-{uuid.uuid4().hex[:8]}"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine instance type based on CPU/memory
        instance_type = "t3.micro"
        if cpu >= 4 or memory >= 4096:
            instance_type = "t3.large"
        elif cpu >= 2 or memory >= 2048:
            instance_type = "t3.medium"
        
        # Create root volume
        root_volume = Volume.create_new(f"{name}-root", 8, "gp3")
        root_volume.device = "/dev/sda1"
        root_volume.attached_at = created_at
        
        return Instance(
            id=instance_id,
            name=name,
            status="stopped",
            state="stopped",
            cpu=cpu,
            memory=memory,
            created_at=created_at,
            image=image,
            region=region,
            owner=owner,
            tags=tags or {},
            volumes=[root_volume.to_dict()],
            state_transitions=[],
            billing_hours=0.0,
            instance_type=instance_type
        )
    
    def to_dict(self) -> dict:
        """Convert instance to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: dict) -> 'Instance':
        """Create instance from dictionary"""
        # Handle backward compatibility
        if 'region' not in data:
            data['region'] = 'us-east-1'
        if 'state' not in data:
            data['state'] = data.get('status', 'stopped')
        if 'tags' not in data:
            data['tags'] = {}
        if 'volumes' not in data:
            # Create default root volume for old instances
            root_vol = Volume.create_new(f"{data.get('name', 'instance')}-root", 8, "gp3")
            root_vol.device = "/dev/sda1"
            root_vol.attached_at = data.get('created_at')
            data['volumes'] = [root_vol.to_dict()]
        if 'state_transitions' not in data:
            data['state_transitions'] = []
        if 'billing_hours' not in data:
            data['billing_hours'] = 0.0
        if 'last_start_time' not in data:
            data['last_start_time'] = None
        if 'instance_type' not in data:
            cpu = data.get('cpu', 1)
            memory = data.get('memory', 512)
            if cpu >= 4 or memory >= 4096:
                data['instance_type'] = 't3.large'
            elif cpu >= 2 or memory >= 2048:
                data['instance_type'] = 't3.medium'
            else:
                data['instance_type'] = 't3.micro'
        if 'container_id' not in data:
            data['container_id'] = None  # Backward compatibility for Docker integration
        return Instance(**data)
    
    def arn(self) -> str:
        """Generate AWS-style ARN for the instance"""
        return f"arn:cloudsim:compute:{self.region}:instance/{self.id}"
    
    def _add_state_transition(self, from_state: str, to_state: str, user: Optional[str] = None, reason: Optional[str] = None):
        """Record state transition"""
        transition = StateTransition(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            from_state=from_state,
            to_state=to_state,
            user=user,
            reason=reason
        )
        self.state_transitions.append(transition.to_dict())
    
    def start(self, user: Optional[str] = None):
        """Start the instance"""
        if self.status in ["stopped", "terminated"]:
            old_state = self.status
            self.status = "running"
            self.state = "running"
            self.last_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._add_state_transition(old_state, "running", user, "User initiated start")
            return True
        return False
    
    def stop(self, user: Optional[str] = None):
        """Stop the instance"""
        if self.status == "running":
            old_state = self.status
            self.status = "stopped"
            self.state = "stopped"
            self._add_state_transition(old_state, "stopped", user, "User initiated stop")
            return True
        return False
    
    def reboot(self, user: Optional[str] = None):
        """Reboot the instance"""
        if self.status == "running":
            old_state = self.status
            self.status = "rebooting"
            self.state = "rebooting"
            self._add_state_transition(old_state, "rebooting", user, "User initiated reboot")
            # Simulate reboot by immediately going back to running
            self.status = "running"
            self.state = "running"
            self._add_state_transition("rebooting", "running", None, "Reboot completed")
            return True
        return False
    
    def terminate(self, user: Optional[str] = None):
        """Terminate the instance"""
        if self.status != "terminated":
            old_state = self.status
            self.status = "terminated"
            self.state = "terminated"
            self._add_state_transition(old_state, "terminated", user, "User initiated termination")
            return True
        return False
    
    def attach_volume(self, volume: Volume, device: str) -> bool:
        """Attach a storage volume"""
        # Check if device already in use
        for vol in self.volumes:
            if vol.get('device') == device:
                return False
        
        volume.device = device
        volume.attached_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.volumes.append(volume.to_dict())
        return True
    
    def detach_volume(self, volume_id: str) -> bool:
        """Detach a storage volume (except root volume)"""
        # Don't allow detaching root volume
        for vol in self.volumes:
            if vol['id'] == volume_id and vol.get('device') != '/dev/sda1':
                self.volumes = [v for v in self.volumes if v['id'] != volume_id]
                return True
        return False
    
    def get_volumes(self) -> List[Volume]:
        """Get all attached volumes"""
        return [Volume.from_dict(vol) for vol in self.volumes]
    
    def update_billing(self, hours: float):
        """Update billing hours counter"""
        self.billing_hours += hours
    
    def get_billing_cost(self) -> float:
        """Calculate estimated cost based on instance type and hours"""
        # Simulated hourly rates
        rates = {
            't3.micro': 0.0104,
            't3.small': 0.0208,
            't3.medium': 0.0416,
            't3.large': 0.0832,
            't3.xlarge': 0.1664
        }
        rate = rates.get(self.instance_type, 0.0104)
        return round(self.billing_hours * rate, 2)
