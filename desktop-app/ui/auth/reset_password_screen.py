"""
Reset Password Screen - Enter OTP and new password
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QLineEdit, QHBoxLayout)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from services.auth_service import auth_service
from ui.components.notifications import NotificationManager
from ui.design_system import Colors, Fonts, Spacing


class ResetPasswordScreen(QWidget):
    """Reset password screen - enter OTP and new password"""
    
    # Signals
    password_reset_success = Signal()
    switch_to_login = Signal()
    
    def __init__(self):
        super().__init__()
        self.notification_manager = NotificationManager()
        self._email = ""
        self._init_ui()
    
    def set_email(self, email: str):
        """Set the email for password reset"""
        self._email = email
        self.email_label.setText(f"Enter the code sent to {email}")
    
    def _init_ui(self):
        """Initialize the UI"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create reset card
        card = self._create_reset_card()
        layout.addWidget(card)
        
        # Apply styles
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.BACKGROUND},
                    stop:1 {Colors.SURFACE}
                );
            }}
        """)
    
    def _create_reset_card(self) -> QWidget:
        """Create the reset password card"""
        card = QWidget()
        card.setFixedWidth(450)
        card.setStyleSheet(f"""
            QWidget {{
                background: {Colors.SURFACE};
                border-radius: 12px;
                padding: {Spacing.XL}px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(int(Spacing.LG.replace("px", "")))
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Form
        form = self._create_form()
        layout.addLayout(form)
        
        # Reset button
        reset_btn = QPushButton("Reset Password")
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 6px;
                padding: {Spacing.MD}px;
                font-size: {Fonts.BODY}px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background: {Colors.TEXT_MUTED};
                color: {Colors.TEXT_SECONDARY};
            }}
        """)
        reset_btn.clicked.connect(self._handle_reset)
        layout.addWidget(reset_btn)
        self.reset_btn = reset_btn
        
        # Resend code link
        resend_layout = QHBoxLayout()
        resend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        resend_label = QLabel("Didn't receive the code?")
        resend_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.SMALL}px;
        """)
        
        resend_link = QPushButton("Resend Code")
        resend_link.setFlat(True)
        resend_link.setStyleSheet(f"""
            QPushButton {{
                color: {Colors.ACCENT};
                border: none;
                padding: 0;
                font-size: {Fonts.SMALL}px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
                text-decoration: underline;
            }}
        """)
        resend_link.clicked.connect(self._handle_resend)
        
        resend_layout.addWidget(resend_label)
        resend_layout.addSpacing(int(Spacing.XS.replace("px", "")))
        resend_layout.addWidget(resend_link)
        
        layout.addLayout(resend_layout)
        
        # Back to login link
        back_link = QPushButton("← Back to Login")
        back_link.setFlat(True)
        back_link.setStyleSheet(f"""
            QPushButton {{
                color: {Colors.TEXT_SECONDARY};
                border: none;
                padding: 0;
                font-size: {Fonts.SMALL}px;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT};
            }}
        """)
        back_link.clicked.connect(self.switch_to_login.emit)
        layout.addWidget(back_link, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return card
    
    def _create_header(self) -> QWidget:
        """Create header section"""
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setSpacing(int(Spacing.SM.replace("px", "")))
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon and title
        title = QLabel("🔐 Create New Password")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE}px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
        """)
        
        self.email_label = QLabel("Enter the verification code")
        self.email_label.setWordWrap(True)
        self.email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.email_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL}px;
            color: {Colors.TEXT_SECONDARY};
            margin-top: {Spacing.XS}px;
        """)
        
        layout.addWidget(title)
        layout.addWidget(self.email_label)
        
        return header
    
    def _create_form(self) -> QVBoxLayout:
        """Create the form"""
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.MD.replace("px", "")))
        
        # OTP field
        otp_label = QLabel("Verification Code")
        otp_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL}px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.XS}px;
        """)
        
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Enter 6-digit code")
        self.otp_input.setMaxLength(6)
        self.otp_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.BACKGROUND};
                border: 2px solid {Colors.BORDER};
                border-radius: 6px;
                padding: {Spacing.MD}px;
                font-size: 24px;
                font-weight: 600;
                color: {Colors.TEXT_PRIMARY};
                letter-spacing: 8px;
                text-align: center;
                font-family: 'Courier New', monospace;
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        layout.addWidget(otp_label)
        layout.addWidget(self.otp_input)
        
        # New password field
        password_label = QLabel("New Password")
        password_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL}px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.XS}px;
            margin-top: {Spacing.MD}px;
        """)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter new password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.BACKGROUND};
                border: 2px solid {Colors.BORDER};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Fonts.BODY}px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        layout.addWidget(password_label)
        layout.addWidget(self.password_input)
        
        # Confirm password field
        confirm_label = QLabel("Confirm Password")
        confirm_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL}px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.XS}px;
        """)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm new password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.BACKGROUND};
                border: 2px solid {Colors.BORDER};
                border-radius: 6px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-size: {Fonts.BODY}px;
                color: {Colors.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
            }}
        """)
        self.confirm_input.returnPressed.connect(self._handle_reset)
        
        layout.addWidget(confirm_label)
        layout.addWidget(self.confirm_input)
        
        return layout
    
    def _handle_reset(self):
        """Handle password reset"""
        otp = self.otp_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        # Validate
        if not otp:
            self.notification_manager.show_warning("Please enter the verification code")
            return
        
        if len(otp) != 6 or not otp.isdigit():
            self.notification_manager.show_error("Please enter a valid 6-digit code")
            return
        
        if not password:
            self.notification_manager.show_warning("Please enter a new password")
            return
        
        if len(password) < 6:
            self.notification_manager.show_error("Password must be at least 6 characters")
            return
        
        if password != confirm:
            self.notification_manager.show_error("Passwords do not match")
            return
        
        # Disable button
        self.reset_btn.setEnabled(False)
        self.reset_btn.setText("Resetting...")
        
        # Reset password (use QTimer for async simulation)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._do_reset(otp, password))
    
    def _do_reset(self, otp: str, password: str):
        """Perform the password reset"""
        success, message = auth_service.reset_password(self._email, otp, password)
        
        # Re-enable button
        self.reset_btn.setEnabled(True)
        self.reset_btn.setText("Reset Password")
        
        if success:
            self.notification_manager.show_success(message)
            self.clear_form()
            self.password_reset_success.emit()
        else:
            self.notification_manager.show_error(message)
    
    def _handle_resend(self):
        """Handle resend code"""
        if not self._email:
            return
        
        success, message = auth_service.request_password_reset(self._email)
        
        if success:
            self.notification_manager.show_success("New code sent!")
        else:
            self.notification_manager.show_error(message)
    
    def clear_form(self):
        """Clear the form"""
        self.otp_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
