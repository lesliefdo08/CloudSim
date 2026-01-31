"""
Forgot Password Screen - Request password reset
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                               QLineEdit, QHBoxLayout)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from services.auth_service import auth_service
from ui.components.notifications import NotificationManager
from ui.design_system import Colors, Fonts, Spacing


class ForgotPasswordScreen(QWidget):
    """Forgot password screen - request reset via email"""
    
    # Signals
    reset_requested = Signal(str)  # email
    switch_to_login = Signal()
    
    def __init__(self):
        super().__init__()
        self.notification_manager = NotificationManager()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create forgot password card
        card = self._create_forgot_password_card()
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
    
    def _create_forgot_password_card(self) -> QWidget:
        """Create the forgot password card"""
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
        layout.setSpacing(int(Spacing.LG.replace('px', '')))
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Form
        form = self._create_form()
        layout.addLayout(form)
        
        # Reset button
        reset_btn = QPushButton("Send Reset Code")
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
        reset_btn.clicked.connect(self._handle_reset_request)
        layout.addWidget(reset_btn)
        self.reset_btn = reset_btn
        
        # Back to login link
        back_layout = QHBoxLayout()
        back_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        back_label = QLabel("Remember your password?")
        back_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.SMALL}px;
        """)
        
        back_link = QPushButton("Back to Login")
        back_link.setFlat(True)
        back_link.setStyleSheet(f"""
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
        back_link.clicked.connect(self.switch_to_login.emit)
        
        back_layout.addWidget(back_label)
        back_layout.addSpacing(int(Spacing.XS.replace("px", "")))
        back_layout.addWidget(back_link)
        
        layout.addLayout(back_layout)
        
        return card
    
    def _create_header(self) -> QWidget:
        """Create header section"""
        header = QWidget()
        layout = QVBoxLayout(header)
        layout.setSpacing(int(Spacing.SM.replace("px", "")))
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon and title
        title = QLabel("🔑 Reset Password")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE}px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
        """)
        
        subtitle = QLabel("Enter your email address and we'll send you a code to reset your password.")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SMALL}px;
            color: {Colors.TEXT_SECONDARY};
            margin-top: {Spacing.XS}px;
        """)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        return header
    
    def _create_form(self) -> QVBoxLayout:
        """Create the form"""
        layout = QVBoxLayout()
        layout.setSpacing(int(Spacing.MD.replace("px", "")))
        
        # Email field
        email_label = QLabel("Email Address")
        email_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL}px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.XS}px;
        """)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        self.email_input.setStyleSheet(f"""
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
        self.email_input.returnPressed.connect(self._handle_reset_request)
        
        layout.addWidget(email_label)
        layout.addWidget(self.email_input)
        
        return layout
    
    def _handle_reset_request(self):
        """Handle reset request"""
        email = self.email_input.text().strip()
        
        # Validate
        if not email:
            self.notification_manager.show_warning("Please enter your email address")
            return
        
        if '@' not in email or '.' not in email:
            self.notification_manager.show_error("Please enter a valid email address")
            return
        
        # Disable button
        self.reset_btn.setEnabled(False)
        self.reset_btn.setText("Sending...")
        
        # Request reset (use QTimer for async simulation)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._do_reset_request(email))
    
    def _do_reset_request(self, email: str):
        """Perform the reset request"""
        success, message = auth_service.request_password_reset(email)
        
        # Re-enable button
        self.reset_btn.setEnabled(True)
        self.reset_btn.setText("Send Reset Code")
        
        if success:
            self.notification_manager.show_success(message)
            self.reset_requested.emit(email)
        else:
            self.notification_manager.show_error(message)
    
    def clear_form(self):
        """Clear the form"""
        self.email_input.clear()
