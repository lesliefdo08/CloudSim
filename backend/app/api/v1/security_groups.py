"""
Security Group API Routes

IAM-protected routes for managing security groups and rules.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.middleware.authorization import RequirePermission
from app.middleware.auth import get_current_user
from app.models.iam_user import User
from app.models.security_group import SecurityGroup
from app.services.security_group_service import SecurityGroupService
from app.schemas.security_group import (
    CreateSecurityGroupRequest,
    AuthorizeSecurityGroupRuleRequest,
    SecurityGroupResponse,
    SecurityGroupRuleResponse,
    ListSecurityGroupsResponse
)
from app.schemas.common import SuccessResponse


router = APIRouter(prefix="/security-groups", tags=["Security Groups"])


@router.post(
    "",
    response_model=SecurityGroupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermission("ec2:CreateSecurityGroup"))]
)
async def create_security_group(
    request: CreateSecurityGroupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new security group.
    
    **Required Permission**: `ec2:CreateSecurityGroup`
    
    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/security-groups \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "vpc_id": "vpc-abc123def456",
        "group_name": "web-servers",
        "description": "Security group for web servers",
        "tags": {"Environment": "Production"}
      }'
    ```
    """
    service = SecurityGroupService()
    
    security_group = await service.create_security_group(
        db=db,
        vpc_id=request.vpc_id,
        account_id=current_user.account_id,
        group_name=request.group_name,
        description=request.description,
        tags=request.tags
    )
    
    # Load rules (empty for new group)
    await db.refresh(security_group, ["rules"])
    
    return SecurityGroupResponse.model_validate(security_group)


@router.get(
    "",
    response_model=ListSecurityGroupsResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeSecurityGroups"))]
)
async def list_security_groups(
    vpc_id: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List security groups.
    
    **Required Permission**: `ec2:DescribeSecurityGroups`
    
    **Example**:
    ```bash
    # List all security groups
    curl http://localhost:8000/api/v1/security-groups \\
      -H "Authorization: Bearer $TOKEN"
    
    # Filter by VPC
    curl "http://localhost:8000/api/v1/security-groups?vpc_id=vpc-abc123" \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    service = SecurityGroupService()
    
    security_groups = await service.list_security_groups(
        db=db,
        account_id=current_user.account_id,
        vpc_id=vpc_id,
        limit=limit,
        offset=offset
    )
    
    # Load rules for each security group
    for sg in security_groups:
        await db.refresh(sg, ["rules"])
    
    # Count total
    query = select(func.count()).select_from(SecurityGroup).where(
        SecurityGroup.account_id == current_user.account_id
    )
    if vpc_id:
        query = query.where(SecurityGroup.vpc_id == vpc_id)
    
    result = await db.execute(query)
    total = result.scalar_one()
    
    return ListSecurityGroupsResponse(
        security_groups=[SecurityGroupResponse.model_validate(sg) for sg in security_groups],
        total=total
    )


@router.get(
    "/{group_id}",
    response_model=SecurityGroupResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeSecurityGroups"))]
)
async def get_security_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get security group by ID.
    
    **Required Permission**: `ec2:DescribeSecurityGroups`
    
    **Example**:
    ```bash
    curl http://localhost:8000/api/v1/security-groups/sg-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    service = SecurityGroupService()
    
    security_group = await service.get_security_group(
        db=db,
        group_id=group_id,
        account_id=current_user.account_id
    )
    
    # Load rules
    await db.refresh(security_group, ["rules"])
    
    return SecurityGroupResponse.model_validate(security_group)


@router.delete(
    "/{group_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(RequirePermission("ec2:DeleteSecurityGroup"))]
)
async def delete_security_group(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a security group.
    
    **Required Permission**: `ec2:DeleteSecurityGroup`
    
    **Example**:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/security-groups/sg-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    service = SecurityGroupService()
    
    await service.delete_security_group(
        db=db,
        group_id=group_id,
        account_id=current_user.account_id
    )
    
    return SuccessResponse(message=f"Security group {group_id} deleted successfully")


@router.post(
    "/{group_id}/rules/ingress",
    response_model=SecurityGroupRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermission("ec2:AuthorizeSecurityGroupIngress"))]
)
async def authorize_ingress(
    group_id: str,
    request: AuthorizeSecurityGroupRuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add ingress (inbound) rule to security group.
    
    **Required Permission**: `ec2:AuthorizeSecurityGroupIngress`
    
    **Example**:
    ```bash
    # Allow SSH from anywhere
    curl -X POST http://localhost:8000/api/v1/security-groups/sg-abc123/rules/ingress \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "ip_protocol": "tcp",
        "from_port": 22,
        "to_port": 22,
        "cidr_ipv4": "0.0.0.0/0",
        "description": "Allow SSH from anywhere"
      }'
    
    # Allow HTTP from anywhere
    curl -X POST http://localhost:8000/api/v1/security-groups/sg-abc123/rules/ingress \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "ip_protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_ipv4": "0.0.0.0/0",
        "description": "Allow HTTP"
      }'
    
    # Allow all traffic from another security group
    curl -X POST http://localhost:8000/api/v1/security-groups/sg-abc123/rules/ingress \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "ip_protocol": "-1",
        "source_security_group_id": "sg-xyz789",
        "description": "Allow from app servers"
      }'
    ```
    """
    service = SecurityGroupService()
    
    rule = await service.authorize_ingress(
        db=db,
        group_id=group_id,
        account_id=current_user.account_id,
        ip_protocol=request.ip_protocol,
        from_port=request.from_port,
        to_port=request.to_port,
        cidr_ipv4=request.cidr_ipv4,
        source_security_group_id=request.source_security_group_id,
        description=request.description
    )
    
    return SecurityGroupRuleResponse.model_validate(rule)


@router.post(
    "/{group_id}/rules/egress",
    response_model=SecurityGroupRuleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermission("ec2:AuthorizeSecurityGroupEgress"))]
)
async def authorize_egress(
    group_id: str,
    request: AuthorizeSecurityGroupRuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add egress (outbound) rule to security group.
    
    **Required Permission**: `ec2:AuthorizeSecurityGroupEgress`
    
    **Example**:
    ```bash
    # Allow all outbound traffic
    curl -X POST http://localhost:8000/api/v1/security-groups/sg-abc123/rules/egress \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "ip_protocol": "-1",
        "cidr_ipv4": "0.0.0.0/0",
        "description": "Allow all outbound"
      }'
    ```
    """
    service = SecurityGroupService()
    
    rule = await service.authorize_egress(
        db=db,
        group_id=group_id,
        account_id=current_user.account_id,
        ip_protocol=request.ip_protocol,
        from_port=request.from_port,
        to_port=request.to_port,
        cidr_ipv4=request.cidr_ipv4,
        destination_security_group_id=request.source_security_group_id,  # Reuse field
        description=request.description
    )
    
    return SecurityGroupRuleResponse.model_validate(rule)


@router.delete(
    "/rules/{rule_id}",
    response_model=SuccessResponse,
    dependencies=[Depends(RequirePermission("ec2:RevokeSecurityGroupIngress"))]
)
async def revoke_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke (delete) a security group rule.
    
    **Required Permission**: `ec2:RevokeSecurityGroupIngress` or `ec2:RevokeSecurityGroupEgress`
    
    **Example**:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/security-groups/rules/sgr-abc123 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    service = SecurityGroupService()
    
    await service.revoke_rule(
        db=db,
        rule_id=rule_id,
        account_id=current_user.account_id
    )
    
    return SuccessResponse(message=f"Security group rule {rule_id} revoked successfully")

