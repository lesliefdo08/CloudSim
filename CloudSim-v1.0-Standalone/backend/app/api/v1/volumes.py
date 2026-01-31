"""
Volume API Routes

Endpoints for managing EBS volumes and snapshots.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.middleware.auth import get_current_account
from app.middleware.authorization import RequirePermission
from app.models.iam_account import Account
from app.models.volume import Volume
from app.models.snapshot import Snapshot
from app.services.volume_service import VolumeService
from app.schemas.volume import (
    CreateVolumeRequest,
    AttachVolumeRequest,
    DetachVolumeRequest,
    VolumeResponse,
    DescribeVolumesResponse,
    CreateSnapshotRequest,
    SnapshotResponse,
    DescribeSnapshotsResponse
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/volumes", tags=["EBS Volumes"])


@router.post(
    "",
    response_model=VolumeResponse,
    dependencies=[Depends(RequirePermission("ec2:CreateVolume", "*"))]
)
async def create_volume(
    request: CreateVolumeRequest,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Create EBS volume.
    
    Creates a new block storage volume. Optionally restore from a snapshot.
    
    Permissions: ec2:CreateVolume
    """
    service = VolumeService()
    
    volume = await service.create_volume(
        db=db,
        account_id=current_account.account_id,
        size_gb=request.size_gb,
        volume_type=request.volume_type,
        availability_zone=request.availability_zone,
        snapshot_id=request.snapshot_id,
        tags=request.tags
    )
    
    return volume


