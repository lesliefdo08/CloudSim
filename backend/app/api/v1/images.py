"""
AMI API Routes

Endpoints for managing Amazon Machine Images (AMIs).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.core.database import get_db
from app.middleware.auth import get_current_account
from app.middleware.authorization import RequirePermission
from app.models.iam_account import Account
from app.models.ami import AMI
from app.services.ami_service import AMIService
from app.schemas.ami import (
    CreateImageRequest,
    AMIResponse,
    DescribeImagesResponse
)
from app.core.exceptions import ResourceNotFoundError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["AMIs"])


@router.post(
    "",
    response_model=AMIResponse,
    dependencies=[Depends(RequirePermission("ec2:CreateImage", "*"))]
)
async def create_image(
    request: CreateImageRequest,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Create AMI from running instance.
    
    Creates a machine image from the specified instance's Docker container.
    The instance must be in running or stopped state.
    
    Permissions: ec2:CreateImage
    """
    service = AMIService()
    
    ami = await service.create_image(
        db=db,
        instance_id=request.instance_id,
        account_id=current_account.account_id,
        name=request.name,
        description=request.description,
        tags=request.tags
    )
    
    return ami


@router.get(
    "",
    response_model=DescribeImagesResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeImages", "*"))]
)
async def describe_images(
    ami_ids: Optional[str] = Query(None, description="Comma-separated AMI IDs"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    List AMIs.
    
    Returns list of AMIs owned by the current account.
    Optionally filter by specific AMI IDs.
    
    Permissions: ec2:DescribeImages
    """
    service = AMIService()
    
    # Parse AMI IDs
    ami_id_list = None
    if ami_ids:
        ami_id_list = [aid.strip() for aid in ami_ids.split(",") if aid.strip()]
    
    # Get AMIs
    images = await service.describe_images(
        db=db,
        account_id=current_account.account_id,
        ami_ids=ami_id_list,
        limit=limit,
        offset=offset
    )
    
    # Count total
    query = select(func.count()).select_from(AMI).where(
        AMI.account_id == current_account.account_id
    )
    if ami_id_list:
        query = query.where(AMI.ami_id.in_(ami_id_list))
    
    result = await db.execute(query)
    total = result.scalar()
    
    return DescribeImagesResponse(images=images, total=total)


@router.get(
    "/{ami_id}",
    response_model=AMIResponse,
    dependencies=[Depends(RequirePermission("ec2:DescribeImages", "*"))]
)
async def get_image(
    ami_id: str,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Get AMI by ID.
    
    Returns details of a specific AMI.
    
    Permissions: ec2:DescribeImages
    """
    service = AMIService()
    
    ami = await service.get_image(
        db=db,
        ami_id=ami_id,
        account_id=current_account.account_id
    )
    
    return ami


@router.delete(
    "/{ami_id}",
    dependencies=[Depends(RequirePermission("ec2:DeregisterImage", "*"))]
)
async def deregister_image(
    ami_id: str,
    db: AsyncSession = Depends(get_db),
    current_account: Account = Depends(get_current_account)
):
    """
    Deregister (delete) AMI.
    
    Removes the AMI and its associated Docker image.
    This operation cannot be undone.
    
    Permissions: ec2:DeregisterImage
    """
    service = AMIService()
    
    await service.deregister_image(
        db=db,
        ami_id=ami_id,
        account_id=current_account.account_id
    )
    
    return {"message": f"AMI {ami_id} deregistered successfully"}

