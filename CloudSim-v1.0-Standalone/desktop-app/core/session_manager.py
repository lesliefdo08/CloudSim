"""
Session Manager - Track active user and manage session state

*** SINGLE NAMESPACE MODE ***
Per-user data directories disabled. All data stored in shared local storage.
This is temporary for UI and feature stabilization.
"""
from typing import Optional
from pathlib import Path
from models.user import User


class SessionManager:
    """Manage user sessions - data isolation disabled for single namespace mode"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._current_user: Optional[User] = None
        # Per-user directories disabled - using shared storage
        # self._user_data_root = Path("data/users")
        # self._user_data_root.mkdir(parents=True, exist_ok=True)
        self._initialized = True
    
    def login(self, user: User):
        """Set current logged-in user"""
        self._current_user = user
        # Per-user directory creation disabled
        # self._ensure_user_directories()
    
    def logout(self):
        """Clear current user session"""
        self._current_user = None
    
    def get_current_user(self) -> Optional[User]:
        """Get currently logged-in user"""
        return self._current_user
    
    def is_authenticated(self) -> bool:
        """Check if user is logged in"""
        return self._current_user is not None
    
    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return self._current_user.user_id if self._current_user else None
    
    def get_username(self) -> Optional[str]:
        """Get current username"""
        return self._current_user.username if self._current_user else None
    
    def get_user_email(self) -> Optional[str]:
        """Get current user email"""
        return self._current_user.email if self._current_user else None
    
    # Per-user directory methods disabled - using shared storage
    # def _ensure_user_directories(self):
    #     """Create user-specific data directories - DISABLED"""
    #     pass
    
    # def get_user_data_dir(self) -> Optional[Path]:
    #     """Get current user's data directory - DISABLED, returns shared data dir"""
    #     return Path("data")
    
    # def get_user_service_dir(self, service: str) -> Optional[Path]:
    #     """Get directory for specific service data - DISABLED, returns shared service dir"""
    #     return Path(f"data/{service}")


# Global session manager instance
session_manager = SessionManager()
