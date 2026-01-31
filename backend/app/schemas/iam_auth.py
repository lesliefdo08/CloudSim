"""
IAM Authentication Schemas
Request/response models for authentication operations
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Password-based Authentication (Console Login)
# ============================================================================

class LoginRequest(BaseModel):
    """Request for password-based login"""
    
    username: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="IAM username"
    )
    
    password: str = Field(
        ...,
        min_length=1,
        description="User password"
    )
    
    account_id: Optional[str] = Field(
        None,
        description="Account ID (optional, can be derived from username)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "alice",
                "password": "SecurePassword123!",
                "account_id": "123456789012"
            }
        }
    )


class TokenResponse(BaseModel):
    """JWT token response"""
    
    access_token: str = Field(
        ...,
        description="JWT access token for API requests"
    )
    
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens"
    )
    
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    
    expires_in: int = Field(
        ...,
        description="Access token expiration time in seconds"
    )
    
    user_id: str = Field(
        ...,
        description="User ID"
    )
    
    username: str = Field(
        ...,
        description="Username"
    )
    
    account_id: str = Field(
        ...,
        description="Account ID"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user_id": "AIDACKCEVSQ6C2EXAMPLE",
                "username": "alice",
                "account_id": "123456789012"
            }
        }
    )


# ============================================================================
# Access Key Authentication (AWS CLI/SDK)
# ============================================================================

class AccessKeyAuthRequest(BaseModel):
    """Request for access key authentication"""
    
    access_key_id: str = Field(
        ...,
        min_length=16,
        max_length=128,
        description="Access Key ID (AKIA...)"
    )
    
    secret_access_key: str = Field(
        ...,
        min_length=16,
        description="Secret Access Key"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_key_id": "AKIAIOSFODNN7EXAMPLE",
                "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            }
        }
    )


# ============================================================================
# Token Refresh
# ============================================================================

class RefreshTokenRequest(BaseModel):
    """Request to refresh access token"""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


# ============================================================================
# User Context (for authenticated requests)
# ============================================================================

class AuthenticatedUser(BaseModel):
    """
    Authenticated user context
    Attached to request.state.user by auth middleware
    """
    
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    account_id: str = Field(..., description="Account ID")
    email: Optional[str] = Field(None, description="User email")
    auth_method: str = Field(..., description="Authentication method: password, access_key")
    
    # For access key auth
    access_key_id: Optional[str] = Field(None, description="Access Key ID used (if access_key auth)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "AIDACKCEVSQ6C2EXAMPLE",
                "username": "alice",
                "account_id": "123456789012",
                "email": "alice@example.com",
                "auth_method": "password"
            }
        }
    )


# ============================================================================
# Password Management
# ============================================================================

class ChangePasswordRequest(BaseModel):
    """Request to change password"""
    
    old_password: str = Field(
        ...,
        min_length=1,
        description="Current password"
    )
    
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 characters)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "old_password": "OldPassword123!",
                "new_password": "NewSecurePassword456!"
            }
        }
    )


class ResetPasswordRequest(BaseModel):
    """Request to reset password (admin operation)"""
    
    username: str = Field(
        ...,
        description="Username to reset password for"
    )
    
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password"
    )
    
    require_password_reset: bool = Field(
        default=True,
        description="Require password reset on next login"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "alice",
                "new_password": "TemporaryPassword123!",
                "require_password_reset": True
            }
        }
    )


# ============================================================================
# Token Info
# ============================================================================

class TokenInfo(BaseModel):
    """Information about a decoded token"""
    
    user_id: str
    username: str
    account_id: str
    token_type: str = Field(..., description="Token type: access or refresh")
    issued_at: datetime
    expires_at: datetime
    is_expired: bool
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "AIDACKCEVSQ6C2EXAMPLE",
                "username": "alice",
                "account_id": "123456789012",
                "token_type": "access",
                "issued_at": "2026-01-31T12:00:00Z",
                "expires_at": "2026-01-31T13:00:00Z",
                "is_expired": False
            }
        }
    )
