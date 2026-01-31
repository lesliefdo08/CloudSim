"""
Login Screen - Modern authentication UI
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from services.auth_service import AuthService
from ui.design_system import Colors, Fonts, Spacing
from ui.components.notifications import NotificationManager


class LoginScreen(QWidget):
    """Modern login screen"""
    
    login_successful = Signal(object)  # Emits User object
    switch_to_signup = Signal()
    forgot_password = Signal()  # New signal for forgot password
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI"""
        # Main layout
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
        
        # Login card
        login_card = self._create_login_card()
        center_layout.addWidget(login_card)
        
        layout.addWidget(center_container)
        
    def _create_login_card(self) -> QFrame:
        """Create login card"""
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
        
        # Logo and title
        header = self._create_header()
        layout.addWidget(header)
        
        # Form
        form = self._create_form()
        layout.addWidget(form)
        
        # Login button
        self.login_btn = QPushButton("Sign In")
        self.login_btn.setFixedHeight(48)
        self.login_btn.setStyleSheet(f"""
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
            QPushButton:pressed {{
                background: {Colors.ACCENT};
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """)
        self.login_btn.clicked.connect(self._handle_login)
        layout.addWidget(self.login_btn)
        
        # Signup link
        signup_layout = QHBoxLayout()
        signup_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        signup_label = QLabel("Don't have an account?")
        signup_label.setStyleSheet(f"""
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.BODY};
        """)
        signup_layout.addWidget(signup_label)
        
        signup_btn = QPushButton("Sign Up")
        signup_btn.setStyleSheet(f"""
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
        signup_btn.clicked.connect(self.switch_to_signup.emit)
        signup_layout.addWidget(signup_btn)
        
        layout.addLayout(signup_layout)
        
        return card
    
    def _create_header(self) -> QWidget:
        """Create header with logo and title"""
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
        title = QLabel("CloudSim Console")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Sign in to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(subtitle)
        
        return container
    
    def _create_form(self) -> QWidget:
        """Create login form"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Username/Email field
        username_label = QLabel("Username or Email")
        username_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username or email")
        self.username_input.setFixedHeight(48)
        self.username_input.returnPressed.connect(self._handle_login)
        self._style_input(self.username_input)
        layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("Password")
        password_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.MEDIUM};
        """)
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setFixedHeight(48)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self._handle_login)
        self._style_input(self.password_input)
        layout.addWidget(self.password_input)
        
        # Remember me and forgot password row
        bottom_row = QHBoxLayout()
        
        remember_check = QCheckBox("Remember me")
        remember_check.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.BODY};
            }}
        """)
        bottom_row.addWidget(remember_check)
        
        bottom_row.addStretch()
        
        # Forgot password link
        forgot_link = QPushButton("Forgot Password?")
        forgot_link.setFlat(True)
        forgot_link.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.ACCENT};
                font-size: {Fonts.BODY};
                padding: 0;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
                text-decoration: underline;
            }}
        """)
        forgot_link.clicked.connect(self.forgot_password.emit)
        bottom_row.addWidget(forgot_link)
        
        layout.addLayout(bottom_row)
        
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
    
    def _handle_login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            NotificationManager.show_error("Please enter username and password")
            return
        
        # Disable button during login
        self.login_btn.setEnabled(False)
        self.login_btn.setText("Signing in...")
        
        # Perform login (use QTimer to not block UI)
        QTimer.singleShot(100, lambda: self._do_login(username, password))
    
    def _do_login(self, username: str, password: str):
        """Perform actual login"""
        success, message, user = self.auth_service.login(username, password)
        
        # Re-enable button
        self.login_btn.setEnabled(True)
        self.login_btn.setText("Sign In")
        
        if success:
            NotificationManager.show_success(message)
            self.login_successful.emit(user)
            self._clear_form()
        else:
            NotificationManager.show_error(message)
    
    def _clear_form(self):
        """Clear form inputs"""
        self.username_input.clear()
        self.password_input.clear()
    
    def clear_form(self):
        """Public method to clear form"""
        self._clear_form()
