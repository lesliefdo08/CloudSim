"""
Subnet Service
Manages Subnet lifecycle within VPCs
"""

import logging
import json
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vpc import VPC
from app.models.subnet import Subnet
from app.core.resource_ids import generate_id, ResourceType
from app.utils.cidr import (
    validate_subnet_cidr,
    check_subnet_overlaps,
    calculate_available_ips
)
from app.core.exceptions import ValidationError, ResourceNotFoundError


logger = logging.getLogger(__name__)


class SubnetService:
    """Subnet management service"""
    
    async def create_subnet(
        self,
        db: AsyncSession,
        vpc_id: str,
        account_id: str,
        cidr_block: str,
        name: Optional[str] = None,
        availability_zone: str = "us-east-1a",
        map_public_ip_on_launch: bool = False,
        tags: Optional[dict] = None
    ) -> Subnet:
        """
        Create a new subnet within VPC
        
        Args:
            db: Database session
            vpc_id: VPC ID
            account_id: AWS account ID
            cidr_block: Subnet CIDR block (e.g., "10.0.1.0/24")
            name: Subnet name (optional)
            availability_zone: Availability zone
            map_public_ip_on_launch: Auto-assign public IPs
            tags: Resource tags
        
        Returns:
            Created Subnet
        
        Raises:
            ResourceNotFoundError: If VPC not found
            ValidationError: If CIDR block is invalid or overlaps
        """
        # Get VPC
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
        
        # Validate subnet CIDR is within VPC CIDR
        is_valid, error_msg = validate_subnet_cidr(vpc.cidr_block, cidr_block)
        if not is_valid:
            raise ValidationError(message=error_msg)
        
        # Get existing subnets in VPC
        result = await db.execute(
            select(Subnet).where(Subnet.vpc_id == vpc_id)
        )
        existing_subnets = result.scalars().all()
        existing_cidrs = [s.cidr_block for s in existing_subnets]
        
        # Check for overlaps
        has_overlap, error_msg = check_subnet_overlaps(
            vpc.cidr_block,
            existing_cidrs,
            cidr_block
        )
        if has_overlap:
            raise ValidationError(message=error_msg)
        
        # Calculate available IPs
        available_ips = calculate_available_ips(cidr_block)
        
        # Generate subnet ID
        subnet_id = generate_id(ResourceType.SUBNET)
        
        # Create subnet
        subnet = Subnet(
            subnet_id=subnet_id,
            vpc_id=vpc_id,
            account_id=account_id,
            cidr_block=cidr_block,
            name=name,
            state="available",
            availability_zone=availability_zone,
            available_ip_address_count=available_ips,
            map_public_ip_on_launch=map_public_ip_on_launch,
            tags=json.dumps(tags) if tags else None
        )
        
        db.add(subnet)
        await db.commit()
        await db.refresh(subnet)
        
        logger.info(f"Created subnet {subnet_id} in VPC {vpc_id} with CIDR {cidr_block}")
        
        return subnet
    
    async def get_subnet(
        self,
        db: AsyncSession,
        subnet_id: str,
        account_id: str
    ) -> Subnet:
        """
        Get subnet by ID
        
        Args:
            db: Database session
            subnet_id: Subnet ID
            account_id: AWS account ID
        
        Returns:
            Subnet
        
        Raises:
            ResourceNotFoundError: If subnet not found
        """
        result = await db.execute(
            select(Subnet).where(
                Subnet.subnet_id == subnet_id,
                Subnet.account_id == account_id
            )
        )
        subnet = result.scalar_one_or_none()
        
        if not subnet:
            raise ResourceNotFoundError(
                resource_type="Subnet",
                resource_id=subnet_id
            )
        
        return subnet
    
    async def list_subnets(
        self,
        db: AsyncSession,
        account_id: str,
        vpc_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Subnet]:
        """
        List subnets for account
        
        Args:
            db: Database session
            account_id: AWS account ID
            vpc_id: Filter by VPC ID (optional)
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of Subnets
        """
        query = select(Subnet).where(Subnet.account_id == account_id)
        
        if vpc_id:
            query = query.where(Subnet.vpc_id == vpc_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        
        return list(result.scalars().all())
    
    async def delete_subnet(
        self,
        db: AsyncSession,
        subnet_id: str,
        account_id: str
    ) -> None:
        """
        Delete subnet
        
        Args:
            db: Database session
            subnet_id: Subnet ID
            account_id: AWS account ID
        
        Raises:
            ResourceNotFoundError: If subnet not found
        """
        # Get subnet
        subnet = await self.get_subnet(db, subnet_id, account_id)
        
        # TODO: Check if subnet has instances
        # For now, allow deletion
        
        # Delete subnet
        await db.delete(subnet)
        await db.commit()
        
        logger.info(f"Deleted subnet {subnet_id}")

