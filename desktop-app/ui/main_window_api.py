"""
CloudSim Main Window - Professional Cloud Console with API Integration
Realistic cloud infrastructure simulator interface with proper logo integration
"""
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
    QFrame, QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon
from pathlib import Path

from api.client import APIClient
from ui.design_system import Colors, Fonts, Spacing, Branding
from ui.views.ec2_view import EC2View
from ui.views.s3_view import S3View
from ui.views.iam_view_simple import IAMViewSimple
from ui.views.lambda_view import LambdaView
from ui.views.rds_view import RDSView


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent.parent
    return base_path / relative_path


class APIMainWindow(QMainWindow):
    """Main window with professional cloud console design and API integration"""
    
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        """Initialize the user interface with proper branding"""
        self.setWindowTitle(f"{Branding.APP_NAME} - Cloud Simulator")
        self.setMinimumSize(1400, 900)
        self.setGeometry(100, 50, 1600, 1000)
        
        # Set window icon
        icon_path = get_resource_path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self._create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Content area
        content_widget = self._create_content_area()
        main_layout.addWidget(content_widget, 1)
        
        # Apply modern styling with gradient
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {Colors.BG_PRIMARY};
            }}
            QWidget {{
                font-family: {Fonts.PRIMARY};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        
        # Show EC2 view by default
        self._switch_to_view(0)
        
    def _create_sidebar(self):
        """Create modern sidebar with gradient header"""
        sidebar = QFrame()
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-right: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with logo
        header = self._create_header()
        layout.addWidget(header)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background: {Colors.BORDER};")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        
        # Service buttons
        self.service_buttons = []
        services = [
            ("Compute (EC2)", "🖥️"),
            ("Storage (S3)", "📦"),
            ("Identity (IAM)", "👤"),
            ("Serverless (Lambda)", "λ"),
            ("Database (RDS)", "🗄️"),
        ]
        
        for i, (name, icon) in enumerate(services):
            btn = self._create_service_button(name, icon, i)
            self.service_buttons.append(btn)
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Footer with connection status
        footer = self._create_footer()
        layout.addWidget(footer)
        
        return sidebar
        
    def _create_header(self):
        """Create header with gradient background and logo"""
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {Colors.BG_GRADIENT_START}, stop: 1 {Colors.BG_GRADIENT_END});
                border: none;
                border-bottom: 3px solid {Colors.PRIMARY};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(25, 15, 25, 15)
        layout.setSpacing(15)
        
        # Logo image (if available)
        logo_path = get_resource_path("logo.png")
        if logo_path.exists():
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setFixedSize(60, 60)
                logo_label.setStyleSheet("background: transparent; border: 2px solid white; border-radius: 30px; padding: 5px;")
                layout.addWidget(logo_label)
        
        # Title and subtitle with modern styling
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel(Branding.APP_NAME)
        title.setFont(QFont(Fonts.PRIMARY, 20, QFont.Bold))
        title.setStyleSheet("color: white; border: none; background: transparent;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("☁️ Cloud Infrastructure Simulator")
        subtitle.setFont(QFont(Fonts.PRIMARY, 10))
        subtitle.setStyleSheet(f"color: rgba(255, 255, 255, 0.9); border: none; background: transparent;")
        text_layout.addWidget(subtitle)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return header
    
    def _create_service_button(self, text, icon, index):
        """Create modern service navigation button"""
        from PySide6.QtWidgets import QPushButton
        
        btn = QPushButton(f"{icon}  {text}")
        btn.setCheckable(True)
        btn.setFixedHeight(56)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_to_view(index))
        
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-left: 4px solid transparent;
                text-align: left;
                padding-left: 24px;
                font-size: 14px;
                font-weight: 500;
                color: {Colors.TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background: {Colors.BG_HOVER};
                color: {Colors.PRIMARY};
            }}
            QPushButton:checked {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 {Colors.PRIMARY_LIGHT}, stop: 1 white);
                border-left: 4px solid {Colors.PRIMARY};
                color: {Colors.PRIMARY};
                font-weight: 700;
            }}
        """)
        
        return btn
        
    def _create_footer(self):
        """Create modern footer with gradient"""
        footer = QFrame()
        footer.setFixedHeight(50)
        footer.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #F9FAFB, stop: 1 white);
                border-top: 2px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(25, 10, 25, 10)
        layout.setSpacing(20)
        
        # Connection status with badge
        self.connection_label = QLabel("● Backend: Ready")
        self.connection_label.setFont(QFont(Fonts.PRIMARY, 10, QFont.Bold))
        self.connection_label.setStyleSheet(f"""
            color: {Colors.SUCCESS}; 
            background: rgba(16, 185, 129, 0.1);
            border: none;
            padding: 6px 14px;
            border-radius: 12px;
        """)
        layout.addWidget(self.connection_label)
        
        layout.addStretch()
        
        # Version badge
        version = QLabel(f"⚡ {Branding.VERSION}")
        version.setFont(QFont(Fonts.PRIMARY, 9, QFont.Bold))
        version.setStyleSheet(f"""
            color: {Colors.PRIMARY};
            background: {Colors.PRIMARY_LIGHT};
            border: none;
            padding: 4px 12px;
            border-radius: 10px;
        """)
        layout.addWidget(version)
        
        return footer
        
    def _create_content_area(self):
        """Create main content area"""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top bar
        top_bar = self._create_top_bar()
        layout.addWidget(top_bar)
        
        # Stacked widget for views
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(f"""
            QStackedWidget {{
                background: {Colors.BG_PRIMARY};
            }}
        """)
        
        # Create views
        self.ec2_view = EC2View(self.api_client)
        self.s3_view = S3View(self.api_client)
        self.iam_view = IAMViewSimple(self.api_client)
        self.lambda_view = LambdaView(self.api_client)
        self.rds_view = RDSView(self.api_client)
        
        # Add views to stack
        self.stacked_widget.addWidget(self.ec2_view)
        self.stacked_widget.addWidget(self.s3_view)
        self.stacked_widget.addWidget(self.iam_view)
        self.stacked_widget.addWidget(self.lambda_view)
        self.stacked_widget.addWidget(self.rds_view)
        
        layout.addWidget(self.stacked_widget, 1)
        
        return content
    
    def _create_top_bar(self):
        """Create modern top bar with breadcrumbs"""
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(35, 15, 35, 15)
        
        # Breadcrumb with icon
        self.breadcrumb_label = QLabel("📍 Services > Compute (EC2)")
        self.breadcrumb_label.setFont(QFont(Fonts.PRIMARY, 13, QFont.Bold))
        self.breadcrumb_label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            border: none;
        """)
        layout.addWidget(self.breadcrumb_label)
        
        layout.addStretch()
        
        # Region selector with modern badge style
        region_label = QLabel("🌍 us-east-1")
        region_label.setFont(QFont(Fonts.PRIMARY, 10))
        region_label.setStyleSheet(f"""
            color: {Colors.PRIMARY};
            background: {Colors.PRIMARY_LIGHT};
            border: 2px solid {Colors.PRIMARY};
            border-radius: 12px;
            padding: 6px 16px;
            font-weight: 600;
        """)
        layout.addWidget(region_label)
        
        return top_bar
        
    def _switch_to_view(self, index):
        """Switch to a different service view"""
        # Update button states
        for i, btn in enumerate(self.service_buttons):
            btn.setChecked(i == index)
        
        # Update breadcrumb with icons
        breadcrumbs = [
            "📍 Services > Compute (EC2)",
            "📍 Services > Storage (S3)",
            "📍 Services > Identity (IAM)",
            "📍 Services > Serverless (Lambda)",
            "📍 Services > Database (RDS)",
        ]
        self.breadcrumb_label.setText(breadcrumbs[index])
        
        # Switch view
        self.stacked_widget.setCurrentIndex(index)
        
    def connect_signals(self):
        """Connect API client signals"""
        self.api_client.request_started.connect(self._on_request_started)
        self.api_client.request_finished.connect(self._on_request_finished)
        self.api_client.error_occurred.connect(self._show_error)
        
    def _on_request_started(self):
        """Handle API request started"""
        self.connection_label.setText("● Backend: Connecting...")
        self.connection_label.setStyleSheet(f"color: {Colors.PRIMARY}; border: none;")
        
    def _on_request_finished(self):
        """Handle API request finished"""
        self.connection_label.setText("● Backend: Ready")
        self.connection_label.setStyleSheet(f"color: {Colors.SUCCESS}; border: none;")
        
    def _show_error(self, message):
        """Show error dialog"""
        self.connection_label.setText("● Backend: Error")
        self.connection_label.setStyleSheet(f"color: {Colors.DANGER}; border: none;")
        
        QMessageBox.critical(
            self,
            "CloudSim Error",
            message,
            QMessageBox.Ok
        )
