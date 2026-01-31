"""
Authentication Routes
Login, token refresh, and access key authentication endpoints
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.iam_auth import (
    LoginRequest,
    TokenResponse,
    AccessKeyAuthRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    AuthenticatedUser,
    TokenInfo,
)
from app.schemas.common import SuccessResponse
from app.middleware.auth import get_current_user
from app.core.exceptions import InvalidCredentialsError


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with username and password",
    description="Authenticate with IAM username and password. Returns JWT access and refresh tokens."
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Password-based authentication
    
    **Request:**
    ```json
    {
        "username": "alice",
        "password": "SecurePassword123!",
        "account_id": "123456789012"
    }
    ```
    
    **Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": "AIDACKCEVSQ6C2EXAMPLE",
        "username": "alice",
        "account_id": "123456789012"
    }
    ```
    
    **Usage:**
    ```bash
    # Login
    curl -X POST http://localhost:8000/api/v1/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "SecurePassword123!"}'
    
    # Use access token
    curl http://localhost:8000/api/v1/ec2/instances \\
      -H "Authorization: Bearer <access_token>"
    ```
    """
    # Authenticate user
    user = await AuthService.authenticate_with_password(
        db=db,
        username=request.username,
        password=request.password,
        account_id=request.account_id
    )
    
    # Check if password reset is required
    if user.require_password_reset:
        raise InvalidCredentialsError(
            message="Password reset required. Please change your password before continuing."
        )
    
    # Create tokens
    access_token = AuthService.create_access_token(
        user_id=user.user_id,
        username=user.username,
        account_id=user.account_id
    )
    
    refresh_token = AuthService.create_refresh_token(
        user_id=user.user_id,
        username=user.username,
        account_id=user.account_id
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.user_id,
        username=user.username,
        account_id=user.account_id
    )


@router.post(
    "/access-key",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate with access key",
    description="Authenticate with AWS-style access key credentials. Returns JWT tokens."
)
async def authenticate_with_access_key(
    request: AccessKeyAuthRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Access key authentication (AWS CLI/SDK style)
    
    **Request:**
    ```json
    {
        "access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    }
    ```
    
    **Response:**
    Same as `/login` endpoint
    
    **Usage:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/auth/access-key \\
      -H "Content-Type: application/json" \\
      -d '{
        "access_key_id": "AKIAIOSFODNN7EXAMPLE",
        "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
      }'
    ```
    """
    # Authenticate with access key
    user, access_key = await AuthService.authenticate_with_access_key(
        db=db,
        access_key_id=request.access_key_id,
        secret_access_key=request.secret_access_key
    )
    
    # Create tokens
    access_token = AuthService.create_access_token(
        user_id=user.user_id,
        username=user.username,
        account_id=user.account_id
    )
    
    refresh_token = AuthService.create_refresh_token(
        user_id=user.user_id,
        username=user.username,
        account_id=user.account_id
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.user_id,
        username=user.username,
        account_id=user.account_id
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Use refresh token to obtain new access and refresh tokens."
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """
    Token refresh endpoint
    
    **Request:**
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Response:**
    Same as `/login` endpoint with new tokens
    
    **Usage:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/auth/refresh \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "<refresh_token>"}'
    ```
    """
    # Refresh tokens
    new_access_token, new_refresh_token = await AuthService.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token
    )
    
    # Decode token to get user info
    payload = AuthService.decode_token(new_access_token)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=payload["sub"],
        username=payload["username"],
        account_id=payload["account_id"]
    )


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Change password",
    description="Change current user's password (requires authentication)."
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SuccessResponse:
    """
    Change password for authenticated user
    
    **Request:**
    ```json
    {
        "old_password": "OldPassword123!",
        "new_password": "NewSecurePassword456!"
    }
    ```
    
    **Response:**
    ```json
    {
        "success": true,
        "message": "Password changed successfully"
    }
    ```
    
    **Usage:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/auth/change-password \\
      -H "Authorization: Bearer <access_token>" \\
      -H "Content-Type: application/json" \\
      -d '{
        "old_password": "OldPassword123!",
        "new_password": "NewSecurePassword456!"
      }'
    ```
    """
    await AuthService.change_password(
        db=db,
        user_id=current_user.user_id,
        old_password=request.old_password,
        new_password=request.new_password
    )
    
    return SuccessResponse(
        success=True,
        message="Password changed successfully"
    )


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get information about the currently authenticated user."
)
async def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> AuthenticatedUser:
    """
    Get current authenticated user information
    
    **Response:**
    ```json
    {
        "user_id": "AIDACKCEVSQ6C2EXAMPLE",
        "username": "alice",
        "account_id": "123456789012",
        "email": "alice@example.com",
        "auth_method": "password"
    }
    ```
    
    **Usage:**
    ```bash
    curl http://localhost:8000/api/v1/auth/me \\
      -H "Authorization: Bearer <access_token>"
    ```
    """
    return current_user


@router.get(
    "/token-info",
    response_model=TokenInfo,
    status_code=status.HTTP_200_OK,
    summary="Get token information",
    description="Decode and inspect the current access token."
)
async def get_token_info(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> TokenInfo:
    """
    Get information about current access token
    
    **Response:**
    ```json
    {
        "user_id": "AIDACKCEVSQ6C2EXAMPLE",
        "username": "alice",
        "account_id": "123456789012",
        "token_type": "access",
        "issued_at": "2026-01-31T12:00:00Z",
        "expires_at": "2026-01-31T13:00:00Z",
        "is_expired": false
    }
    ```
    
    **Usage:**
    ```bash
    curl http://localhost:8000/api/v1/auth/token-info \\
      -H "Authorization: Bearer <access_token>"
    ```
    """
    # This endpoint requires authentication, so token is already validated
    # We can return token info from current_user
    from datetime import datetime, timedelta
    
    return TokenInfo(
        user_id=current_user.user_id,
        username=current_user.username,
        account_id=current_user.account_id,
        token_type="access",
        issued_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES),
        is_expired=False
    )

