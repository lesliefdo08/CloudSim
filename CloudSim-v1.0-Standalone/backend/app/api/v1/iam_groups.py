"""
IAM Group Management Routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.authorization import RequirePermission
from app.schemas.iam_auth import AuthenticatedUser
from app.schemas.iam_operations import (
    CreateGroupRequest,
    GroupResponse,
    ListGroupsResponse,
    AddUserToGroupRequest
)
from app.schemas.common import SuccessResponse
from app.models.iam_group import Group
from app.models.iam_user import User
from app.core.resource_ids import generate_id, ResourceType
from app.utils.arn import build_arn
from app.core.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError


router = APIRouter(prefix="/groups", tags=["IAM Groups"])


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create IAM group",
    dependencies=[Depends(RequirePermission("iam:CreateGroup"))]
)
async def create_group(
    request: CreateGroupRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> GroupResponse:
    """
    Create a new IAM group
    
    **Required Permission:** `iam:CreateGroup`
    """
    # Check if group exists
    result = await db.execute(
        select(Group).where(
            Group.group_name == request.group_name,
            Group.account_id == current_user.account_id
        )
    )
    if result.scalar_one_or_none():
        raise ResourceAlreadyExistsError(
            resource_type="Group",
            resource_id=request.group_name
        )
    
    # Generate group ID
    group_id = generate_id(ResourceType.GROUP)
    
    # Build ARN
    arn = build_arn(
        service="iam",
        resource_type="group",
        resource_id=request.group_name,
        region="",
        account_id=current_user.account_id
    )
    
    # Create group
    group = Group(
        group_id=group_id,
        account_id=current_user.account_id,
        group_name=request.group_name,
        arn=arn,
        path=request.path
    )
    
    db.add(group)
    await db.commit()
    await db.refresh(group)
    
    return GroupResponse.model_validate(group)


@router.get(
    "",
    response_model=ListGroupsResponse,
    summary="List IAM groups",
    dependencies=[Depends(RequirePermission("iam:ListGroups"))]
)
async def list_groups(
    path_prefix: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ListGroupsResponse:
    """
    List IAM groups
    
    **Required Permission:** `iam:ListGroups`
    """
    query = select(Group).where(Group.account_id == current_user.account_id)
    
    if path_prefix:
        query = query.where(Group.path.startswith(path_prefix))
    
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get groups
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    groups = result.scalars().all()
    
    return ListGroupsResponse(
        groups=[GroupResponse.model_validate(g) for g in groups],
        total=total
    )


@router.post(
    "/{group_name}/users",
    response_model=SuccessResponse,
    summary="Add user to group",
    dependencies=[Depends(RequirePermission("iam:AddUserToGroup"))]
)
async def add_user_to_group(
    group_name: str,
    username: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Add user to group
    
    **Required Permission:** `iam:AddUserToGroup`
    """
    # Get group
    result = await db.execute(
        select(Group).where(
            Group.group_name == group_name,
            Group.account_id == current_user.account_id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise ResourceNotFoundError(resource_type="Group", resource_id=group_name)
    
    # Get user
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.account_id == current_user.account_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(resource_type="User", resource_id=username)
    
    # Add user to group
    if user not in group.users:
        group.users.append(user)
        await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"User '{username}' added to group '{group_name}'"
    )


@router.delete(
    "/{group_name}/users/{username}",
    response_model=SuccessResponse,
    summary="Remove user from group",
    dependencies=[Depends(RequirePermission("iam:RemoveUserFromGroup"))]
)
async def remove_user_from_group(
    group_name: str,
    username: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Remove user from group
    
    **Required Permission:** `iam:RemoveUserFromGroup`
    """
    # Get group
    result = await db.execute(
        select(Group).where(
            Group.group_name == group_name,
            Group.account_id == current_user.account_id
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise ResourceNotFoundError(resource_type="Group", resource_id=group_name)
    
    # Get user
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.account_id == current_user.account_id
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise ResourceNotFoundError(resource_type="User", resource_id=username)
    
    # Remove user from group
    if user in group.users:
        group.users.remove(user)
        await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"User '{username}' removed from group '{group_name}'"
    )


@router.delete(
    "/{group_name}",
    response_model=SuccessResponse,
    summary="Delete IAM group",
    dependencies=[Depends(RequirePermission("iam:DeleteGroup"))]
)
async def delete_group(
    group_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete IAM group
    
    **Required Permission:** `iam:DeleteGroup`
    """
    result = await db.execute(
        select(Group).where(
            Group.group_name == group_name,
            Group.account_id == current_user.account_id
        )
    )
    group = result.scalar_one_or_none()
    
    if not group:
        raise ResourceNotFoundError(resource_type="Group", resource_id=group_name)
    
    await db.delete(group)
    await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Group '{group_name}' deleted successfully"
    )

