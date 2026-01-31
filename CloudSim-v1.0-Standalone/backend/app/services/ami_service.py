"""
AMI Service

Business logic for managing Amazon Machine Images.
"""

from typing import Optional, List
import docker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ami import AMI
from app.models.instance import Instance
from app.core.resource_ids import generate_id, ResourceType
from app.core.exceptions import ResourceNotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class AMIService:
    """Service for managing AMIs"""
    
    def __init__(self):
        """Initialize Docker client"""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    async def create_image(
        self,
        db: AsyncSession,
        instance_id: str,
        account_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[dict] = None
    ) -> AMI:
        """
        Create AMI from running instance.
        
        Args:
            db: Database session
            instance_id: Source instance ID
            account_id: Account ID
            name: AMI name
            description: AMI description
            tags: Tags dictionary
        
        Returns:
            Created AMI
        
        Raises:
            ResourceNotFoundError: Instance not found
            ValidationError: Instance not in valid state
        """
        # Get source instance
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
            raise ValidationError(
                message=f"Cannot create image from instance in state {instance.state}"
            )
        
        # Generate AMI ID
        ami_id = generate_id(ResourceType.AMI)
        
        # Create AMI record
        ami = AMI(
            ami_id=ami_id,
            account_id=account_id,
            name=name,
            description=description,
            source_instance_id=instance_id,
            state="pending",
            tags=str(tags) if tags else None
        )
        
        db.add(ami)
        await db.flush()
        
        # Commit Docker container to image
        if self.docker_client and instance.docker_container_id:
            try:
                container = self.docker_client.containers.get(instance.docker_container_id)
                
                # Create Docker image tag
                image_tag = f"cloudsim-ami-{ami_id}"
                
                # Commit container to new image
                container.commit(
                    repository="cloudsim-ami",
                    tag=ami_id,
                    message=f"AMI created from instance {instance_id}",
                    author="cloudsim"
                )
                
                # Get committed image
                docker_image = self.docker_client.images.get(f"cloudsim-ami:{ami_id}")
                
                # Update AMI with Docker details
                ami.docker_image_id = docker_image.id
                ami.docker_image_tag = image_tag
                ami.state = "available"
                
                logger.info(f"Created AMI {ami_id} from instance {instance_id}")
                
            except docker.errors.NotFound:
                ami.state = "failed"
                logger.error(f"Failed to create AMI {ami_id}: Container not found")
            except docker.errors.DockerException as e:
                ami.state = "failed"
                logger.error(f"Failed to create AMI {ami_id}: {e}")
        else:
            # No Docker client, mark as available anyway
            ami.state = "available"
        
        await db.commit()
        await db.refresh(ami)
        
        return ami
    
    async def get_image(
        self,
        db: AsyncSession,
        ami_id: str,
        account_id: str
    ) -> AMI:
        """
        Get AMI by ID.
        
        Args:
            db: Database session
            ami_id: AMI ID
            account_id: Account ID
        
        Returns:
            AMI
        
        Raises:
            ResourceNotFoundError: AMI not found
        """
        result = await db.execute(
            select(AMI).where(
                AMI.ami_id == ami_id,
                AMI.account_id == account_id
            )
        )
        ami = result.scalar_one_or_none()
        
        if not ami:
            raise ResourceNotFoundError(
                resource_type="AMI",
                resource_id=ami_id,
                message=f"AMI {ami_id} not found"
            )
        
        return ami
    
    async def describe_images(
        self,
        db: AsyncSession,
        account_id: str,
        ami_ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AMI]:
        """
        List AMIs.
        
        Args:
            db: Database session
            account_id: Account ID
            ami_ids: Optional list of AMI IDs to filter
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of AMI
        """
        query = select(AMI).where(AMI.account_id == account_id)
        
        if ami_ids:
            query = query.where(AMI.ami_id.in_(ami_ids))
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def deregister_image(
        self,
        db: AsyncSession,
        ami_id: str,
        account_id: str
    ):
        """
        Deregister (delete) AMI.
        
        Args:
            db: Database session
            ami_id: AMI ID
            account_id: Account ID
        
        Raises:
            ResourceNotFoundError: AMI not found
        """
        ami = await self.get_image(db, ami_id, account_id)
        
        # Remove Docker image
        if self.docker_client and ami.docker_image_tag:
            try:
                docker_image = self.docker_client.images.get(f"cloudsim-ami:{ami_id}")
                self.docker_client.images.remove(docker_image.id, force=True)
                logger.info(f"Removed Docker image for AMI {ami_id}")
            except docker.errors.NotFound:
                logger.warning(f"Docker image for AMI {ami_id} not found")
            except docker.errors.DockerException as e:
                logger.error(f"Failed to remove Docker image: {e}")
        
        # Delete AMI record
        await db.delete(ami)
        await db.commit()
        
        logger.info(f"Deregistered AMI {ami_id}")


