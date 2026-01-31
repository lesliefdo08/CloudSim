"""
VPC API Routes
IAM-protected VPC management endpoints
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
    CreateVPCRequest,
    VPCResponse,
    ListVPCsResponse
)
from app.schemas.common import SuccessResponse
from app.services.vpc_service import VPCService
from app.models.vpc import VPC


router = APIRouter(prefix="/vpcs", tags=["VPC"])


@router.post(
    "",
    response_model=VPCResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create VPC",
    dependencies=[Depends(RequirePermission("ec2:CreateVpc"))]
)
async def create_vpc(
    request: CreateVPCRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> VPCResponse:
    """
    Create a new Virtual Private Cloud
    
    **Required Permission:** `ec2:CreateVpc`
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/vpcs \\
      -H "Authorization: Bearer $TOKEN" \\
      -H "Content-Type: application/json" \\
      -d '{
        "cidr_block": "10.0.0.0/16",
        "name": "production-vpc",
        "enable_dns_support": true,
        "enable_dns_hostnames": true
      }'
    ```
    """
    vpc_service = VPCService()
    
    vpc = await vpc_service.create_vpc(
        db=db,
        account_id=current_user.account_id,
        cidr_block=request.cidr_block,
        name=request.name,
        enable_dns_support=request.enable_dns_support,
        enable_dns_hostnames=request.enable_dns_hostnames,
        tags=request.tags
    )
    
    return VPCResponse.model_validate(vpc)


@router.get(
    "",
    response_model=ListVPCsResponse,
    summary="List VPCs",
    dependencies=[Depends(RequirePermission("ec2:DescribeVpcs"))]
)
async def list_vpcs(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ListVPCsResponse:
    """
    List VPCs in account
    
    **Required Permission:** `ec2:DescribeVpcs`
    
    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/vpcs \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    vpc_service = VPCService()
    
    # Get VPCs
    vpcs = await vpc_service.list_vpcs(
        db=db,
        account_id=current_user.account_id,
        limit=limit,
        offset=offset
    )
    
    # Get total count
    result = await db.execute(
        select(func.count()).select_from(VPC).where(VPC.account_id == current_user.account_id)
    )
    total = result.scalar()
    
    return ListVPCsResponse(
        vpcs=[VPCResponse.model_validate(vpc) for vpc in vpcs],
        total=total
    )


@router.get(
    "/{vpc_id}",
    response_model=VPCResponse,
    summary="Get VPC",
    dependencies=[Depends(RequirePermission("ec2:DescribeVpcs"))]
)
async def get_vpc(
    vpc_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> VPCResponse:
    """
    Get VPC by ID
    
    **Required Permission:** `ec2:DescribeVpcs`
    
    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/vpcs/vpc-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    vpc_service = VPCService()
    
    vpc = await vpc_service.get_vpc(
        db=db,
        vpc_id=vpc_id,
        account_id=current_user.account_id
    )
    
    return VPCResponse.model_validate(vpc)


@router.delete(
    "/{vpc_id}",
    response_model=SuccessResponse,
    summary="Delete VPC",
    dependencies=[Depends(RequirePermission("ec2:DeleteVpc"))]
)
async def delete_vpc(
    vpc_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete VPC and associated Docker network
    
    **Required Permission:** `ec2:DeleteVpc`
    
    **Note:** VPC must not have any subnets
    
    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/vpcs/vpc-abc123def456 \\
      -H "Authorization: Bearer $TOKEN"
    ```
    """
    vpc_service = VPCService()
    
    await vpc_service.delete_vpc(
        db=db,
        vpc_id=vpc_id,
        account_id=current_user.account_id
    )
    
    return SuccessResponse(
        success=True,
        message=f"VPC '{vpc_id}' deleted successfully"
    )