@router.get(
    "",
    response_model=DescribeVolumesResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeVolumes", "*"))]
)
async def describe_volumes(
    volume_ids: Optional[str] = Query(None, description="Comma-separated volume IDs"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    List volumes.
    
    Returns list of volumes owned by the current account.
    Optionally filter by specific volume IDs.
    
    Permissions: ec2:DescribeVolumes
    """
    service = VolumeService()
    
    # Parse volume IDs
    volume_id_list = None
    if volume_ids:
        volume_id_list = [vid.strip() for vid in volume_ids.split(",") if vid.strip()]
    
    # Get volumes
    volumes = await service.describe_volumes(
        db=db,
        account_id=current_account.account_id,
        volume_ids=volume_id_list,
        limit=limit,
        offset=offset
    )
    
    # Count total
    query = select(func.count()).select_from(Volume).where(
        Volume.account_id == current_account.account_id
    )
    if volume_id_list:
        query = query.where(Volume.volume_id.in_(volume_id_list))
    
    result = await db.execute(query)
    total = result.scalar()
    
    return DescribeVolumesResponse(volumes=volumes, total=total)


@router.get(
    "/{volume_id}",
    response_model=VolumeResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeVolumes", "*"))]
)
async def get_volume(
    volume_id: str,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Get volume by ID.
    
    Returns details of a specific volume.
    
    Permissions: ec2:DescribeVolumes
    """
    service = VolumeService()
    
    volume = await service.get_volume(
        db=db,
        volume_id=volume_id,
        account_id=current_account.account_id
    )
    
    return volume


@router.delete(
    "/{volume_id}",
    dependencies=[Depends(RequirePermission("ec2:DeleteVolume", "*"))]
)
async def delete_volume(
    volume_id: str,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Delete volume.
    
    Deletes the volume and its associated Docker volume.
    Volume must not be attached to any instance.
    
    Permissions: ec2:DeleteVolume
    """
    service = VolumeService()
    
    await service.delete_volume(
        db=db,
        volume_id=volume_id,
        account_id=current_account.account_id
    )
    
    return {"message": f"Volume {volume_id} deleted successfully"}


@router.post(
    "/{volume_id}/attach",
    response_model=VolumeResponse,
    dependencies=[Depends(RequirePermission("ec2:AttachVolume", "*"))]
)
async def attach_volume(
    volume_id: str,
    request: AttachVolumeRequest,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Attach volume to instance.
    
    Attaches the volume to a running or stopped instance.
    
    Permissions: ec2:AttachVolume
    """
    service = VolumeService()
    
    volume = await service.attach_volume(
        db=db,
        volume_id=volume_id,
        account_id=current_account.account_id,
        instance_id=request.instance_id,
        device_name=request.device_name
    )
    
    return volume


@router.post(
    "/{volume_id}/detach",
    response_model=VolumeResponse,
    dependencies=[Depends(RequirePermission("ec2:DetachVolume", "*"))]
)
async def detach_volume(
    volume_id: str,
    request: DetachVolumeRequest,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Detach volume from instance.
    
    Detaches the volume from its attached instance.
    
    Permissions: ec2:DetachVolume
    """
    service = VolumeService()
    
    volume = await service.detach_volume(
        db=db,
        volume_id=volume_id,
        account_id=current_account.account_id,
        force=request.force
    )
    
    return volume


# Snapshot endpoints
snapshots_router = APIRouter(prefix="/snapshots", tags=["EBS Snapshots"])


@snapshots_router.post(
    "",
    response_model=SnapshotResponse,
    dependencies=[Depends(RequirePermission("ec2:CreateSnapshot", "*"))]
)
async def create_snapshot(
    request: CreateSnapshotRequest,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Create snapshot from volume.
    
    Creates a point-in-time backup of a volume.
    
    Permissions: ec2:CreateSnapshot
    """
    service = VolumeService()
    
    snapshot = await service.create_snapshot(
        db=db,
        volume_id=request.volume_id,
        account_id=current_account.account_id,
        description=request.description,
        tags=request.tags
    )
    
    return snapshot


@snapshots_router.get(
    "",
    response_model=DescribeSnapshotsResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeSnapshots", "*"))]
)
async def describe_snapshots(
    snapshot_ids: Optional[str] = Query(None, description="Comma-separated snapshot IDs"),
    volume_id: Optional[str] = Query(None, description="Filter by volume ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    List snapshots.
    
    Returns list of snapshots owned by the current account.
    Optionally filter by specific snapshot IDs or volume ID.
    
    Permissions: ec2:DescribeSnapshots
    """
    service = VolumeService()
    
    # Parse snapshot IDs
    snapshot_id_list = None
    if snapshot_ids:
        snapshot_id_list = [sid.strip() for sid in snapshot_ids.split(",") if sid.strip()]
    
    # Get snapshots
    snapshots = await service.describe_snapshots(
        db=db,
        account_id=current_account.account_id,
        snapshot_ids=snapshot_id_list,
        volume_id=volume_id,
        limit=limit,
        offset=offset
    )
    
    # Count total
    query = select(func.count()).select_from(Snapshot).where(
        Snapshot.account_id == current_account.account_id
    )
    if snapshot_id_list:
        query = query.where(Snapshot.snapshot_id.in_(snapshot_id_list))
    if volume_id:
        query = query.where(Snapshot.volume_id == volume_id)
    
    result = await db.execute(query)
    total = result.scalar()
    
    return DescribeSnapshotsResponse(snapshots=snapshots, total=total)


@snapshots_router.get(
    "/{snapshot_id}",
    response_model=SnapshotResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeSnapshots", "*"))]
)
async def get_snapshot(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Get snapshot by ID.
    
    Returns details of a specific snapshot.
    
    Permissions: ec2:DescribeSnapshots
    """
    service = VolumeService()
    
    snapshot = await service.get_snapshot(
        db=db,
        snapshot_id=snapshot_id,
        account_id=current_account.account_id
    )
    
    return snapshot


@snapshots_router.delete(
    "/{snapshot_id}",
    dependencies=[Depends(RequirePermission("ec2:DeleteSnapshot", "*"))]
)
async def delete_snapshot(
    snapshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Delete snapshot.
    
    Deletes the snapshot and its backup data.
    
    Permissions: ec2:DeleteSnapshot
    """
    service = VolumeService()
    
    await service.delete_snapshot(
        db=db,
        snapshot_id=snapshot_id,
        account_id=current_account.account_id
    )
    
    return {"message": f"Snapshot {snapshot_id} deleted successfully"}


# Include snapshots router in main volume router
router.include_router(snapshots_router)



