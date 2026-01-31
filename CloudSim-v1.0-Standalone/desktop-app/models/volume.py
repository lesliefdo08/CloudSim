"""
Volume model for EBS-like storage
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import random
import string


@dataclass
class Snapshot:
    """Snapshot of a volume at a point in time"""
    id: str
    volume_id: str
    name: str
    description: Optional[str]
    size_gb: int
    volume_type: str
    created_at: str
    status: str  # creating, available, deleting
    owner: Optional[str] = None
    region: str = "us-east-1"
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Snapshot':
        """Create from dictionary"""
        return Snapshot(**data)
    
    @staticmethod
    def generate_id() -> str:
        """Generate snapshot ID in AWS format"""
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"snap-{suffix}"


@dataclass
class Volume:
    """EBS-like storage volume"""
    id: str
    name: str
    size_gb: int
    volume_type: str  # gp3, gp2, io2, st1, sc1, standard
    state: str  # available, in-use, creating, deleting
    created_at: str
    region: str
    availability_zone: str
    owner: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)
    
    # Attachment info
    attached_instance_id: Optional[str] = None
    attached_device: Optional[str] = None
    attached_at: Optional[str] = None
    
    # Volume characteristics
    iops: Optional[int] = None  # For io2 volumes
    throughput: Optional[int] = None  # For gp3 volumes
    encrypted: bool = False
    snapshot_id: Optional[str] = None  # If created from snapshot
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Volume':
        """Create from dictionary"""
        return Volume(**data)
    
    @staticmethod
    def generate_id() -> str:
        """Generate volume ID in AWS format"""
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"vol-{suffix}"
    
    @staticmethod
    def create_new(
        name: str,
        size_gb: int,
        volume_type: str = "gp3",
        region: str = "us-east-1",
        availability_zone: str = "us-east-1a",
        owner: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        encrypted: bool = False,
        snapshot_id: Optional[str] = None
    ) -> 'Volume':
        """Create a new volume"""
        volume_id = Volume.generate_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Set default IOPS and throughput based on volume type
        iops = None
        throughput = None
        if volume_type == "gp3":
            iops = 3000  # Base IOPS for gp3
            throughput = 125  # MB/s
        elif volume_type == "io2":
            iops = min(size_gb * 500, 64000)  # 500 IOPS per GB, max 64000
        
        return Volume(
            id=volume_id,
            name=name,
            size_gb=size_gb,
            volume_type=volume_type,
            state="available",
            created_at=now,
            region=region,
            availability_zone=availability_zone,
            owner=owner,
            tags=tags or {},
            iops=iops,
            throughput=throughput,
            encrypted=encrypted,
            snapshot_id=snapshot_id
        )
    
    def attach(self, instance_id: str, device: str) -> None:
        """Attach volume to an instance"""
        if self.state != "available":
            raise ValueError(f"Cannot attach volume in state: {self.state}")
        
        self.state = "in-use"
        self.attached_instance_id = instance_id
        self.attached_device = device
        self.attached_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def detach(self) -> None:
        """Detach volume from instance"""
        if self.state != "in-use":
            raise ValueError(f"Cannot detach volume in state: {self.state}")
        
        self.state = "available"
        self.attached_instance_id = None
        self.attached_device = None
        self.attached_at = None
    
    def is_attached(self) -> bool:
        """Check if volume is attached"""
        return self.state == "in-use" and self.attached_instance_id is not None
    
    def get_arn(self) -> str:
        """Get ARN for IAM"""
        return f"arn:cloudsim:storage:{self.region}:volume/{self.id}"
    
    def create_snapshot(
        self,
        snapshot_name: str,
        description: Optional[str] = None,
        owner: Optional[str] = None
    ) -> Snapshot:
        """Create a snapshot of this volume"""
        snapshot_id = Snapshot.generate_id()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return Snapshot(
            id=snapshot_id,
            volume_id=self.id,
            name=snapshot_name,
            description=description,
            size_gb=self.size_gb,
            volume_type=self.volume_type,
            created_at=now,
            status="available",  # Instant snapshot for simulation
            owner=owner,
            region=self.region,
            tags={}
        )
    
    def get_status_display(self) -> str:
        """Get human-readable status"""
        status_map = {
            "available": "Available",
            "in-use": "In Use",
            "creating": "Creating",
            "deleting": "Deleting"
        }
        return status_map.get(self.state, self.state.title())
    
    def get_attachment_info(self) -> str:
        """Get attachment information for display"""
        if self.is_attached():
            return f"{self.attached_instance_id} ({self.attached_device})"
        return "Not attached"
