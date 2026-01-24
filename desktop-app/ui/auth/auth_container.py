"""
Authentication Container - Manages login/signup/OTP/password reset flow
"""
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout
from PySide6.QtCore import Signal
from ui.auth.login_screen import LoginScreen
from ui.auth.signup_screen import SignupScreen
from ui.auth.otp_screen import OTPScreen
from ui.auth.forgot_password_screen import ForgotPasswordScreen
from ui.auth.reset_password_screen import ResetPasswordScreen


class AuthContainer(QWidget):
    """Container for authentication screens"""
    
    authentication_successful = Signal(object)  # Emits User object
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for different auth screens
        self.stack = QStackedWidget()
        
        # Create screens
        self.login_screen = LoginScreen()
        self.signup_screen = SignupScreen()
        self.otp_screen = OTPScreen()
        self.forgot_password_screen = ForgotPasswordScreen()
        self.reset_password_screen = ResetPasswordScreen()
        
        # Add to stack
        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.signup_screen)
        self.stack.addWidget(self.otp_screen)
        self.stack.addWidget(self.forgot_password_screen)
        self.stack.addWidget(self.reset_password_screen)
        
        # Connect login screen signals
        self.login_screen.login_successful.connect(self.authentication_successful.emit)
        self.login_screen.switch_to_signup.connect(self.show_signup)
        self.login_screen.forgot_password.connect(self.show_forgot_password)
        
        # Connect signup screen signals
        self.signup_screen.signup_successful.connect(self.show_otp)
        self.signup_screen.switch_to_login.connect(self.show_login)
        
        # Connect OTP screen signals
        self.otp_screen.verification_successful.connect(self.show_login)
        self.otp_screen.switch_to_login.connect(self.show_login)
        
        # Connect forgot password screen signals
        self.forgot_password_screen.reset_requested.connect(self.show_reset_password)
        self.forgot_password_screen.switch_to_login.connect(self.show_login)
        
        # Connect reset password screen signals
        self.reset_password_screen.password_reset_success.connect(self.show_login)
        self.reset_password_screen.switch_to_login.connect(self.show_login)
        
        layout.addWidget(self.stack)
        
        # Start with login screen
        self.show_login()
        
    def show_login(self):
        """Show login screen"""
        self.login_screen.clear_form()
        self.stack.setCurrentWidget(self.login_screen)
    
    def show_signup(self):
        """Show signup screen"""
        self.signup_screen.clear_form()
        self.stack.setCurrentWidget(self.signup_screen)
    
    def show_otp(self, email: str):
        """Show OTP verification screen"""
        self.otp_screen.set_email(email)
        self.stack.setCurrentWidget(self.otp_screen)
    
    def show_forgot_password(self):
        """Show forgot password screen"""
        self.forgot_password_screen.clear_form()
        self.stack.setCurrentWidget(self.forgot_password_screen)
    
    def show_reset_password(self, email: str):
        """Show reset password screen"""
        self.reset_password_screen.set_email(email)
        self.reset_password_screen.clear_form()
        self.stack.setCurrentWidget(self.reset_password_screen)
