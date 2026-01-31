"""
Volume Schemas

Request/response models for volume and snapshot endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class CreateVolumeRequest(BaseModel):
    """Request to create volume"""
    size_gb: int = Field(..., ge=1, le=16384, description="Volume size in GB (1-16384)")
    volume_type: str = Field("gp2", description="Volume type (gp2, gp3, io1, io2, st1, sc1)")
    availability_zone: str = Field("us-east-1a", description="Availability zone")
    snapshot_id: Optional[str] = Field(None, description="Snapshot ID to restore from")
    tags: Optional[dict] = Field(None, description="Tags for the volume")


class AttachVolumeRequest(BaseModel):
    """Request to attach volume to instance"""
    instance_id: str = Field(..., description="Instance ID to attach to")
    device_name: str = Field("/dev/sdf", description="Device name (e.g., /dev/sdf)")


class DetachVolumeRequest(BaseModel):
    """Request to detach volume"""
    force: bool = Field(False, description="Force detachment")


class VolumeResponse(BaseModel):
    """Volume response"""
    model_config = ConfigDict(from_attributes=True)
    
    volume_id: str
    account_id: str
    size_gb: int
    volume_type: str
    state: str
    attached_instance_id: Optional[str]
    device_name: Optional[str]
    availability_zone: str
    docker_volume_name: Optional[str]
    tags: Optional[str]
    created_at: datetime


class DescribeVolumesResponse(BaseModel):
    """Response for describe volumes"""
    volumes: List[VolumeResponse]
    total: int


class CreateSnapshotRequest(BaseModel):
    """Request to create snapshot"""
    volume_id: str = Field(..., description="Volume ID to snapshot")
    description: Optional[str] = Field(None, max_length=500, description="Snapshot description")
    tags: Optional[dict] = Field(None, description="Tags for the snapshot")


class SnapshotResponse(BaseModel):
    """Snapshot response"""
    model_config = ConfigDict(from_attributes=True)
    
    snapshot_id: str
    account_id: str
    volume_id: str
    size_gb: int
    state: str
    description: Optional[str]
    docker_volume_backup: Optional[str]
    tags: Optional[str]
    created_at: datetime


class DescribeSnapshotsResponse(BaseModel):
    """Response for describe snapshots"""
    snapshots: List[SnapshotResponse]
    total: int
