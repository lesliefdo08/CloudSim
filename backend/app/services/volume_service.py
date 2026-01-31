"""
Volume Service

Business logic for EBS volume lifecycle management with Docker integration.
"""

from typing import Optional, List
import docker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.volume import Volume
from app.models.snapshot import Snapshot
from app.models.instance import Instance
from app.core.resource_ids import generate_id, ResourceType
from app.core.exceptions import ResourceNotFoundError, ValidationError, ConflictError
import logging
import json

logger = logging.getLogger(__name__)


class VolumeService:
    """Service for managing EBS volumes with Docker volumes"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    async def create_volume(
        self,
        db: AsyncSession,
        account_id: str,
        size_gb: int,
        volume_type: str = "gp2",
        availability_zone: str = "us-east-1a",
        snapshot_id: Optional[str] = None,
        tags: Optional[dict] = None
    ) -> Volume:
        """
        Create new EBS volume.
        
        Args:
            db: Database session
            account_id: Account ID
            size_gb: Volume size in GB
            volume_type: Volume type (gp2, gp3, io1, io2, st1, sc1)
            availability_zone: Availability zone
            snapshot_id: Optional snapshot to restore from
            tags: Tags dictionary
        
        Returns:
            Created Volume
        
        Raises:
            ValidationError: Invalid parameters
            ResourceNotFoundError: Snapshot not found
        """
        # Validate volume type
        valid_types = ["gp2", "gp3", "io1", "io2", "st1", "sc1"]
        if volume_type not in valid_types:
            raise ValidationError(
                message=f"Invalid volume type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Validate size
        if size_gb < 1 or size_gb > 16384:  # AWS limit is 16 TiB
            raise ValidationError(
                message="Volume size must be between 1 and 16384 GB"
            )
        
        # If restoring from snapshot, verify it exists
        source_snapshot = None
        if snapshot_id:
            result = await db.execute(
                select(Snapshot).where(
                    Snapshot.snapshot_id == snapshot_id,
                    Snapshot.account_id == account_id
                )
            )
            source_snapshot = result.scalar_one_or_none()
            
            if not source_snapshot:
                raise ResourceNotFoundError(
                    resource_type="Snapshot",
                    resource_id=snapshot_id,
                    message=f"Snapshot {snapshot_id} not found"
                )
            
            if source_snapshot.state != "completed":
                raise ValidationError(
                    message=f"Snapshot {snapshot_id} is not in completed state"
                )
            
            # Use snapshot size if not specified
            if size_gb < source_snapshot.size_gb:
                raise ValidationError(
                    message=f"Volume size must be at least {source_snapshot.size_gb} GB (snapshot size)"
                )
        
        # Generate volume ID
        volume_id = generate_id(ResourceType.VOLUME)
        
        # Create volume record
        volume = Volume(
            volume_id=volume_id,
            account_id=account_id,
            size_gb=size_gb,
            volume_type=volume_type,
            state="creating",
            availability_zone=availability_zone,
            tags=json.dumps(tags) if tags else None
        )
        
        db.add(volume)
        await db.flush()
        
        # Create Docker volume
        if self.docker_client:
            try:
                docker_volume_name = f"cloudsim-volume-{volume_id}"
                
                # Create Docker volume with size label
                docker_volume = self.docker_client.volumes.create(
                    name=docker_volume_name,
                    driver="local",
                    labels={
                        "cloudsim.volume_id": volume_id,
                        "cloudsim.account_id": account_id,
                        "cloudsim.size_gb": str(size_gb),
                        "cloudsim.volume_type": volume_type
                    }
                )
                
                # If restoring from snapshot, copy data
                if source_snapshot and source_snapshot.docker_volume_backup:
                    # TODO: Implement snapshot restore (copy data from backup volume)
                    logger.info(f"Snapshot restore not yet implemented for {snapshot_id}")
                
                # Update volume with Docker details
                volume.docker_volume_name = docker_volume_name
                volume.state = "available"
                
                logger.info(f"Created Docker volume {docker_volume_name} for {volume_id}")
                
            except docker.errors.DockerException as e:
                volume.state = "error"
                logger.error(f"Failed to create Docker volume: {e}")
        else:
            # No Docker client, mark as available anyway
            volume.state = "available"
        
        await db.commit()
        await db.refresh(volume)
        
        return volume
    
    async def get_volume(
        self,
        db: AsyncSession,
        volume_id: str,
        account_id: str
    ) -> Volume:
        """
        Get volume by ID.
        
        Args:
            db: Database session
            volume_id: Volume ID
            account_id: Account ID
        
        Returns:
            Volume
        
        Raises:
            ResourceNotFoundError: Volume not found
        """
        result = await db.execute(
            select(Volume).where(
                Volume.volume_id == volume_id,
                Volume.account_id == account_id
            )
        )
        volume = result.scalar_one_or_none()
        
        if not volume:
            raise ResourceNotFoundError(
                resource_type="Volume",
                resource_id=volume_id,
                message=f"Volume {volume_id} not found"
            )
        
        return volume
    
    async def describe_volumes(
        self,
        db: AsyncSession,
        account_id: str,
        volume_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Volume]:
        """
        List volumes.
        
        Args:
            db: Database session
            account_id: Account ID
            volume_ids: Optional list of volume IDs to filter
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of Volume
        """
        query = select(Volume).where(Volume.account_id == account_id)
        
        if volume_ids:
            query = query.where(Volume.volume_id.in_(volume_ids))
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_volume(
        self,
        db: AsyncSession,
        volume_id: str,
        account_id: str
    ):
        """
        Delete volume.
        
        Args:
            db: Database session
            volume_id: Volume ID
            account_id: Account ID
        
        Raises:
            ResourceNotFoundError: Volume not found
            ConflictError: Volume is attached to an instance
        """
        volume = await self.get_volume(db, volume_id, account_id)
        
        # Cannot delete if attached
        if volume.state == "in-use" or volume.attached_instance_id:
            raise ConflictError(
                message=f"Volume {volume_id} is attached to instance {volume.attached_instance_id}. Detach first."
            )
        
        # Update state
        volume.state = "deleting"
        await db.commit()
        
        # Remove Docker volume
        if self.docker_client and volume.docker_volume_name:
            try:
                docker_volume = self.docker_client.volumes.get(volume.docker_volume_name)
                docker_volume.remove(force=True)
                logger.info(f"Removed Docker volume {volume.docker_volume_name}")
            except docker.errors.NotFound:
                logger.warning(f"Docker volume {volume.docker_volume_name} not found")
            except docker.errors.DockerException as e:
                logger.error(f"Failed to remove Docker volume: {e}")
        
        # Delete volume record
        await db.delete(volume)
        await db.commit()
        
        logger.info(f"Deleted volume {volume_id}")
    
    async def attach_volume(
        self,
        db: AsyncSession,
        volume_id: str,
        account_id: str,
        instance_id: str,
        device_name: str = "/dev/sdf"
    ) -> Volume:
        """
        Attach volume to instance.
        
        Args:
            db: Database session
            volume_id: Volume ID
            account_id: Account ID
            instance_id: Instance ID to attach to
            device_name: Device name (e.g., /dev/sdf)
        
        Returns:
            Updated Volume
        
        Raises:
            ResourceNotFoundError: Volume or instance not found
            ConflictError: Volume already attached or instance not running
        """
        # Get volume
        volume = await self.get_volume(db, volume_id, account_id)
        
        # Check volume state
        if volume.state != "available":
            raise ConflictError(
                message=f"Volume {volume_id} is not available (state: {volume.state})"
            )
        
        # Get instance
        result = await db.execute(
            select(Instance).where(
                Instance.instance_id == instance_id,
                Instance.account_id == account_id
            )
        )
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise ResourceNotFoundError(
                resource_type="Instance",
                resource_id=instance_id,
                message=f"Instance {instance_id} not found"
            )
        
        # Instance must be running or stopped
        if instance.state not in ["running", "stopped"]:
            raise ConflictError(
                message=f"Cannot attach volume to instance in state {instance.state}"
            )
        
        # Attach Docker volume to container
        if self.docker_client and volume.docker_volume_name and instance.docker_container_id:
            try:
                container = self.docker_client.containers.get(instance.docker_container_id)
                
                # Mount volume (requires container restart for Docker API)
                # Note: In real AWS, this is hot-pluggable. In Docker, we need to restart or use exec
                logger.info(f"Attaching Docker volume {volume.docker_volume_name} to container {instance.docker_container_id}")
                
                # For simplicity, we'll just record the attachment
                # In a full implementation, we'd use docker exec to mount or restart container with new volume
                
            except docker.errors.NotFound:
                logger.error(f"Container {instance.docker_container_id} not found")
            except docker.errors.DockerException as e:
                logger.error(f"Failed to attach volume: {e}")
        
        # Update volume record
        volume.state = "in-use"
        volume.attached_instance_id = instance_id
        volume.device_name = device_name
        
        await db.commit()
        await db.refresh(volume)
        
        logger.info(f"Attached volume {volume_id} to instance {instance_id} as {device_name}")
        
        return volume
    
    async def detach_volume(
        self,
        db: AsyncSession,
        volume_id: str,
        account_id: str,
        force: bool = False
    ) -> Volume:
        """
        Detach volume from instance.
        
        Args:
            db: Database session
            volume_id: Volume ID
            account_id: Account ID
            force: Force detachment
        
        Returns:
            Updated Volume
        
        Raises:
            ResourceNotFoundError: Volume not found
            ConflictError: Volume not attached
        """
        # Get volume
        volume = await self.get_volume(db, volume_id, account_id)
        
        # Check if attached
        if volume.state != "in-use" or not volume.attached_instance_id:
            raise ConflictError(
                message=f"Volume {volume_id} is not attached to any instance"
            )
        
        # Detach from Docker container
        if self.docker_client and volume.docker_volume_name and volume.attached_instance_id:
            try:
                # Get instance
                result = await db.execute(
                    select(Instance).where(
                        Instance.instance_id == volume.attached_instance_id,
                        Instance.account_id == account_id
                    )
                )
                instance = result.scalar_one_or_none()
                
                if instance and instance.docker_container_id:
                    logger.info(f"Detaching Docker volume {volume.docker_volume_name} from container {instance.docker_container_id}")
                    # In full implementation, would unmount volume
                
            except docker.errors.DockerException as e:
                if not force:
                    raise ConflictError(
                        message=f"Failed to detach volume: {e}"
                    )
                logger.error(f"Failed to detach volume (forced): {e}")
        
        # Update volume record
        volume.state = "available"
        volume.attached_instance_id = None
        volume.device_name = None
        
        await db.commit()
        await db.refresh(volume)
        
        logger.info(f"Detached volume {volume_id}")
        
        return volume
    
    async def create_snapshot(
        self,
        db: AsyncSession,
        volume_id: str,
        account_id: str,
        description: Optional[str] = None,
        tags: Optional[dict] = None
    ) -> Snapshot:
        """
        Create snapshot from volume.
        
        Args:
            db: Database session
            volume_id: Volume ID
            account_id: Account ID
            description: Snapshot description
            tags: Tags dictionary
        
        Returns:
            Created Snapshot
        
        Raises:
            ResourceNotFoundError: Volume not found
        """
        # Get volume
        volume = await self.get_volume(db, volume_id, account_id)
        
        # Generate snapshot ID
        snapshot_id = generate_id(ResourceType.SNAPSHOT)
        
        # Create snapshot record
        snapshot = Snapshot(
            snapshot_id=snapshot_id,
            account_id=account_id,
            volume_id=volume_id,
            size_gb=volume.size_gb,
            state="pending",
            description=description,
            tags=json.dumps(tags) if tags else None
        )
        
        db.add(snapshot)
        await db.flush()
        
        # Create Docker volume backup
        if self.docker_client and volume.docker_volume_name:
            try:
                backup_volume_name = f"cloudsim-snapshot-{snapshot_id}"
                
                # Create backup volume
                backup_volume = self.docker_client.volumes.create(
                    name=backup_volume_name,
                    driver="local",
                    labels={
                        "cloudsim.snapshot_id": snapshot_id,
                        "cloudsim.volume_id": volume_id,
                        "cloudsim.account_id": account_id
                    }
                )
                
                # TODO: Copy data from source volume to backup
                # This would typically involve running a container to copy data
                logger.info(f"Created snapshot backup volume {backup_volume_name}")
                
                # Update snapshot
                snapshot.docker_volume_backup = backup_volume_name
                snapshot.state = "completed"
                
            except docker.errors.DockerException as e:
                snapshot.state = "error"
                logger.error(f"Failed to create snapshot: {e}")
        else:
            # No Docker client, mark as completed
            snapshot.state = "completed"
        
        await db.commit()
        await db.refresh(snapshot)
        
        logger.info(f"Created snapshot {snapshot_id} from volume {volume_id}")
        
        return snapshot
    
    async def get_snapshot(
        self,
        db: AsyncSession,
        snapshot_id: str,
        account_id: str
    ) -> Snapshot:
        """Get snapshot by ID"""
        result = await db.execute(
            select(Snapshot).where(
                Snapshot.snapshot_id == snapshot_id,
                Snapshot.account_id == account_id
            )
        )
        snapshot = result.scalar_one_or_none()
        
        if not snapshot:
            raise ResourceNotFoundError(
                resource_type="Snapshot",
                resource_id=snapshot_id,
                message=f"Snapshot {snapshot_id} not found"
            )
        
        return snapshot
    
    async def describe_snapshots(
        self,
        db: AsyncSession,
        account_id: str,
        snapshot_ids: Optional[List[str]] = None,
        volume_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Snapshot]:
        """List snapshots"""
        query = select(Snapshot).where(Snapshot.account_id == account_id)
        
        if snapshot_ids:
            query = query.where(Snapshot.snapshot_id.in_(snapshot_ids))
        
        if volume_id:
            query = query.where(Snapshot.volume_id == volume_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_snapshot(
        self,
        db: AsyncSession,
        snapshot_id: str,
        account_id: str
    ):
        """Delete snapshot"""
        snapshot = await self.get_snapshot(db, snapshot_id, account_id)
        
        # Update state
        snapshot.state = "deleting"
        await db.commit()
        
        # Remove Docker backup volume
        if self.docker_client and snapshot.docker_volume_backup:
            try:
                backup_volume = self.docker_client.volumes.get(snapshot.docker_volume_backup)
                backup_volume.remove(force=True)
                logger.info(f"Removed snapshot backup volume {snapshot.docker_volume_backup}")
            except docker.errors.NotFound:
                logger.warning(f"Snapshot backup volume not found")
            except docker.errors.DockerException as e:
                logger.error(f"Failed to remove snapshot backup: {e}")
        
        # Delete snapshot record
        await db.delete(snapshot)
        await db.commit()
        
        logger.info(f"Deleted snapshot {snapshot_id}")


