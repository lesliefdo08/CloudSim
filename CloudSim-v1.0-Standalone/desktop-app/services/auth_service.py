"""
Authentication Service - User management, login, signup, OTP verification

*** OFFLINE MODE ***
Email and OTP services are disabled. All operations work locally without network calls.
"""
from typing import Optional, Dict
from pathlib import Path
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from models.user import User
# Email service disabled for offline mode - returns dummy success values
from services.email_service import email_service
from core.config import EmailConfig, AppConfig


class AuthService:
    """Handle authentication operations"""
    
    def __init__(self):
        self.users_file = AppConfig.USERS_FILE
        self.otp_file = AppConfig.OTPS_FILE
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        self._users: Dict[str, User] = {}
        self._otps: Dict[str, dict] = {}  # email -> {otp_hash, expires, user_id, type}
        self._load_data()
    
    def _load_data(self):
        """Load users from storage"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for user_data in data:
                        user = User.from_dict(user_data)
                        self._users[user.user_id] = user
            except (json.JSONDecodeError, IOError):
                pass
        
        # Load OTPs
        if self.otp_file.exists():
            try:
                with open(self.otp_file, 'r') as f:
                    self._otps = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_users(self):
        """Save users to storage"""
        data = [user.to_dict() for user in self._users.values()]
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_otps(self):
        """Save OTPs to storage"""
        with open(self.otp_file, 'w') as f:
            json.dump(self._otps, f, indent=2)
    
    def _generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return f"{secrets.randbelow(999999):06d}"
    
    def _hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage"""
        return hashlib.sha256(otp.encode()).hexdigest()
    
    def _verify_otp_hash(self, otp: str, otp_hash: str) -> bool:
        """Verify OTP against stored hash"""
        return self._hash_otp(otp) == otp_hash
    
    def signup(self, username: str, email: str, password: str) -> tuple[bool, str, Optional[User]]:
        """
        Sign up new user
        Returns: (success, message, user)
        """
        # Validate inputs
        if not username or not email or not password:
            return False, "All fields are required", None
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters", None
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters", None
        
        if '@' not in email or '.' not in email:
            return False, "Invalid email format", None
        
        # Check if username or email already exists
        for user in self._users.values():
            if user.username.lower() == username.lower():
                return False, "Username already taken", None
            if user.email.lower() == email.lower():
                return False, "Email already registered", None
        
        # Create new user
        user = User.create_new(username, email, password)
        self._users[user.user_id] = user
        self._save_users()
        
        # Generate and send OTP
        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)
        self._otps[email] = {
            'otp_hash': otp_hash,
            'expires': (datetime.now() + timedelta(minutes=EmailConfig.OTP_EXPIRY_MINUTES)).isoformat(),
            'user_id': user.user_id,
            'type': 'verification'
        }
        self._save_otps()
        
        # Send OTP via email
        success, message = email_service.send_otp_verification(email, username, otp)
        
        if not success:
            # Fallback to console if email fails
            print(f"\n{'='*60}")
            print(f"📧 OTP for {email}: {otp}")
            print(f"   (Valid for {EmailConfig.OTP_EXPIRY_MINUTES} minutes)")
            print(f"   Email send failed: {message}")
            print(f"{'='*60}\n")
        
        return True, f"Account created! OTP sent to {email}", user
    
    def verify_otp(self, email: str, otp: str) -> tuple[bool, str]:
        """
        Verify OTP code
        Returns: (success, message)
        """
        if email not in self._otps:
            return False, "No OTP found for this email"
        
        otp_data = self._otps[email]
        
        # Check expiration
        expires = datetime.fromisoformat(otp_data['expires'])
        if datetime.now() > expires:
            del self._otps[email]
            self._save_otps()
            return False, "OTP expired. Please request a new one"
        
        # Check OTP match (compare hashes)
        otp_hash = otp_data.get('otp_hash', otp_data.get('otp'))  # Support legacy
        if 'otp_hash' in otp_data:
            if not self._verify_otp_hash(otp, otp_hash):
                return False, "Invalid OTP code"
        else:
            # Legacy plain OTP support
            if otp_hash != otp:
                return False, "Invalid OTP code"
        
        # Mark user as verified
        user_id = otp_data['user_id']
        if user_id in self._users:
            self._users[user_id].is_verified = True
            self._save_users()
        
        # Clear OTP
        del self._otps[email]
        self._save_otps()
        
        return True, "Email verified successfully!"
    
    def resend_otp(self, email: str) -> tuple[bool, str]:
        """
        Resend OTP to email
        Returns: (success, message)
        """
        # Find user by email
        user = None
        for u in self._users.values():
            if u.email.lower() == email.lower():
                user = u
                break
        
        if not user:
            return False, "Email not found"
        
        if user.is_verified:
            return False, "Email already verified"
        
        # Generate new OTP
        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)
        self._otps[email] = {
            'otp_hash': otp_hash,
            'expires': (datetime.now() + timedelta(minutes=EmailConfig.OTP_EXPIRY_MINUTES)).isoformat(),
            'user_id': user.user_id,
            'type': 'verification'
        }
        self._save_otps()
        
        # Send OTP via email
        success, message = email_service.send_otp_verification(email, user.username, otp)
        
        if not success:
            # Fallback to console
            print(f"\n{'='*60}")
            print(f"📧 New OTP for {email}: {otp}")
            print(f"   (Valid for {EmailConfig.OTP_EXPIRY_MINUTES} minutes)")
            print(f"   Email send failed: {message}")
            print(f"{'='*60}\n")
        
        return True, "New OTP sent!"
    
    def login(self, username_or_email: str, password: str) -> tuple[bool, str, Optional[User]]:
        """
        Login user
        Returns: (success, message, user)
        """
        if not username_or_email or not password:
            return False, "Username/email and password required", None
        
        # Find user by username or email
        user = None
        for u in self._users.values():
            if (u.username.lower() == username_or_email.lower() or 
                u.email.lower() == username_or_email.lower()):
                user = u
                break
        
        if not user:
            return False, "Invalid username/email or password", None
        
        # Verify password
        if not user.verify_password(password):
            return False, "Invalid username/email or password", None
        
        # Check if account is active
        if not user.is_active:
            return False, "Account is disabled", None
        
        # Check if email is verified
        if not user.is_verified:
            return False, "Please verify your email first", None
        
        # Update last login
        user.last_login = datetime.now()
        self._save_users()
        
        # Send login alert email (optional, non-blocking)
        email_service.send_login_alert(user.email, user.username)
        
        return True, "Login successful!", user
    
    def request_password_reset(self, email: str) -> tuple[bool, str]:
        """
        Request password reset by sending OTP
        Returns: (success, message)
        """
        # Find user by email
        user = self.get_user_by_email(email)
        
        if not user:
            # Don't reveal if email exists for security
            return True, f"If an account exists with {email}, a reset code has been sent"
        
        if not user.is_verified:
            return False, "Please verify your email first before resetting password"
        
        if not user.is_active:
            return False, "Account is disabled"
        
        # Generate OTP for password reset
        otp = self._generate_otp()
        otp_hash = self._hash_otp(otp)
        self._otps[email] = {
            'otp_hash': otp_hash,
            'expires': (datetime.now() + timedelta(minutes=EmailConfig.OTP_EXPIRY_MINUTES)).isoformat(),
            'user_id': user.user_id,
            'type': 'password_reset'
        }
        self._save_otps()
        
        # Send OTP via email
        success, message = email_service.send_password_reset(email, user.username, otp)
        
        if not success:
            # Fallback to console
            print(f"\n{'='*60}")
            print(f"🔑 Password Reset OTP for {email}: {otp}")
            print(f"   (Valid for {EmailConfig.OTP_EXPIRY_MINUTES} minutes)")
            print(f"   Email send failed: {message}")
            print(f"{'='*60}\n")
        
        return True, f"If an account exists with {email}, a reset code has been sent"
    
    def reset_password(self, email: str, otp: str, new_password: str) -> tuple[bool, str]:
        """
        Reset password using OTP
        Returns: (success, message)
        """
        # Validate new password
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Check if OTP exists
        if email not in self._otps:
            return False, "No reset request found for this email"
        
        otp_data = self._otps[email]
        
        # Check if it's a password reset OTP
        if otp_data.get('type') != 'password_reset':
            return False, "Invalid reset request"
        
        # Check expiration
        expires = datetime.fromisoformat(otp_data['expires'])
        if datetime.now() > expires:
            del self._otps[email]
            self._save_otps()
            return False, "Reset code expired. Please request a new one"
        
        # Verify OTP
        otp_hash = otp_data.get('otp_hash', otp_data.get('otp'))
        if 'otp_hash' in otp_data:
            if not self._verify_otp_hash(otp, otp_hash):
                return False, "Invalid reset code"
        else:
            if otp_hash != otp:
                return False, "Invalid reset code"
        
        # Get user and update password
        user_id = otp_data['user_id']
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        user.password_hash = User.hash_password(new_password)
        self._save_users()
        
        # Clear OTP
        del self._otps[email]
        self._save_otps()
        
        return True, "Password reset successfully!"
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self._users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    def change_password(self, user_id: str, old_password: str, new_password: str) -> tuple[bool, str]:
        """Change user password"""
        user = self.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if not user.verify_password(old_password):
            return False, "Incorrect current password"
        
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters"
        
        user.password_hash = User.hash_password(new_password)
        self._save_users()
        
        return True, "Password changed successfully!"


# Global auth service instance
auth_service = AuthService()
