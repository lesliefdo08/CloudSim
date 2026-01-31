"""
Signup Screen - User registration with email verification
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from services.auth_service import AuthService
from ui.design_system import Colors, Fonts, Spacing
from ui.components.notifications import NotificationManager


class SignupScreen(QWidget):
    """Modern signup screen"""
    
    signup_successful = Signal(str)  # Emits email for OTP verification
    switch_to_login = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self._init_ui()
        
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
        
        # Signup card
        signup_card = self._create_signup_card()
        center_layout.addWidget(signup_card)
        
        layout.addWidget(center_container)
        
    def _create_signup_card(self) -> QFrame:
        """Create signup card"""
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
        
        # Form
        form = self._create_form()
        layout.addWidget(form)
        
        # Signup button
        self.signup_btn = QPushButton("Create Account")
        self.signup_btn.setFixedHeight(48)
        self.signup_btn.setStyleSheet(f"""
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
        self.signup_btn.clicked.connect(self._handle_signup)
        layout.addWidget(self.signup_btn)
        
        # Login link
        login_layout = QHBoxLayout()
        login_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        login_label = QLabel("Already have an account?")
        login_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.BODY};
        """)
        login_layout.addWidget(login_label)
        
        login_btn = QPushButton("Sign In")
        login_btn.setStyleSheet(f"""
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
        login_btn.clicked.connect(self.switch_to_login.emit)
        login_layout.addWidget(login_btn)
        
        layout.addLayout(login_layout)
        
        return card
    
    def _create_header(self) -> QWidget:
        """Create header"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo
        logo = QLabel("☁️")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 64px;")
        layout.addWidget(logo)
        
        # Title
        title = QLabel("Create Account")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Join CloudSim Console")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(subtitle)
        
        return container
    
    def _create_form(self) -> QWidget:
        """Create signup form"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Username field
        username_label = QLabel("Username")
        username_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username (min 3 characters)")
        self.username_input.setFixedHeight(48)
        self._style_input(self.username_input)
        layout.addWidget(self.username_input)
        
        # Email field
        email_label = QLabel("Email")
        email_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setFixedHeight(48)
        self._style_input(self.email_input)
        layout.addWidget(self.email_input)
        
        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Create a password (min 6 characters)")
        self.password_input.setFixedHeight(48)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._style_input(self.password_input)
        layout.addWidget(self.password_input)
        
        # Confirm password field
        confirm_label = QLabel("Confirm Password")
        confirm_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(confirm_label)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Re-enter your password")
        self.confirm_input.setFixedHeight(48)
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.returnPressed.connect(self._handle_signup)
        self._style_input(self.confirm_input)
        layout.addWidget(self.confirm_input)
        
        return container
    
    def _style_input(self, input_widget: QLineEdit):
        """Apply consistent styling to input fields"""
        input_widget.setStyleSheet(f"""
            QLineEdit {{
                background: {Colors.SURFACE};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 0 16px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
                background: {Colors.SURFACE_HOVER};
            }}
            QLineEdit::placeholder {{
                color: {Colors.TEXT_MUTED};
            }}
        """)
    
    def _handle_signup(self):
        """Handle signup button click"""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_input.text()
        
        # Validation
        if not username or not email or not password:
            NotificationManager.show_error("All fields are required")
            return
        
        if password != confirm:
            NotificationManager.show_error("Passwords do not match")
            return
        
        # Disable button during signup
        self.signup_btn.setEnabled(False)
        self.signup_btn.setText("Creating account...")
        
        # Perform signup (use QTimer to not block UI)
        QTimer.singleShot(100, lambda: self._do_signup(username, email, password))
    
    def _do_signup(self, username: str, email: str, password: str):
        """Perform actual signup"""
        success, message, user = self.auth_service.signup(username, email, password)
        
        # Re-enable button
        self.signup_btn.setEnabled(True)
        self.signup_btn.setText("Create Account")
        
        if success:
            NotificationManager.show_success(message)
            self.signup_successful.emit(email)
            self._clear_form()
        else:
            NotificationManager.show_error(message)
    
    def _clear_form(self):
        """Clear form inputs"""
        self.username_input.clear()
        self.email_input.clear()
        self.password_input.clear()
        self.confirm_input.clear()
    
    def clear_form(self):
        """Public method to clear form"""
        self._clear_form()
