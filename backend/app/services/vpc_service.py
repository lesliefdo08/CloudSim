"""
VPC Service
Manages Virtual Private Cloud lifecycle and Docker network integration
"""

import logging
import json
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import docker
from docker.errors import DockerException, NotFound

from app.models.vpc import VPC
from app.models.subnet import Subnet
from app.core.resource_ids import generate_id, ResourceType
from app.utils.cidr import (
    validate_cidr,
    calculate_available_ips,
    is_private_cidr
)
from app.core.exceptions import ValidationError, ResourceNotFoundError, ConflictError


logger = logging.getLogger(__name__)


class VPCService:
    """VPC management service with Docker network integration"""
    
    def __init__(self):
        """Initialize VPC service with Docker client"""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.docker_client = None
    
    async def create_vpc(
        self,
        db: AsyncSession,
        account_id: str,
        cidr_block: str,
        name: Optional[str] = None,
        enable_dns_support: bool = True,
        enable_dns_hostnames: bool = False,
        tags: Optional[dict] = None
    ) -> VPC:
        """
        Create a new VPC with Docker network
        
        Args:
            db: Database session
            account_id: AWS account ID
            cidr_block: VPC CIDR block (e.g., "10.0.0.0/16")
            name: VPC name (optional)
            enable_dns_support: Enable DNS resolution
            enable_dns_hostnames: Enable DNS hostnames
            tags: Resource tags
        
        Returns:
            Created VPC
        
        Raises:
            ValidationError: If CIDR block is invalid
        """
        # Validate CIDR block
        is_valid, error_msg = validate_cidr(cidr_block)
        if not is_valid:
            raise ValidationError(message=error_msg)
        
        # Warn if not private CIDR
        if not is_private_cidr(cidr_block):
            logger.warning(f"VPC CIDR {cidr_block} is not in private IP range")
        
        # Generate VPC ID
        vpc_id = generate_id(ResourceType.VPC)
        
        # Create Docker network
        docker_network_id = None
        docker_network_name = f"cloudsim-vpc-{vpc_id}"
        
        if self.docker_client:
            try:
                # Create bridge network with custom subnet
                ipam_pool = docker.types.IPAMPool(
                    subnet=cidr_block
                )
                ipam_config = docker.types.IPAMConfig(
                    pool_configs=[ipam_pool]
                )
                
                network = self.docker_client.networks.create(
                    name=docker_network_name,
                    driver="bridge",
                    ipam=ipam_config,
                    labels={
                        "cloudsim.vpc_id": vpc_id,
                        "cloudsim.account_id": account_id,
                        "cloudsim.cidr_block": cidr_block
                    }
                )
                
                docker_network_id = network.id
                logger.info(f"Created Docker network {docker_network_name} ({docker_network_id})")
            
            except DockerException as e:
                logger.error(f"Failed to create Docker network: {e}")
                # Continue without Docker network (for development)
        
        # Create VPC
        vpc = VPC(
            vpc_id=vpc_id,
            account_id=account_id,
            cidr_block=cidr_block,
            name=name,
            state="available",
            enable_dns_support=enable_dns_support,
            enable_dns_hostnames=enable_dns_hostnames,
            docker_network_id=docker_network_id,
            docker_network_name=docker_network_name,
            tags=json.dumps(tags) if tags else None
        )
        
        db.add(vpc)
        await db.commit()
        await db.refresh(vpc)
        
        logger.info(f"Created VPC {vpc_id} with CIDR {cidr_block}")
        
        return vpc
    
    async def get_vpc(self, db: AsyncSession, vpc_id: str, account_id: str) -> VPC:
        """
        Get VPC by ID
        
        Args:
            db: Database session
            vpc_id: VPC ID
            account_id: AWS account ID
        
        Returns:
            VPC
        
        Raises:
            ResourceNotFoundError: If VPC not found
        """
        result = await db.execute(
            select(VPC).where(
                VPC.vpc_id == vpc_id,
                VPC.account_id == account_id
            )
        )
        vpc = result.scalar_one_or_none()
        
        if not vpc:
            raise ResourceNotFoundError(
                resource_type="VPC",
                resource_id=vpc_id
            )
        
        return vpc
    
    async def list_vpcs(
        self,
        db: AsyncSession,
        account_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[VPC]:
        """
        List VPCs for account
        
        Args:
            db: Database session
            account_id: AWS account ID
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of VPCs
        """
        result = await db.execute(
            select(VPC)
            .where(VPC.account_id == account_id)
            .limit(limit)
            .offset(offset)
        )
        
        return list(result.scalars().all())
    
    async def delete_vpc(self, db: AsyncSession, vpc_id: str, account_id: str) -> None:
        """
        Delete VPC and associated Docker network
        
        Args:
            db: Database session
            vpc_id: VPC ID
            account_id: AWS account ID
        
        Raises:
            ResourceNotFoundError: If VPC not found
            ConflictError: If VPC has subnets
        """
        # Get VPC
        vpc = await self.get_vpc(db, vpc_id, account_id)
        
        # Check for subnets
        result = await db.execute(
            select(Subnet).where(Subnet.vpc_id == vpc_id)
        )
        subnets = result.scalars().all()
        
        if subnets:
            raise ConflictError(
                message=f"Cannot delete VPC {vpc_id} because it has {len(subnets)} subnet(s). Delete subnets first."
            )
        
        # Delete Docker network
        if self.docker_client and vpc.docker_network_id:
            try:
                network = self.docker_client.networks.get(vpc.docker_network_id)
                network.remove()
                logger.info(f"Deleted Docker network {vpc.docker_network_name}")
            except NotFound:
                logger.warning(f"Docker network {vpc.docker_network_name} not found")
            except DockerException as e:
                logger.error(f"Failed to delete Docker network: {e}")
        
        # Delete VPC
        await db.delete(vpc)
        await db.commit()
        
        logger.info(f"Deleted VPC {vpc_id}")
    
    def get_docker_network(self, vpc: VPC):
        """
        Get Docker network for VPC
        
        Args:
            vpc: VPC instance
        
        Returns:
            Docker network object or None
        """
        if not self.docker_client or not vpc.docker_network_id:
            return None
        
        try:
            return self.docker_client.networks.get(vpc.docker_network_id)
        except NotFound:
            logger.warning(f"Docker network {vpc.docker_network_name} not found")
            return None
        except DockerException as e:
            logger.error(f"Failed to get Docker network: {e}")
            return None


