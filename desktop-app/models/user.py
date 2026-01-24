"""
User Model - Authentication and user management
"""
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime
import hashlib
import secrets


@dataclass
class User:
    """User account model"""
    user_id: str
    username: str
    email: str
    password_hash: str
    created_at: datetime
    last_login: Optional[datetime] = None
    is_verified: bool = False
    is_active: bool = True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate unique user ID"""
        return f"user-{secrets.token_hex(8)}"
    
    @classmethod
    def create_new(cls, username: str, email: str, password: str) -> 'User':
        """Create new user"""
        return cls(
            user_id=cls.generate_user_id(),
            username=username,
            email=email,
            password_hash=cls.hash_password(password),
            created_at=datetime.now(),
            is_verified=False,
            is_active=True
        )
    
    def verify_password(self, password: str) -> bool:
        """Verify password matches hash"""
        return self.password_hash == self.hash_password(password)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['last_login'] = self.last_login.isoformat() if self.last_login else None
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Create from dictionary"""
        data = data.copy()
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_login' in data and data['last_login']:
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)
