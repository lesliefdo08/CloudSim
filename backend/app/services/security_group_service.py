"""
Security Group Service

Business logic for managing security groups and rules.
Handles Docker port exposure enforcement.
"""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.security_group import SecurityGroup
from app.models.security_group_rule import SecurityGroupRule
from app.models.vpc import VPC
from app.core.resource_ids import generate_id, ResourceType
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.utils.port_validation import (
    validate_protocol,
    validate_port_range,
    validate_rule_source
)
import logging

logger = logging.getLogger(__name__)


class SecurityGroupService:
    """Service for managing security groups and rules"""
    
    async def create_security_group(
        self,
        db: AsyncSession,
        vpc_id: str,
        account_id: str,
        group_name: str,
        description: Optional[str] = None,
        tags: Optional[dict] = None
    ) -> SecurityGroup:
        """
        Create a new security group.
        
        Args:
            db: Database session
            vpc_id: VPC ID
            account_id: Account ID
            group_name: Security group name
            description: Description
            tags: Tags dictionary
        
        Returns:
            Created SecurityGroup
        
        Raises:
            ResourceNotFoundError: VPC not found
            ValidationError: Invalid parameters
        """
        # Verify VPC exists
        result = await db.execute(
            select(VPC).where(VPC.vpc_id == vpc_id, VPC.account_id == account_id)
        )
        vpc = result.scalar_one_or_none()
        
        if not vpc:
            raise ResourceNotFoundError(
                resource_type="VPC",
                resource_id=vpc_id,
                message=f"VPC {vpc_id} not found"
            )
        
        # Check for duplicate group name in VPC
        result = await db.execute(
            select(SecurityGroup).where(
                SecurityGroup.vpc_id == vpc_id,
                SecurityGroup.group_name == group_name
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValidationError(
                message=f"Security group with name '{group_name}' already exists in VPC {vpc_id}"
            )
        
        # Generate group ID
        group_id = generate_id(ResourceType.SECURITY_GROUP)
        
        # Create security group
        security_group = SecurityGroup(
            group_id=group_id,
            vpc_id=vpc_id,
            account_id=account_id,
            group_name=group_name,
            description=description,
            is_default=False,
            tags=str(tags) if tags else None
        )
        
        db.add(security_group)
        await db.commit()
        await db.refresh(security_group)
        
        logger.info(f"Created security group {group_id} in VPC {vpc_id}")
        
        return security_group
    
    async def get_security_group(
        self,
        db: AsyncSession,
        group_id: str,
        account_id: str
    ) -> SecurityGroup:
        """
        Get security group by ID.
        
        Args:
            db: Database session
            group_id: Security group ID
            account_id: Account ID
        
        Returns:
            SecurityGroup
        
        Raises:
            ResourceNotFoundError: Security group not found
        """
        result = await db.execute(
            select(SecurityGroup).where(
                SecurityGroup.group_id == group_id,
                SecurityGroup.account_id == account_id
            )
        )
        security_group = result.scalar_one_or_none()
        
        if not security_group:
            raise ResourceNotFoundError(
                resource_type="SecurityGroup",
                resource_id=group_id,
                message=f"Security group {group_id} not found"
            )
        
        return security_group
    
    async def list_security_groups(
        self,
        db: AsyncSession,
        account_id: str,
        vpc_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[SecurityGroup]:
        """
        List security groups.
        
        Args:
            db: Database session
            account_id: Account ID
            vpc_id: Optional VPC ID filter
            limit: Maximum results
            offset: Offset for pagination
        
        Returns:
            List of SecurityGroup
        """
        query = select(SecurityGroup).where(SecurityGroup.account_id == account_id)
        
        if vpc_id:
            query = query.where(SecurityGroup.vpc_id == vpc_id)
        
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def delete_security_group(
        self,
        db: AsyncSession,
        group_id: str,
        account_id: str
    ):
        """
        Delete security group.
        
        Args:
            db: Database session
            group_id: Security group ID
            account_id: Account ID
        
        Raises:
            ResourceNotFoundError: Security group not found
            ValidationError: Cannot delete default security group
        """
        security_group = await self.get_security_group(db, group_id, account_id)
        
        # Cannot delete default security group
        if security_group.is_default:
            raise ValidationError(
                message="Cannot delete default security group"
            )
        
        # TODO: Check if security group is attached to any instances
        # For now, we allow deletion
        
        await db.delete(security_group)
        await db.commit()
        
        logger.info(f"Deleted security group {group_id}")
    
    async def authorize_ingress(
        self,
        db: AsyncSession,
        group_id: str,
        account_id: str,
        ip_protocol: str,
        from_port: Optional[int] = None,
        to_port: Optional[int] = None,
        cidr_ipv4: Optional[str] = None,
        source_security_group_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> SecurityGroupRule:
        """
        Add ingress rule to security group.
        
        Args:
            db: Database session
            group_id: Security group ID
            account_id: Account ID
            ip_protocol: Protocol (tcp, udp, icmp, -1)
            from_port: Start port
            to_port: End port
            cidr_ipv4: CIDR block
            source_security_group_id: Source security group ID
            description: Rule description
        
        Returns:
            Created SecurityGroupRule
        
        Raises:
            ResourceNotFoundError: Security group not found
            ValidationError: Invalid rule parameters
        """
        # Verify security group exists
        security_group = await self.get_security_group(db, group_id, account_id)
        
        # Validate protocol
        is_valid, error = validate_protocol(ip_protocol)
        if not is_valid:
            raise ValidationError(message=error)
        
        # Validate port range
        is_valid, error = validate_port_range(from_port, to_port, ip_protocol)
        if not is_valid:
            raise ValidationError(message=error)
        
        # Validate source
        is_valid, error = validate_rule_source(cidr_ipv4, source_security_group_id)
        if not is_valid:
            raise ValidationError(message=error)
        
        # Generate rule ID
        rule_id = generate_id(ResourceType.SECURITY_GROUP_RULE)
        
        # Create rule
        rule = SecurityGroupRule(
            rule_id=rule_id,
            group_id=group_id,
            rule_type="ingress",
            ip_protocol=ip_protocol.lower(),
            from_port=from_port,
            to_port=to_port,
            cidr_ipv4=cidr_ipv4,
            source_security_group_id=source_security_group_id,
            description=description
        )
        
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"Added ingress rule {rule_id} to security group {group_id}")
        
        return rule
    
    async def authorize_egress(
        self,
        db: AsyncSession,
        group_id: str,
        account_id: str,
        ip_protocol: str,
        from_port: Optional[int] = None,
        to_port: Optional[int] = None,
        cidr_ipv4: Optional[str] = None,
        destination_security_group_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> SecurityGroupRule:
        """
        Add egress rule to security group.
        
        Args:
            db: Database session
            group_id: Security group ID
            account_id: Account ID
            ip_protocol: Protocol (tcp, udp, icmp, -1)
            from_port: Start port
            to_port: End port
            cidr_ipv4: CIDR block
            destination_security_group_id: Destination security group ID
            description: Rule description
        
        Returns:
            Created SecurityGroupRule
        
        Raises:
            ResourceNotFoundError: Security group not found
            ValidationError: Invalid rule parameters
        """
        # Verify security group exists
        security_group = await self.get_security_group(db, group_id, account_id)
        
        # Validate protocol
        is_valid, error = validate_protocol(ip_protocol)
        if not is_valid:
            raise ValidationError(message=error)
        
        # Validate port range
        is_valid, error = validate_port_range(from_port, to_port, ip_protocol)
        if not is_valid:
            raise ValidationError(message=error)
        
        # Validate destination
        is_valid, error = validate_rule_source(cidr_ipv4, destination_security_group_id)
        if not is_valid:
            raise ValidationError(message=error)
        
        # Generate rule ID
        rule_id = generate_id(ResourceType.SECURITY_GROUP_RULE)
        
        # Create rule
        rule = SecurityGroupRule(
            rule_id=rule_id,
            group_id=group_id,
            rule_type="egress",
            ip_protocol=ip_protocol.lower(),
            from_port=from_port,
            to_port=to_port,
            cidr_ipv4=cidr_ipv4,
            source_security_group_id=destination_security_group_id,  # Reuse field
            description=description
        )
        
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        
        logger.info(f"Added egress rule {rule_id} to security group {group_id}")
        
        return rule
    
    async def revoke_rule(
        self,
        db: AsyncSession,
        rule_id: str,
        account_id: str
    ):
        """
        Revoke (delete) a security group rule.
        
        Args:
            db: Database session
            rule_id: Rule ID
            account_id: Account ID
        
        Raises:
            ResourceNotFoundError: Rule not found
        """
        # Get rule and verify ownership
        result = await db.execute(
            select(SecurityGroupRule)
            .join(SecurityGroup)
            .where(
                SecurityGroupRule.rule_id == rule_id,
                SecurityGroup.account_id == account_id
            )
        )
        rule = result.scalar_one_or_none()
        
        if not rule:
            raise ResourceNotFoundError(
                resource_type="SecurityGroupRule",
                resource_id=rule_id,
                message=f"Security group rule {rule_id} not found"
            )
        
        await db.delete(rule)
        await db.commit()
        
        logger.info(f"Revoked security group rule {rule_id}")
    
    async def get_rules_for_group(
        self,
        db: AsyncSession,
        group_id: str,
        account_id: str
    ) -> list[SecurityGroupRule]:
        """
        Get all rules for a security group.
        
        Args:
            db: Database session
            group_id: Security group ID
            account_id: Account ID
        
        Returns:
            List of SecurityGroupRule
        """
        result = await db.execute(
            select(SecurityGroupRule)
            .join(SecurityGroup)
            .where(
                SecurityGroupRule.group_id == group_id,
                SecurityGroup.account_id == account_id
            )
        )
        return list(result.scalars().all())

