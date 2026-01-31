"""
Authentication Middleware
JWT token validation and user context injection
"""

import logging
from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.iam_auth import AuthenticatedUser
from app.core.exceptions import AuthenticationError, InvalidCredentialsError
from app.models.iam_account import Account
from sqlalchemy import select


logger = logging.getLogger(__name__)


# Security scheme for FastAPI docs
security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> AuthenticatedUser:
    """
    Dependency to get current authenticated user
    
    Validates JWT token and returns user context
    
    Usage:
        @app.get("/instances")
        async def list_instances(user: AuthenticatedUser = Depends(get_current_user)):
            # user is authenticated
            user_id = user.user_id
    
    Raises:
        HTTPException: If token is invalid or missing
    """
    # Allow unauthenticated access to public endpoints
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"] or \
       request.url.path.startswith("/api/v1/auth/login") or \
       request.url.path.startswith("/api/v1/auth/access-key"):
        return AuthenticatedUser(
            user_id="anonymous",
            username="anonymous",
            account_id="000000000000",
            auth_method="none"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        token = credentials.credentials
        
        # Decode and verify JWT token
        payload = AuthService.decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise AuthenticationError(
                message="Invalid token type (expected access token)"
            )
        
        # Create authenticated user context
        user = AuthenticatedUser(
            user_id=payload["sub"],
            username=payload["username"],
            account_id=payload["account_id"],
            auth_method="password"
        )
        
        # Store in request state for later access
        request.state.user = user
        
        return user
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[AuthenticatedUser]:
    """
    Optional authentication dependency
    Returns user if authenticated, None otherwise
    
    Usage:
        @app.get("/public-endpoint")
        async def public_endpoint(user: Optional[AuthenticatedUser] = Depends(get_optional_user)):
            if user:
                # User is authenticated
                pass
            else:
                # Anonymous access
                pass
    """
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_permissions(*permissions: str):
    """
    Decorator to require specific permissions
    
    TODO: Implement IAM policy evaluation
    This is a placeholder for future authorization logic.
    
    Usage:
        @app.delete("/instances/{instance_id}")
        @require_permissions("ec2:TerminateInstances")
        async def terminate_instance(instance_id: str, user: dict = Depends(get_current_user)):
            pass
    """
    def decorator(func):
        # TODO: Implement permission checking
        # This would integrate with IAM policy evaluation
        return func
    return decorator


async def get_current_account(
    user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Account:
    """
    Dependency to get current account from authenticated user
    
    Usage:
        @app.get("/images")
        async def list_images(account: Account = Depends(get_current_account)):
            # account is the current AWS account
            pass
    
    Raises:
        HTTPException: If account not found
    """
    result = await db.execute(
        select(Account).where(Account.account_id == user.account_id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {user.account_id} not found"
        )
    
    return account
