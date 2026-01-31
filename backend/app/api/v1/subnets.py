"""
Subnet API Routes
IAM-protected Subnet management endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.authorization import RequirePermission
from app.schemas.iam_auth import AuthenticatedUser
from app.schemas.vpc import (
    CreateSubnetRequest,
    SubnetResponse,
    ListSubnetsResponse
)
from app.schemas.common import SuccessResponse
from app.services.subnet_service import SubnetService
from app.models.subnet import Subnet


router = APIRouter(prefix="/subnets", tags=["Subnets"])


@router.post(
    "",
    response_model=SubnetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subnet",
    dependencies=[Depends(RequirePermission("ec2:CreateSubnet"))]
)
async def create_subnet(
    request: CreateSubnetRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubnetResponse:
    """
    Create a new Subnet within VPC
    
    **Required Permission:** `ec2:CreateSubnet`
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/subnets \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "vpc_id": "vpc-abc123def456",
        "cidr_block": "10.0.1.0/24",
        "name": "public-subnet-1a",
        "availability_zone": "us-east-1a",
        "map_public_ip_on_launch": true
      }'
    ```
    """
    subnet_service = SubnetService()
    
    subnet = await subnet_service.create_subnet(
        db=db,
        vpc_id=request.vpc_id,
        account_id=current_user.account_id,
        cidr_block=request.cidr_block,
        name=request.name,
        availability_zone=request.availability_zone,
        map_public_ip_on_launch=request.map_public_ip_on_launch,
        tags=request.tags
    )
    
    return SubnetResponse.model_validate(subnet)


@router.get(
    "",
    response_model=ListSubnetsResponse,
    summary="List Subnets",
    dependencies=[Depends(RequirePermission("ec2:DescribeSubnets"))]
)
async def list_subnets(
    vpc_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ListSubnetsResponse:
    """
    List Subnets in account
    
    **Required Permission:** `ec2:DescribeSubnets`
    
    **Example:**
    ```bash
    # List all subnets
    curl http://localhost:8000/api/v1/subnets \\
      -H "Authorization: Bearer $TOKEN"
    
    # List subnets in specific VPC
    curl "http://localhost:8000/api/v1/subnets?vpc_id=vpc-abc123def456" \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    subnet_service = SubnetService()
    
    # Get subnets
    subnets = await subnet_service.list_subnets(
        db=db,
        account_id=current_user.account_id,
        vpc_id=vpc_id,
        limit=limit,
        offset=offset
    )
    
    # Get total count
    query = select(func.count()).select_from(Subnet).where(Subnet.account_id == current_user.account_id)
    if vpc_id:
        query = query.where(Subnet.vpc_id == vpc_id)
    
    result = await db.execute(query)
    total = result.scalar()
    
    return ListSubnetsResponse(
        subnets=[SubnetResponse.model_validate(subnet) for subnet in subnets],
        total=total
    )


@router.get(
    "/{subnet_id}",
    response_model=SubnetResponse,
    summary="Get Subnet",
    dependencies=[Depends(RequirePermission("ec2:DescribeSubnets"))]
)
async def get_subnet(
    subnet_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SubnetResponse:
    """
    Get Subnet by ID
    
    **Required Permission:** `ec2:DescribeSubnets`
    
    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/subnets/subnet-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    subnet_service = SubnetService()
    
    subnet = await subnet_service.get_subnet(
        db=db,
        subnet_id=subnet_id,
        account_id=current_user.account_id
    )
    
    return SubnetResponse.model_validate(subnet)


@router.delete(
    "/{subnet_id}",
    response_model=SuccessResponse,
    summary="Delete Subnet",
    dependencies=[Depends(RequirePermission("ec2:DeleteSubnet"))]
)
async def delete_subnet(
    subnet_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete Subnet
    
    **Required Permission:** `ec2:DeleteSubnet`
    
    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/subnets/subnet-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    subnet_service = SubnetService()
    
    await subnet_service.delete_subnet(
        db=db,
        subnet_id=subnet_id,
        account_id=current_user.account_id
    )
    
    return SuccessResponse(
        success=True,
        message=f"Subnet '{subnet_id}' deleted successfully"
    )

