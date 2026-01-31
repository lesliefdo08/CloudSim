"""
Authorization Middleware
Enforces IAM policies on API requests
"""

import logging
from typing import Optional, Callable
from functools import wraps

from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.schemas.iam_auth import AuthenticatedUser
from app.services.policy_service import PolicyEvaluator
from app.core.exceptions import UnauthorizedError


logger = logging.getLogger(__name__)


async def check_authorization(
    request: Request,
    action: str,
    resource: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Check if current user has permission to perform action on resource
    
    Args:
        request: FastAPI request
        action: IAM action (e.g., "ec2:StartInstances")
        resource: Resource ARN
        current_user: Authenticated user from get_current_user
        db: Database session
        
    Raises:
        HTTPException: 403 if access denied
    """
    # Skip authorization for anonymous users (public endpoints)
    if current_user.user_id == "anonymous":
        return
    
    # Evaluate policy
    decision = await PolicyEvaluator.evaluate(
        db=db,
        user_id=current_user.user_id,
        action=action,
        resource=resource
    )
    
    if not decision.is_allowed:
        logger.warning(
            f"Access denied for user {current_user.username}: {decision.reason}",
            extra={
                "user_id": current_user.user_id,
                "action": action,
                "resource": resource,
                "reason": decision.reason
            }
        )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "AccessDenied",
                "message": f"User '{current_user.username}' is not authorized to perform: {action}",
                "reason": decision.reason,
                "action": action,
                "resource": resource
            }
        )
    
    logger.info(
        f"Access granted for user {current_user.username}: {action} on {resource}",
        extra={
            "user_id": current_user.user_id,
            "action": action,
            "resource": resource
        }
    )


def require_permission(action: str, resource_fn: Optional[Callable] = None):
    """
    Decorator to enforce IAM permission on endpoint
    
    Usage:
        @require_permission("ec2:StartInstances", lambda kwargs: f"arn:aws:ec2:*:*:instance/{kwargs['instance_id']}")
        async def start_instance(instance_id: str, ...):
            ...
    
    Args:
        action: IAM action string
        resource_fn: Function to build resource ARN from endpoint kwargs
                    If None, uses "*" as resource
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            request: Optional[Request] = None
            current_user: Optional[AuthenticatedUser] = None
            db: Optional[AsyncSession] = None
            
            # Find dependencies in kwargs
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                elif isinstance(value, AuthenticatedUser):
                    current_user = value
                elif isinstance(value, AsyncSession):
                    db = value
            
            if not all([request, current_user, db]):
                raise RuntimeError("Missing required dependencies for authorization")
            
            # Build resource ARN
            if resource_fn:
                resource = resource_fn(kwargs)
            else:
                resource = "*"
            
            # Check authorization
            await check_authorization(
                request=request,
                action=action,
                resource=resource,
                current_user=current_user,
                db=db
            )
            
            # Execute endpoint
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class RequirePermission:
    """
    Dependency class for permission checking
    
    Usage:
        @router.post("/instances/{instance_id}/start")
        async def start_instance(
            instance_id: str,
            _: None = Depends(RequirePermission("ec2:StartInstances", lambda id: f"arn:aws:ec2:*:*:instance/{id}"))
        ):
            ...
    """
    
    def __init__(self, action: str, resource: str = "*"):
        """
        Initialize permission dependency
        
        Args:
            action: IAM action string
            resource: Resource ARN (can be dynamic)
        """
        self.action = action
        self.resource = resource
    
    async def __call__(
        self,
        request: Request,
        current_user: AuthenticatedUser = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> None:
        """Check authorization"""
        await check_authorization(
            request=request,
            action=self.action,
            resource=self.resource,
            current_user=current_user,
            db=db
        )
