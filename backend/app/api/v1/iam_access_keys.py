"""
IAM Access Key Management Routes
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.authorization import RequirePermission
from app.schemas.iam_auth import AuthenticatedUser
from app.schemas.iam_operations import (
    CreateAccessKeyRequest,
    AccessKeyResponse,
    ListAccessKeysResponse
)
from app.schemas.common import SuccessResponse
from app.models.iam_user import User
from app.models.iam_access_key import AccessKey
from app.services.auth_service import AuthService
from app.core.resource_ids import generate_access_key
from app.core.exceptions import ResourceNotFoundError, LimitExceededError
import secrets


router = APIRouter(prefix="/access-keys", tags=["IAM Access Keys"])


@router.post(
    "",
    response_model=AccessKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create access key",
    dependencies=[Depends(RequirePermission("iam:CreateAccessKey"))]
)
async def create_access_key(
    username: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AccessKeyResponse:
    """
    Create access key for user
    
    **Required Permission:** `iam:CreateAccessKey`
    
    **Note:** Users can have maximum 2 active access keys (for rotation)
    """
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
    
    # Check limit (max 2 access keys per user)
    result = await db.execute(
        select(AccessKey).where(
            AccessKey.user_id == user.user_id,
            AccessKey.status == "Active"
        )
    )
    active_keys = result.scalars().all()
    
    if len(active_keys) >= 2:
        raise LimitExceededError(
            resource_type="AccessKey",
            limit=2,
            message="User can have maximum 2 active access keys"
        )
    
    # Generate access key ID and secret
    access_key_id = generate_access_key()
    secret_access_key = secrets.token_urlsafe(32)  # 40+ characters
    
    # Hash secret
    secret_hash = AuthService.hash_password(secret_access_key)
    
    # Create access key
    access_key = AccessKey(
        access_key_id=access_key_id,
        user_id=user.user_id,
        secret_access_key_hash=secret_hash,
        status="Active"
    )
    
    db.add(access_key)
    await db.commit()
    await db.refresh(access_key)
    
    # Return with secret (only shown once)
    response = AccessKeyResponse.model_validate(access_key)
    response.secret_access_key = secret_access_key
    
    return response


@router.get(
    "",
    response_model=ListAccessKeysResponse,
    summary="List access keys",
    dependencies=[Depends(RequirePermission("iam:ListAccessKeys"))]
)
async def list_access_keys(
    username: str = Query(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ListAccessKeysResponse:
    """
    List access keys for user
    
    **Required Permission:** `iam:ListAccessKeys`
    """
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
    
    # Get access keys
    result = await db.execute(
        select(AccessKey).where(AccessKey.user_id == user.user_id)
    )
    keys = result.scalars().all()
    
    return ListAccessKeysResponse(
        access_keys=[AccessKeyResponse.model_validate(k) for k in keys],
        total=len(keys)
    )


@router.put(
    "/{access_key_id}/status",
    response_model=SuccessResponse,
    summary="Update access key status",
    dependencies=[Depends(RequirePermission("iam:UpdateAccessKey"))]
)
async def update_access_key_status(
    access_key_id: str,
    status: str = Query(..., regex="^(Active|Inactive)$"),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Update access key status (Active/Inactive)
    
    **Required Permission:** `iam:UpdateAccessKey`
    """
    # Get access key
    result = await db.execute(
        select(AccessKey).where(AccessKey.access_key_id == access_key_id)
    )
    access_key = result.scalar_one_or_none()
    if not access_key:
        raise ResourceNotFoundError(resource_type="AccessKey", resource_id=access_key_id)
    
    # Verify ownership
    result = await db.execute(
        select(User).where(
            User.user_id == access_key.user_id,
            User.account_id == current_user.account_id
        )
    )
    if not result.scalar_one_or_none():
        raise ResourceNotFoundError(resource_type="AccessKey", resource_id=access_key_id)
    
    # Update status
    access_key.status = status
    await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Access key status updated to {status}"
    )


@router.delete(
    "/{access_key_id}",
    response_model=SuccessResponse,
    summary="Delete access key",
    dependencies=[Depends(RequirePermission("iam:DeleteAccessKey"))]
)
async def delete_access_key(
    access_key_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete access key
    
    **Required Permission:** `iam:DeleteAccessKey`
    """
    # Get access key
    result = await db.execute(
        select(AccessKey).where(AccessKey.access_key_id == access_key_id)
    )
    access_key = result.scalar_one_or_none()
    if not access_key:
        raise ResourceNotFoundError(resource_type="AccessKey", resource_id=access_key_id)
    
    # Verify ownership
    result = await db.execute(
        select(User).where(
            User.user_id == access_key.user_id,
            User.account_id == current_user.account_id
        )
    )
    if not result.scalar_one_or_none():
        raise ResourceNotFoundError(resource_type="AccessKey", resource_id=access_key_id)
    
    await db.delete(access_key)
    await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Access key '{access_key_id}' deleted successfully"
    )

