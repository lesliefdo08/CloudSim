"""
Volume (EBS-like) service for storage management
"""
from typing import List, Optional, Dict, Any
from models.volume import Volume, Snapshot
from core.iam import IAMManager
from core.events import emit_event, EventType
from utils.storage import Storage


class VolumeService:
    """Manages EBS-like storage volumes
    
    *** SHARED LOCAL STORAGE ***
    Uses: data/volumes.json (single namespace, not per-user)
    """
    
    def __init__(self):
        self.iam_manager = IAMManager()
        # Shared storage: data/volumes.json
        self.storage = Storage("volumes.json")
        self._volumes: Dict[str, Volume] = {}
        self._snapshots: Dict[str, Snapshot] = {}
        self._load_data()
    
    def _load_data(self) -> None:
        """Load volumes and snapshots from storage"""
        data = self.storage.load()
        if data:
            for item in data:
                if item.get("type") == "volume":
                    vol = Volume.from_dict(item)
                    self._volumes[vol.id] = vol
                elif item.get("type") == "snapshot":
                    snap = Snapshot.from_dict(item)
                    self._snapshots[snap.id] = snap
    
    def _save_data(self) -> None:
        """Save volumes and snapshots to storage"""
        data = []
        for vol in self._volumes.values():
            vol_dict = vol.to_dict()
            vol_dict["type"] = "volume"
            data.append(vol_dict)
        for snap in self._snapshots.values():
            snap_dict = snap.to_dict()
            snap_dict["type"] = "snapshot"
            data.append(snap_dict)
        self.storage.save(data)
    
    def create_volume(
        self,
        name: str,
        size_gb: int,
        volume_type: str = "gp3",
        region: str = "us-east-1",
        availability_zone: str = "us-east-1a",
        user: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        encrypted: bool = False,
        snapshot_id: Optional[str] = None
    ) -> Volume:
        """Create a new volume"""
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:create", "*"):
            raise PermissionError(f"User does not have permission to create volumes")
        
        # Validate snapshot if provided
        if snapshot_id and snapshot_id not in self._snapshots:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Create volume
        volume = Volume.create_new(
            name=name,
            size_gb=size_gb,
            volume_type=volume_type,
            region=region,
            availability_zone=availability_zone,
            owner=user,
            tags=tags,
            encrypted=encrypted,
            snapshot_id=snapshot_id
        )
        
        self._volumes[volume.id] = volume
        self._save_data()
        
        # Emit event
        emit_event(
            EventType.VOLUME_CREATED,
            "storage",
            region,
            volume.id,
            volume.get_arn(),
            {
                "name": name,
                "size_gb": size_gb,
                "volume_type": volume_type,
                "encrypted": encrypted,
                "snapshot_id": snapshot_id
            }
        )
        
        return volume
    
    def list_volumes(
        self,
        user: Optional[str] = None,
        region: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Volume]:
        """List all volumes"""
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:list", "*"):
            raise PermissionError(f"User does not have permission to list volumes")
        
        volumes = list(self._volumes.values())
        
        # Filter by region
        if region:
            volumes = [v for v in volumes if v.region == region]
        
        # Filter by state
        if state:
            volumes = [v for v in volumes if v.state == state]
        
        return volumes
    
    def get_volume(self, volume_id: str) -> Optional[Volume]:
        """Get volume by ID"""
        return self._volumes.get(volume_id)
    
    def attach_volume(
        self,
        volume_id: str,
        instance_id: str,
        device: str,
        user: Optional[str] = None
    ) -> Volume:
        """Attach volume to an instance"""
        volume = self.get_volume(volume_id)
        if not volume:
            raise ValueError(f"Volume {volume_id} not found")
        
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:attach", volume.get_arn()):
            raise PermissionError(f"User does not have permission to attach this volume")
        
        # Attach volume
        volume.attach(instance_id, device)
        self._save_data()
        
        # Emit event
        emit_event(
            EventType.VOLUME_ATTACHED,
            "storage",
            volume.region,
            volume.id,
            volume.get_arn(),
            {
                "instance_id": instance_id,
                "device": device,
                "volume_name": volume.name
            }
        )
        
        return volume
    
    def detach_volume(
        self,
        volume_id: str,
        user: Optional[str] = None,
        force: bool = False
    ) -> Volume:
        """Detach volume from instance"""
        volume = self.get_volume(volume_id)
        if not volume:
            raise ValueError(f"Volume {volume_id} not found")
        
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:detach", volume.get_arn()):
            raise PermissionError(f"User does not have permission to detach this volume")
        
        # Store instance info for event
        instance_id = volume.attached_instance_id
        device = volume.attached_device
        
        # Detach volume
        volume.detach()
        self._save_data()
        
        # Emit event
        emit_event(
            EventType.VOLUME_DETACHED,
            "storage",
            volume.region,
            volume.id,
            volume.get_arn(),
            {
                "instance_id": instance_id,
                "device": device,
                "volume_name": volume.name,
                "force": force
            }
        )
        
        return volume
    
    def delete_volume(
        self,
        volume_id: str,
        user: Optional[str] = None
    ) -> None:
        """Delete a volume"""
        volume = self.get_volume(volume_id)
        if not volume:
            raise ValueError(f"Volume {volume_id} not found")
        
        # Cannot delete attached volume
        if volume.is_attached():
            raise ValueError(f"Cannot delete volume {volume_id} - it is attached to {volume.attached_instance_id}")
        
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:delete", volume.get_arn()):
            raise PermissionError(f"User does not have permission to delete this volume")
        
        # Delete volume
        del self._volumes[volume_id]
        self._save_data()
        
        # Emit event
        emit_event(
            EventType.VOLUME_DELETED,
            "storage",
            volume.region,
            volume.id,
            volume.get_arn(),
            {
                "name": volume.name,
                "size_gb": volume.size_gb,
                "volume_type": volume.volume_type
            }
        )
    
    def create_snapshot(
        self,
        volume_id: str,
        snapshot_name: str,
        description: Optional[str] = None,
        user: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Snapshot:
        """Create a snapshot of a volume"""
        volume = self.get_volume(volume_id)
        if not volume:
            raise ValueError(f"Volume {volume_id} not found")
        
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:snapshot", volume.get_arn()):
            raise PermissionError(f"User does not have permission to snapshot this volume")
        
        # Create snapshot
        snapshot = volume.create_snapshot(
            snapshot_name=snapshot_name,
            description=description,
            owner=user
        )
        
        if tags:
            snapshot.tags = tags
        
        self._snapshots[snapshot.id] = snapshot
        self._save_data()
        
        # Emit event
        emit_event(
            EventType.SNAPSHOT_CREATED,
            "storage",
            volume.region,
            snapshot.id,
            f"arn:cloudsim:storage:{volume.region}:snapshot/{snapshot.id}",
            {
                "name": snapshot_name,
                "volume_id": volume_id,
                "volume_name": volume.name,
                "size_gb": snapshot.size_gb,
                "description": description
            }
        )
        
        return snapshot
    
    def list_snapshots(
        self,
        user: Optional[str] = None,
        volume_id: Optional[str] = None
    ) -> List[Snapshot]:
        """List all snapshots"""
        # Check IAM permission
        if not self.iam_manager.check_permission("storage:list", "*"):
            raise PermissionError(f"User does not have permission to list snapshots")
        
        snapshots = list(self._snapshots.values())
        
        # Filter by volume
        if volume_id:
            snapshots = [s for s in snapshots if s.volume_id == volume_id]
        
        return snapshots
    
    def get_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Get snapshot by ID"""
        return self._snapshots.get(snapshot_id)
    
    def delete_snapshot(
        self,
        snapshot_id: str,
        user: Optional[str] = None
    ) -> None:
        """Delete a snapshot"""
        snapshot = self.get_snapshot(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} not found")
        
        # Check IAM permission
        snapshot_arn = f"arn:cloudsim:storage:{snapshot.region}:snapshot/{snapshot.id}"
        if not self.iam_manager.check_permission("storage:delete", snapshot_arn):
            raise PermissionError(f"User does not have permission to delete this snapshot")
        
        # Delete snapshot
        del self._snapshots[snapshot_id]
        self._save_data()
        
        # Emit event
        emit_event(
            EventType.SNAPSHOT_DELETED,
            "storage",
            snapshot.region,
            snapshot.id,
            snapshot_arn,
            {
                "name": snapshot.name,
                "volume_id": snapshot.volume_id
            }
        )
    
    def get_volume_stats(self) -> Dict[str, Any]:
        """Get volume statistics"""
        total_volumes = len(self._volumes)
        available_volumes = len([v for v in self._volumes.values() if v.state == "available"])
        in_use_volumes = len([v for v in self._volumes.values() if v.state == "in-use"])
        total_storage_gb = sum(v.size_gb for v in self._volumes.values())
        total_snapshots = len(self._snapshots)
        
        return {
            "total_volumes": total_volumes,
            "available_volumes": available_volumes,
            "in_use_volumes": in_use_volumes,
            "total_storage_gb": total_storage_gb,
            "total_snapshots": total_snapshots
        }
