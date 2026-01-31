"""
Authentication Service
Handles password verification, JWT tokens, and access key authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    ResourceNotFoundError,
)
from app.models.iam_user import User
from app.models.iam_access_key import AccessKey
from app.schemas.iam_auth import AuthenticatedUser, TokenInfo


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service for CloudSim IAM
    
    Provides:
    - Password verification (bcrypt)
    - JWT token creation (access + refresh)
    - JWT token verification
    - Access key authentication
    - Token refresh logic
    """
    
    # Token expiration times
    ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt
        
        Args:
            password: Plain text password
            
        Returns:
            Bcrypt hash
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Bcrypt hash
            
        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(
        user_id: str,
        username: str,
        account_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token
        
        Args:
            user_id: User ID
            username: Username
            account_id: Account ID
            expires_delta: Custom expiration time (optional)
            
        Returns:
            JWT access token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=AuthService.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,
            "username": username,
            "account_id": account_id,
            "type": "access",
            "iat": datetime.utcnow(),
            "exp": expire,
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        username: str,
        account_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT refresh token
        
        Args:
            user_id: User ID
            username: Username
            account_id: Account ID
            expires_delta: Custom expiration time (optional)
            
        Returns:
            JWT refresh token string
        """
        if expires_delta is None:
            expires_delta = timedelta(days=AuthService.REFRESH_TOKEN_EXPIRE_DAYS)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,
            "username": username,
            "account_id": account_id,
            "type": "refresh",
            "iat": datetime.utcnow(),
            "exp": expire,
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and verify JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Token payload dictionary
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(
                message="Invalid or expired token",
                details={"error": str(e)}
            )
    
    @staticmethod
    def get_token_info(token: str) -> TokenInfo:
        """
        Get information about a token
        
        Args:
            token: JWT token string
            
        Returns:
            TokenInfo object
        """
        payload = AuthService.decode_token(token)
        
        issued_at = datetime.fromtimestamp(payload["iat"])
        expires_at = datetime.fromtimestamp(payload["exp"])
        is_expired = datetime.utcnow() > expires_at
        
        return TokenInfo(
            user_id=payload["sub"],
            username=payload["username"],
            account_id=payload["account_id"],
            token_type=payload["type"],
            issued_at=issued_at,
            expires_at=expires_at,
            is_expired=is_expired
        )
    
    @staticmethod
    async def authenticate_with_password(
        db: AsyncSession,
        username: str,
        password: str,
        account_id: Optional[str] = None
    ) -> User:
        """
        Authenticate user with username and password
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            account_id: Account ID (optional)
            
        Returns:
            Authenticated User object
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            ResourceNotFoundError: If user not found
        """
        # Build query
        query = select(User).where(User.username == username)
        
        if account_id:
            query = query.where(User.account_id == account_id)
        
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ResourceNotFoundError(
                resource_type="User",
                resource_id=username,
                message=f"User '{username}' not found"
            )
        
        # Check if user is enabled
        if not user.enabled:
            raise InvalidCredentialsError(
                message="User account is disabled"
            )
        
        # Check if console access is enabled
        if not user.console_access_enabled:
            raise InvalidCredentialsError(
                message="Console access is disabled for this user"
            )
        
        # Verify password
        if not user.password_hash:
            raise InvalidCredentialsError(
                message="Password authentication not configured for this user"
            )
        
        if not AuthService.verify_password(password, user.password_hash):
            raise InvalidCredentialsError(
                message="Invalid username or password"
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        await db.commit()
        
        return user
    
    @staticmethod
    async def authenticate_with_access_key(
        db: AsyncSession,
        access_key_id: str,
        secret_access_key: str
    ) -> tuple[User, AccessKey]:
        """
        Authenticate user with access key credentials
        
        Args:
            db: Database session
            access_key_id: Access Key ID (AKIA...)
            secret_access_key: Secret Access Key
            
        Returns:
            Tuple of (User, AccessKey)
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            ResourceNotFoundError: If access key not found
        """
        # Find access key
        result = await db.execute(
            select(AccessKey).where(AccessKey.access_key_id == access_key_id)
        )
        access_key = result.scalar_one_or_none()
        
        if not access_key:
            raise ResourceNotFoundError(
                resource_type="AccessKey",
                resource_id=access_key_id,
                message=f"Access key '{access_key_id}' not found"
            )
        
        # Check if access key is active
        if access_key.status != "Active":
            raise InvalidCredentialsError(
                message="Access key is not active"
            )
        
        # Verify secret access key
        if not AuthService.verify_password(secret_access_key, access_key.secret_access_key_hash):
            raise InvalidCredentialsError(
                message="Invalid access key credentials"
            )
        
        # Get user
        result = await db.execute(
            select(User).where(User.user_id == access_key.user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ResourceNotFoundError(
                resource_type="User",
                resource_id=access_key.user_id,
                message="User associated with access key not found"
            )
        
        # Check if user is enabled
        if not user.enabled:
            raise InvalidCredentialsError(
                message="User account is disabled"
            )
        
        # Update last used
        access_key.last_used = datetime.utcnow()
        user.last_activity = datetime.utcnow()
        await db.commit()
        
        return user, access_key
    
    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str
    ) -> tuple[str, str]:
        """
        Refresh access token using refresh token
        
        Args:
            db: Database session
            refresh_token: Valid refresh token
            
        Returns:
            Tuple of (new_access_token, new_refresh_token)
            
        Raises:
            AuthenticationError: If refresh token is invalid
        """
        # Decode refresh token
        payload = AuthService.decode_token(refresh_token)
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise AuthenticationError(
                message="Invalid token type (expected refresh token)"
            )
        
        # Verify user still exists and is active
        user_id = payload["sub"]
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.enabled:
            raise AuthenticationError(
                message="User not found or disabled"
            )
        
        # Create new tokens
        new_access_token = AuthService.create_access_token(
            user_id=user.user_id,
            username=user.username,
            account_id=user.account_id
        )
        
        new_refresh_token = AuthService.create_refresh_token(
            user_id=user.user_id,
            username=user.username,
            account_id=user.account_id
        )
        
        return new_access_token, new_refresh_token
    
    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> None:
        """
        Change user password
        
        Args:
            db: Database session
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Raises:
            ResourceNotFoundError: If user not found
            InvalidCredentialsError: If old password is incorrect
        """
        result = await db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise ResourceNotFoundError(
                resource_type="User",
                resource_id=user_id
            )
        
        # Verify old password
        if not user.password_hash or not AuthService.verify_password(old_password, user.password_hash):
            raise InvalidCredentialsError(
                message="Current password is incorrect"
            )
        
        # Update password
        user.password_hash = AuthService.hash_password(new_password)
        user.password_last_changed = datetime.utcnow()
        user.require_password_reset = False
        
        await db.commit()

