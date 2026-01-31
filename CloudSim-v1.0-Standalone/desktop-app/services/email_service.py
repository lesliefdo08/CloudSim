"""
Email service for CloudSim authentication and notifications.
Supports SMTP (Gmail, Outlook) with rate limiting and templates.

*** DISABLED FOR OFFLINE MODE ***
All email functionality is stubbed out to allow fully offline operation.
"""

# SMTP imports disabled for offline mode
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
import json

from core.config import EmailConfig, AppConfig


class RateLimiter:
    """Rate limiting for email operations."""
    
    def __init__(self):
        self.rate_limits_file = AppConfig.RATE_LIMITS_FILE
        self._load_limits()
    
    def _load_limits(self):
        """Load rate limit data from file."""
        if self.rate_limits_file.exists():
            with open(self.rate_limits_file, 'r') as f:
                self.limits = json.load(f)
        else:
            self.limits = {}
    
    def _save_limits(self):
        """Save rate limit data to file."""
        with open(self.rate_limits_file, 'w') as f:
            json.dump(self.limits, f, indent=2)
    
    def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, Optional[int]]:
        """
        Check if rate limit is exceeded.
        
        Returns:
            (allowed: bool, retry_after_seconds: Optional[int])
        """
        now = datetime.now()
        
        if key not in self.limits:
            self.limits[key] = []
        
        # Clean old requests outside the window
        cutoff = now - timedelta(seconds=window_seconds)
        self.limits[key] = [
            req_time for req_time in self.limits[key]
            if datetime.fromisoformat(req_time) > cutoff
        ]
        
        # Check if limit exceeded
        if len(self.limits[key]) >= max_requests:
            oldest_request = datetime.fromisoformat(self.limits[key][0])
            retry_after = int((oldest_request + timedelta(seconds=window_seconds) - now).total_seconds())
            return False, max(retry_after, 0)
        
        # Add new request
        self.limits[key] = self.limits[key]
        self.limits[key].append(now.isoformat())
        self._save_limits()
        
        return True, None
    
    def reset_limit(self, key: str):
        """Reset rate limit for a specific key."""
        if key in self.limits:
            del self.limits[key]
            self._save_limits()


