"""
Configuration management for CloudSim application.
Handles email settings and other configuration options.
"""

import os
from pathlib import Path
from typing import Optional


class EmailConfig:
    """Email service configuration."""
    
    # SMTP Configuration
    SMTP_SERVER: str = os.getenv("CLOUDSIM_SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("CLOUDSIM_SMTP_PORT", "587"))
    SMTP_USE_TLS: bool = os.getenv("CLOUDSIM_SMTP_USE_TLS", "True").lower() == "true"
    
    # Email Credentials
    EMAIL_SENDER: str = os.getenv("CLOUDSIM_EMAIL_SENDER", "")
    EMAIL_PASSWORD: str = os.getenv("CLOUDSIM_EMAIL_PASSWORD", "")
    EMAIL_SENDER_NAME: str = os.getenv("CLOUDSIM_EMAIL_SENDER_NAME", "CloudSim Console")
    
    # Email Settings
    EMAIL_ENABLED: bool = os.getenv("CLOUDSIM_EMAIL_ENABLED", "False").lower() == "true"
    EMAIL_TEST_MODE: bool = os.getenv("CLOUDSIM_EMAIL_TEST_MODE", "True").lower() == "true"
    
    # Rate Limiting
    OTP_MAX_REQUESTS: int = int(os.getenv("CLOUDSIM_OTP_MAX_REQUESTS", "3"))
    OTP_RATE_LIMIT_WINDOW: int = int(os.getenv("CLOUDSIM_OTP_RATE_LIMIT_WINDOW", "300"))  # 5 minutes
    OTP_EXPIRY_MINUTES: int = int(os.getenv("CLOUDSIM_OTP_EXPIRY_MINUTES", "10"))
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if email service is properly configured."""
        return bool(cls.EMAIL_SENDER and cls.EMAIL_PASSWORD and cls.EMAIL_ENABLED)
    
    @classmethod
    def get_smtp_config(cls) -> dict:
        """Get SMTP configuration dictionary."""
        return {
            "server": cls.SMTP_SERVER,
            "port": cls.SMTP_PORT,
            "use_tls": cls.SMTP_USE_TLS,
            "sender": cls.EMAIL_SENDER,
            "password": cls.EMAIL_PASSWORD,
            "sender_name": cls.EMAIL_SENDER_NAME,
        }


class AppConfig:
    """General application configuration."""
    
    # Application Info
    APP_NAME: str = "CloudSim Console"
    APP_VERSION: str = "1.0.0"
    
    # Data Directories - Single shared namespace (not per-user)
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    # USERS_DIR removed - using shared local storage for UI stabilization
    
    # Shared storage paths
    INSTANCES_FILE: Path = DATA_DIR / "instances.json"
    VOLUMES_FILE: Path = DATA_DIR / "volumes.json"
    BUCKETS_DIR: Path = DATA_DIR / "buckets"
    DATABASES_DIR: Path = DATA_DIR / "databases"
    FUNCTIONS_DIR: Path = DATA_DIR / "functions"
    
    # Auth files (still in data root)
    USERS_FILE: Path = DATA_DIR / "users.json"
    OTPS_FILE: Path = DATA_DIR / "otps.json"
    RATE_LIMITS_FILE: Path = DATA_DIR / "rate_limits.json"
    
    # Security
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("CLOUDSIM_MAX_LOGIN_ATTEMPTS", "5"))
    ACCOUNT_LOCKOUT_MINUTES: int = int(os.getenv("CLOUDSIM_ACCOUNT_LOCKOUT_MINUTES", "30"))
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.BUCKETS_DIR.mkdir(exist_ok=True)
        cls.DATABASES_DIR.mkdir(exist_ok=True)
        cls.FUNCTIONS_DIR.mkdir(exist_ok=True)


# Initialize configuration
AppConfig.ensure_directories()
