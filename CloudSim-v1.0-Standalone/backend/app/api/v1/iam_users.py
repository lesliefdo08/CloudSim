"""
IAM User Management Routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.authorization import RequirePermission
from app.schemas.iam_auth import AuthenticatedUser
from app.schemas.iam_operations import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    ListUsersResponse
)
from app.schemas.common import SuccessResponse
from app.models.iam_user import User
from app.services.auth_service import AuthService
from app.core.resource_ids import generate_id, ResourceType
from app.utils.arn import build_arn
from app.core.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError


router = APIRouter(prefix="/users", tags=["IAM Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create IAM user",
    dependencies=[Depends(RequirePermission("iam:CreateUser"))]
)
async def create_user(
    request: CreateUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Create a new IAM user
    
    **Required Permission:** `iam:CreateUser`
    
    **Request:**
    ```json
    {
        "username": "alice",
        "password": "TempPassword123!",
        "console_access_enabled": true,
        "require_password_reset": true
    }
    ```
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/iam/users \\
      -H "Authorization: Bearer <token>" \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "TempPassword123!"}'
    ```
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(
            User.username == request.username,
            User.account_id == current_user.account_id
        )
    )
    if result.scalar_one_or_none():
        raise ResourceAlreadyExistsError(
            resource_type="User",
            resource_id=request.username,
            message=f"User '{request.username}' already exists"
        )
    
    # Generate user ID
    user_id = generate_id(ResourceType.USER)
    
    # Build ARN
    arn = build_arn(
        service="iam",
        resource_type="user",
        resource_id=request.username,
        region="",
        account_id=current_user.account_id
    )
    
    # Hash password if provided
    password_hash = None
    if request.password:
        password_hash = AuthService.hash_password(request.password)
    
    # Create user
    user = User(
        user_id=user_id,
        account_id=current_user.account_id,
        username=request.username,
        arn=arn,
        path=request.path,
        password_hash=password_hash,
        console_access_enabled=request.console_access_enabled,
        require_password_reset=request.require_password_reset,
        enabled=True
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get(
    "",
    response_model=ListUsersResponse,
    summary="List IAM users",
    dependencies=[Depends(RequirePermission("iam:ListUsers"))]
)
async def list_users(
    path_prefix: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ListUsersResponse:
    """
    List IAM users in account
    
    **Required Permission:** `iam:ListUsers`
    
    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/iam/users \\
      -H "Authorization: Bearer <token>"
    ```
    """
    query = select(User).where(User.account_id == current_user.account_id)
    
    if path_prefix:
        query = query.where(User.path.startswith(path_prefix))
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get users
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    users = result.scalars().all()
    
    return ListUsersResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total
    )


@router.get(
    "/{username}",
    response_model=UserResponse,
    summary="Get IAM user",
    dependencies=[Depends(RequirePermission("iam:GetUser"))]
)
async def get_user(
    username: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get IAM user by username
    
    **Required Permission:** `iam:GetUser`
    
    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/iam/users/alice \\
      -H "Authorization: Bearer <token>"
    ```
    """
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.account_id == current_user.account_id
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=username
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/{username}",
    response_model=UserResponse,
    summary="Update IAM user",
    dependencies=[Depends(RequirePermission("iam:UpdateUser"))]
)
async def update_user(
    username: str,
    request: UpdateUserRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Update IAM user
    
    **Required Permission:** `iam:UpdateUser`
    """
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.account_id == current_user.account_id
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=username
        )
    
    # Update fields
    if request.new_username:
        user.username = request.new_username
    if request.new_path:
        user.path = request.new_path
    if request.enabled is not None:
        user.enabled = request.enabled
    if request.console_access_enabled is not None:
        user.console_access_enabled = request.console_access_enabled
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete(
    "/{username}",
    response_model=SuccessResponse,
    summary="Delete IAM user",
    dependencies=[Depends(RequirePermission("iam:DeleteUser"))]
)
async def delete_user(
    username: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete IAM user
    
    **Required Permission:** `iam:DeleteUser`
    
    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/iam/users/alice \\
      -H "Authorization: Bearer <token>"
    ```
    """
    result = await db.execute(
        select(User).where(
            User.username == username,
            User.account_id == current_user.account_id
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise ResourceNotFoundError(
            resource_type="User",
            resource_id=username
        )
    
    await db.delete(user)
    await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"User '{username}' deleted successfully"
    )