class EmailTemplate:
    """Email template generator with HTML styling."""
    
    @staticmethod
    def _get_base_template() -> str:
        """Get base HTML template with CloudSim branding."""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header p {{
            margin: 5px 0 0 0;
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            padding: 40px 30px;
        }}
        .otp-code {{
            background: #f8f9fa;
            border: 2px dashed #6366f1;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 25px 0;
        }}
        .otp-code .code {{
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 8px;
            color: #6366f1;
            font-family: 'Courier New', monospace;
        }}
        .otp-code .expiry {{
            margin-top: 10px;
            font-size: 13px;
            color: #666;
        }}
        .button {{
            display: inline-block;
            background: #6366f1;
            color: white !important;
            padding: 12px 30px;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            margin: 20px 0;
        }}
        .info-box {{
            background: #f0f9ff;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning-box {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            font-size: 13px;
            color: #666;
            border-top: 1px solid #e5e7eb;
        }}
        .footer a {{
            color: #6366f1;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☁️ {app_name}</h1>
            <p>Cloud Infrastructure Simulation Platform</p>
        </div>
        <div class="content">
            {content}
        </div>
        <div class="footer">
            <p>This is an automated message from CloudSim Console.</p>
            <p>If you didn't request this, please ignore this email.</p>
            <p style="margin-top: 15px;">© 2026 CloudSim Console. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    
    @classmethod
    def otp_verification(cls, otp: str, username: str, expiry_minutes: int) -> str:
        """Generate OTP verification email template."""
        content = f"""
            <h2>Welcome to CloudSim, {username}! 🎉</h2>
            <p>Thank you for signing up. To complete your registration, please verify your email address using the One-Time Password (OTP) below:</p>
            
            <div class="otp-code">
                <div class="code">{otp}</div>
                <div class="expiry">⏱️ Expires in {expiry_minutes} minutes</div>
            </div>
            
            <div class="info-box">
                <strong>📧 Verification Instructions:</strong>
                <ol style="margin: 10px 0 0 0; padding-left: 20px;">
                    <li>Copy the OTP code above</li>
                    <li>Return to the CloudSim application</li>
                    <li>Paste the code in the verification field</li>
                    <li>Click "Verify" to activate your account</li>
                </ol>
            </div>
            
            <div class="warning-box">
                <strong>⚠️ Security Notice:</strong>
                <p style="margin: 5px 0 0 0;">Never share this code with anyone. CloudSim staff will never ask for your OTP.</p>
            </div>
        """
        
        return cls._get_base_template().format(
            app_name=AppConfig.APP_NAME,
            content=content
        )
    
    @classmethod
    def password_reset(cls, otp: str, username: str, expiry_minutes: int) -> str:
        """Generate password reset email template."""
        content = f"""
            <h2>Password Reset Request</h2>
            <p>Hello {username},</p>
            <p>We received a request to reset your CloudSim account password. Use the OTP code below to proceed with resetting your password:</p>
            
            <div class="otp-code">
                <div class="code">{otp}</div>
                <div class="expiry">⏱️ Expires in {expiry_minutes} minutes</div>
            </div>
            
            <div class="info-box">
                <strong>🔑 Reset Instructions:</strong>
                <ol style="margin: 10px 0 0 0; padding-left: 20px;">
                    <li>Copy the OTP code above</li>
                    <li>Return to the CloudSim application</li>
                    <li>Enter the OTP and your new password</li>
                    <li>Click "Reset Password" to confirm</li>
                </ol>
            </div>
            
            <div class="warning-box">
                <strong>⚠️ Didn't request this?</strong>
                <p style="margin: 5px 0 0 0;">If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</p>
            </div>
        """
        
        return cls._get_base_template().format(
            app_name=AppConfig.APP_NAME,
            content=content
        )
    
    @classmethod
    def login_alert(cls, username: str, login_time: str, ip_address: str = "Unknown") -> str:
        """Generate login alert email template."""
        content = f"""
            <h2>New Login Detected 🔐</h2>
            <p>Hello {username},</p>
            <p>We detected a new login to your CloudSim account:</p>
            
            <div class="info-box">
                <strong>Login Details:</strong>
                <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                    <li><strong>Time:</strong> {login_time}</li>
                    <li><strong>IP Address:</strong> {ip_address}</li>
                    <li><strong>Device:</strong> CloudSim Desktop Application</li>
                </ul>
            </div>
            
            <p>If this was you, no action is needed. If you don't recognize this login, please secure your account immediately.</p>
            
            <div class="warning-box">
                <strong>⚠️ Suspicious Activity?</strong>
                <p style="margin: 5px 0 0 0;">If you didn't log in, someone may have access to your account. Consider changing your password immediately.</p>
            </div>
        """
        
        return cls._get_base_template().format(
            app_name=AppConfig.APP_NAME,
            content=content
        )


class EmailService:
    """
    Email service for sending authentication and notification emails.
    
    *** OFFLINE MODE - ALL EMAIL FUNCTIONALITY DISABLED ***
    Returns dummy success values without making network calls.
    """
    
    def __init__(self):
        self.config = EmailConfig
        self.rate_limiter = RateLimiter()
        self._test_mode = True  # Always in test mode (offline)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        STUBBED: Email sending disabled for offline mode.
        Returns success without sending any email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body
            text_content: Plain text fallback (optional)
        
        Returns:
            (success: bool, message: str)
        """
        # OFFLINE MODE: No email sent, just return success
        print(f"\n{'='*60}")
        print(f"📧 EMAIL (OFFLINE MODE - NOT SENT)")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"{'='*60}\n")
        return True, "Email sending disabled (offline mode)"
    
    def send_otp_verification(
        self,
        to_email: str,
        username: str,
        otp: str
    ) -> tuple[bool, str]:
        """
        STUBBED: OTP email disabled for offline mode.
        Prints OTP to console instead.
        
        Returns:
            (success: bool, message: str)
        """
        # OFFLINE MODE: Just print OTP to console
        print(f"\n{'='*60}")
        print(f"📧 OTP VERIFICATION (OFFLINE MODE)")
        print(f"User: {username}")
        print(f"Email: {to_email}")
        print(f"OTP Code: {otp}")
        print(f"(Valid for {EmailConfig.OTP_EXPIRY_MINUTES} minutes)")
        print(f"{'='*60}\n")
        return True, f"OTP displayed in console (offline mode)"
    
    def send_password_reset(
        self,
        to_email: str,
        username: str,
        otp: str
    ) -> tuple[bool, str]:
        """
        STUBBED: Password reset email disabled for offline mode.
        Prints OTP to console instead.
        
        Returns:
            (success: bool, message: str)
        """
        # OFFLINE MODE: Just print OTP to console
        print(f"\n{'='*60}")
        print(f"🔑 PASSWORD RESET (OFFLINE MODE)")
        print(f"User: {username}")
        print(f"Email: {to_email}")
        print(f"OTP Code: {otp}")
        print(f"(Valid for {EmailConfig.OTP_EXPIRY_MINUTES} minutes)")
        print(f"{'='*60}\n")
        return True, f"OTP displayed in console (offline mode)"
    
    def send_login_alert(
        self,
        to_email: str,
        username: str,
        ip_address: str = "Unknown"
    ) -> tuple[bool, str]:
        """
        STUBBED: Login alert disabled for offline mode.
        Returns success without sending.
        
        Returns:
            (success: bool, message: str)
        """
        # OFFLINE MODE: No email sent
        return True, "Login alert disabled (offline mode)"


# ORIGINAL EMAIL SENDING CODE (DISABLED FOR OFFLINE MODE)
# Preserved for future use when online mode is re-enabled
"""
class EmailService_ORIGINAL:
    def send_email_ORIGINAL(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> tuple[bool, str]:
        '''Original email sending with SMTP - DISABLED FOR OFFLINE MODE'''
        # All SMTP code below is preserved but commented out
        pass
        
        # Check if email service is configured
        # if not self.config.is_configured():
        #     if self._test_mode:
        #         print(f"\\n{'='*60}")
        #         print(f"📧 EMAIL (Test Mode)")
        #         print(f"{'='*60}")
        #         print(f"To: {to_email}")
        #         print(f"Subject: {subject}")
        #         print(f"{'='*60}\\n")
        #         return True, "Email sent (test mode)"
        #     return False, "Email service not configured."
        
        # try:
        #     # Create message
        #     msg = MIMEMultipart('alternative')
        #     msg['From'] = f"{self.config.EMAIL_SENDER_NAME} <{self.config.EMAIL_SENDER}>"
        #     msg['To'] = to_email
        #     msg['Subject'] = subject
        #     
        #     # Add plain text and HTML parts
        #     if text_content:
        #         msg.attach(MIMEText(text_content, 'plain'))
        #     msg.attach(MIMEText(html_content, 'html'))
        #     
        #     # Connect to SMTP server
        #     if self.config.SMTP_USE_TLS:
        #         server = smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT)
        #         server.starttls()
        #     else:
        #         server = smtplib.SMTP_SSL(self.config.SMTP_SERVER, self.config.SMTP_PORT)
        #     
        #     # Login and send
        #     server.login(self.config.EMAIL_SENDER, self.config.EMAIL_PASSWORD)
        #     server.send_message(msg)
        #     server.quit()
        #     
        #     return True, "Email sent successfully"
        # 
        # except smtplib.SMTPAuthenticationError:
        #     return False, "Failed to authenticate with email server."
        # except smtplib.SMTPException as e:
        #     return False, f"Failed to send email: {str(e)}"
        # except Exception as e:
        #     return False, f"Unexpected error: {str(e)}"
"""


# Global email service instance
email_service = EmailService()
