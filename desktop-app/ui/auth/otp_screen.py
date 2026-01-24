"""
OTP Verification Screen - Email verification with OTP
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from services.auth_service import AuthService
from ui.design_system import Colors, Fonts, Spacing
from ui.components.notifications import NotificationManager


class OTPScreen(QWidget):
    """OTP verification screen"""
    
    verification_successful = Signal()
    switch_to_login = Signal()
    
    def __init__(self, email: str = "", parent=None):
        super().__init__(parent)
        self.email = email
        self.auth_service = AuthService()
        self._init_ui()
        
    def set_email(self, email: str):
        """Set email for verification"""
        self.email = email
        self.email_label.setText(f"Enter the 6-digit code sent to {email}")
        
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Background
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0f1e, stop:1 #0f172a);
            }}
        """)
        
        # Center container
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # OTP card
        otp_card = self._create_otp_card()
        center_layout.addWidget(otp_card)
        
        layout.addWidget(center_container)
        
    def _create_otp_card(self) -> QFrame:
        """Create OTP verification card"""
        card = QFrame()
        card.setFixedWidth(450)
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(32)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # OTP input
        otp_container = self._create_otp_input()
        layout.addWidget(otp_container)
        
        # Verify button
        self.verify_btn = QPushButton("Verify Email")
        self.verify_btn.setFixedHeight(48)
        self.verify_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.ACCENT};
                border: none;
                border-radius: 8px;
                color: white;
                font-size: {Fonts.HEADING};
                font-weight: {Fonts.SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
        self.verify_btn.clicked.connect(self._handle_verify)
        layout.addWidget(self.verify_btn)
        
        # Resend link
        resend_layout = QHBoxLayout()
        resend_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        resend_label = QLabel("Didn't receive code?")
        resend_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.BODY};
        """)
        resend_layout.addWidget(resend_label)
        
        resend_btn = QPushButton("Resend")
        resend_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.ACCENT};
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
                text-decoration: underline;
            }}
        """)
        resend_btn.clicked.connect(self._handle_resend)
        resend_layout.addWidget(resend_btn)
        
        layout.addLayout(resend_layout)
        
        # Back to login link
        back_btn = QPushButton("← Back to Login")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.BODY};
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        back_btn.clicked.connect(self.switch_to_login.emit)
        layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return card
    
    def _create_header(self) -> QWidget:
        """Create header"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon
        icon = QLabel("📧")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 64px;")
        layout.addWidget(icon)
        
        # Title
        title = QLabel("Verify Your Email")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Subtitle
        self.email_label = QLabel(f"Enter the 6-digit code sent to {self.email}")
        self.email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.email_label.setWordWrap(True)
        self.email_label.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(self.email_label)
        
        return container
    
    def _create_otp_input(self) -> QWidget:
        """Create OTP input field"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        label = QLabel("Verification Code")
        label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(label)
        
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("000000")
        self.otp_input.setFixedHeight(64)
        self.otp_input.setMaxLength(6)
        self.otp_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.otp_input.returnPressed.connect(self._handle_verify)
        self.otp_input.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.SURFACE};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 0 16px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 28px;
                font-weight: {Fonts.BOLD};
                letter-spacing: 8px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
                background: {Colors.SURFACE_HOVER};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
                letter-spacing: 8px;
            }}
        """)
        layout.addWidget(self.otp_input)
        
        # Helper text
        helper = QLabel("Check your email inbox (and spam folder)")
        helper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        helper.setStyleSheet(f"""
            color: {Colors.TEXT_MUTED};
            font-size: {Fonts.SMALL};
        """)
        layout.addWidget(helper)
        
        return container
    
    def _handle_verify(self):
        """Handle verify button click"""
        otp = self.otp_input.text().strip()
        
        if len(otp) != 6 or not otp.isdigit():
            NotificationManager.show_error("Please enter a valid 6-digit code")
            return
        
        # Disable button during verification
        self.verify_btn.setEnabled(False)
        self.verify_btn.setText("Verifying...")
        
        # Perform verification
        QTimer.singleShot(100, lambda: self._do_verify(otp))
    
    def _do_verify(self, otp: str):
        """Perform actual verification"""
        success, message = self.auth_service.verify_otp(self.email, otp)
        
        # Re-enable button
        self.verify_btn.setEnabled(True)
        self.verify_btn.setText("Verify Email")
        
        if success:
            NotificationManager.show_success(message)
            self.verification_successful.emit()
            self.otp_input.clear()
        else:
            NotificationManager.show_error(message)
    
    def _handle_resend(self):
        """Handle resend OTP"""
        success, message = self.auth_service.resend_otp(self.email)
        
        if success:
            NotificationManager.show_success(message)
        else:
            NotificationManager.show_error(message)
    
    def clear_form(self):
        """Public method to clear form"""
        self.otp_input.clear()
