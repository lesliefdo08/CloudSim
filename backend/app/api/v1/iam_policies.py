"""
IAM Policy Management Routes
"""

import json
from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.authorization import RequirePermission
from app.schemas.iam_auth import AuthenticatedUser
from app.schemas.iam_operations import (
    CreatePolicyRequest,
    PolicyResponse,
    ListPoliciesResponse,
    AttachPolicyRequest,
    DetachPolicyRequest
)
from app.schemas.common import SuccessResponse
from app.schemas.iam_policy import PolicyDocument
from app.models.iam_policy import Policy
from app.models.iam_user import User
from app.models.iam_group import Group
from app.core.resource_ids import generate_id, ResourceType
from app.utils.arn import build_arn
from app.core.exceptions import ResourceAlreadyExistsError, ResourceNotFoundError, ValidationError


router = APIRouter(prefix="/policies", tags=["IAM Policies"])


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create IAM policy",
    dependencies=[Depends(RequirePermission("iam:CreatePolicy"))]
)
async def create_policy(
    request: CreatePolicyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> PolicyResponse:
    """
    Create a new IAM policy
    
    **Required Permission:** `iam:CreatePolicy`
    """
    # Validate policy document
    try:
        policy_doc = PolicyDocument(**request.policy_document)
    except Exception as e:
        raise ValidationError(message=f"Invalid policy document: {str(e)}")
    
    # Check if policy exists
    result = await db.execute(
        select(Policy).where(
            Policy.policy_name == request.policy_name,
            Policy.account_id == current_user.account_id
        )
    )
    if result.scalar_one_or_none():
        raise ResourceAlreadyExistsError(
            resource_type="Policy",
            resource_id=request.policy_name
        )
    
    # Generate policy ID
    policy_id = generate_id(ResourceType.POLICY)
    
    # Build ARN
    arn = build_arn(
        service="iam",
        resource_type="policy",
        resource_id=request.policy_name,
        region="",
        account_id=current_user.account_id
    )
    
    # Create policy
    policy = Policy(
        policy_id=policy_id,
        account_id=current_user.account_id,
        policy_name=request.policy_name,
        arn=arn,
        path=request.path,
        description=request.description,
        policy_document=json.dumps(request.policy_document),
        is_aws_managed=False,
        version_id="v1",
        is_default_version=True,
        attachment_count=0
    )
    
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    
    return PolicyResponse.model_validate(policy)


@router.get(
    "",
    response_model=ListPoliciesResponse,
    summary="List IAM policies",
    dependencies=[Depends(RequirePermission("iam:ListPolicies"))]
)
async def list_policies(
    scope: Optional[str] = Query("Local", regex="^(All|AWS|Local)$"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ListPoliciesResponse:
    """
    List IAM policies
    
    **Required Permission:** `iam:ListPolicies`
    
    **Scope:**
    - `All`: All policies (AWS-managed + customer-managed)
    - `AWS`: Only AWS-managed policies
    - `Local`: Only customer-managed policies (default)
    """
    query = select(Policy)
    
    if scope == "AWS":
        query = query.where(Policy.is_aws_managed == True)
    elif scope == "Local":
        query = query.where(
            Policy.account_id == current_user.account_id,
            Policy.is_aws_managed == False
        )
    else:  # All
        query = query.where(
            (Policy.account_id == current_user.account_id) |
            (Policy.is_aws_managed == True)
        )
    
    # Get total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get policies
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    policies = result.scalars().all()
    
    return ListPoliciesResponse(
        policies=[PolicyResponse.model_validate(p) for p in policies],
        total=total
    )


@router.post(
    "/attach/user/{username}",
    response_model=SuccessResponse,
    summary="Attach policy to user",
    dependencies=[Depends(RequirePermission("iam:AttachUserPolicy"))]
)
async def attach_user_policy(
    username: str,
    request: AttachPolicyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Attach policy to user
    
    **Required Permission:** `iam:AttachUserPolicy`
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
    
    # Get policy
    result = await db.execute(
        select(Policy).where(Policy.arn == request.policy_arn)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise ResourceNotFoundError(resource_type="Policy", resource_id=request.policy_arn)
    
    # Attach policy
    if policy not in user.attached_policies:
        user.attached_policies.append(policy)
        policy.attachment_count += 1
        await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Policy attached to user '{username}'"
    )


@router.post(
    "/detach/user/{username}",
    response_model=SuccessResponse,
    summary="Detach policy from user",
    dependencies=[Depends(RequirePermission("iam:DetachUserPolicy"))]
)
async def detach_user_policy(
    username: str,
    request: DetachPolicyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Detach policy from user
    
    **Required Permission:** `iam:DetachUserPolicy`
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
    
    # Get policy
    result = await db.execute(
        select(Policy).where(Policy.arn == request.policy_arn)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise ResourceNotFoundError(resource_type="Policy", resource_id=request.policy_arn)
    
    # Detach policy
    if policy in user.attached_policies:
        user.attached_policies.remove(policy)
        policy.attachment_count -= 1
        await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Policy detached from user '{username}'"
    )


@router.post(
    "/attach/group/{group_name}",
    response_model=SuccessResponse,
    summary="Attach policy to group",
    dependencies=[Depends(RequirePermission("iam:AttachGroupPolicy"))]
)
async def attach_group_policy(
    group_name: str,
    request: AttachPolicyRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Attach policy to group
    
    **Required Permission:** `iam:AttachGroupPolicy`
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
    
    # Get policy
    result = await db.execute(
        select(Policy).where(Policy.arn == request.policy_arn)
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise ResourceNotFoundError(resource_type="Policy", resource_id=request.policy_arn)
    
    # Attach policy
    if policy not in group.attached_policies:
        group.attached_policies.append(policy)
        policy.attachment_count += 1
        await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Policy attached to group '{group_name}'"
    )


@router.delete(
    "/{policy_name}",
    response_model=SuccessResponse,
    summary="Delete IAM policy",
    dependencies=[Depends(RequirePermission("iam:DeletePolicy"))]
)
async def delete_policy(
    policy_name: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Delete IAM policy
    
    **Required Permission:** `iam:DeletePolicy`
    """
    result = await db.execute(
        select(Policy).where(
            Policy.policy_name == policy_name,
            Policy.account_id == current_user.account_id
        )
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        raise ResourceNotFoundError(resource_type="Policy", resource_id=policy_name)
    
    if policy.attachment_count > 0:
        raise ValidationError(
            message=f"Cannot delete policy '{policy_name}' because it is attached to {policy.attachment_count} entities"
        )
    
    await db.delete(policy)
    await db.commit()
    
    return SuccessResponse(
        success=True,
        message=f"Policy '{policy_name}' deleted successfully"
    )

