"""
Main Window - Premium Enterprise Console
Professional UI/UX Design
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QStatusBar, QPushButton, QComboBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont
from pathlib import Path
from ui.sidebar import Sidebar
from ui.design_system import Colors, Fonts, Styles, Branding
from ui.views.dashboard_view import DashboardView
from ui.views.compute_view import ComputeView
from ui.views.storage_view import StorageView
from ui.views.database_view import DatabaseView
from ui.views.serverless_view import ServerlessView
from ui.views.volumes_view import VolumesView
from ui.views.iam_view import IAMView
from ui.views.activity_log_view_enhanced import EnhancedActivityLogView
from services.volume_service import VolumeService
from ui.utils import show_permission_denied
from ui.components.notifications import NotificationManager, GlobalActivityFeed


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        # Window properties
        self.setWindowTitle(f"{Branding.APP_NAME} Console {Branding.VERSION}")
        self.setMinimumSize(1400, 900)
        
        # Set window background with subtle pattern
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0f1e, stop:1 #0f172a);
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # User info bar at top
        user_bar = self._create_user_bar()
        main_layout.addWidget(user_bar)
        
        # Content area with sidebar
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Create sidebar
        self.sidebar = Sidebar()
        self.sidebar.button_clicked.connect(self.switch_view)
        content_layout.addWidget(self.sidebar)
        
        # Create main content area with modern styling
        content_container = QWidget()
        content_container.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #0a0f1e, stop:1 #0f172a);"
        )
        self.content_area = QVBoxLayout(content_container)
        self.content_area.setContentsMargins(0, 0, 0, 0)
        self.content_area.setSpacing(0)
        content_layout.addWidget(content_container, 1)
        
        main_layout.addWidget(content_widget)
        
        # Initialize services
        self.volume_service = VolumeService()
        
        # Initialize notification system
        self.notification_manager = NotificationManager(self)
        
        # Create views
        self.views = {
            "Dashboard": DashboardView(),
            "Compute": ComputeView(volume_service=self.volume_service),
            "Storage": StorageView(),
            "Volumes": VolumesView(),
            "Database": DatabaseView(),
            "Serverless": ServerlessView(),
            "IAM": IAMView(),
            "Activity": EnhancedActivityLogView()
        }
        
        # Connect dashboard navigation signals
        self.views["Dashboard"].navigate_to_service.connect(self.navigate_to_service)
        
        # Create status bar
        self._create_status_bar()
        
        # Show dashboard by default
        self.current_view = None
        self.switch_view("Dashboard")
    
    def _create_user_bar(self) -> QFrame:
        """Create realistic header bar with account ID, region, and latency indicator"""
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(20)
        
        # App title
        title = QLabel("☁️ CloudSim Console")
        title.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        # Account ID (fake but realistic)
        account_container = QWidget()
        account_layout = QVBoxLayout(account_container)
        account_layout.setContentsMargins(0, 0, 0, 0)
        account_layout.setSpacing(2)
        
        account_label = QLabel("Account")
        account_label.setStyleSheet(f"""
            font-size: {Fonts.TINY};
            color: {Colors.TEXT_MUTED};
        """)
        account_layout.addWidget(account_label)
        
        account_id = QLabel("123456789012")
        account_id.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.MONOSPACE};
        """)
        account_layout.addWidget(account_id)
        
        layout.addWidget(account_container)
        
        layout.addStretch()
        
        # Region selector with latency indicator
        region_container = QWidget()
        region_layout = QHBoxLayout(region_container)
        region_layout.setContentsMargins(0, 0, 0, 0)
        region_layout.setSpacing(12)
        
        region_combo = QComboBox()
        region_combo.addItems(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])
        region_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 6px 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
                min-width: 120px;
            }}
            QComboBox:hover {{
                border-color: {Colors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                selection-background-color: {Colors.ACCENT};
            }}
        """)
        region_layout.addWidget(region_combo)
        
        # Latency indicator
        latency_label = QLabel("🟢 15ms")
        latency_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.SUCCESS};
            background: {Colors.SUCCESS_BG};
            padding: 6px 12px;
            border-radius: 8px;
            font-family: {Fonts.MONOSPACE};
        """)
        latency_label.setToolTip("Region latency")
        region_layout.addWidget(latency_label)
        
        layout.addWidget(region_container)
        
        # Local Mode indicator
        local_mode_label = QLabel("🔧 Local")
        local_mode_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.WARNING};
            background: {Colors.WARNING_BG};
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid {Colors.WARNING};
        """)
        local_mode_label.setToolTip("Running in local simulation mode")
        layout.addWidget(local_mode_label)
        
        # Region selector
        region_label = QLabel("Region:")
        region_label.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
            padding-right: 8px;
        """)
        layout.addWidget(region_label)
        
        self.region_combo = QComboBox()
        self.region_combo.addItems([
            "🌍 us-east-1",
            "🌏 ap-southeast-1", 
            "🌎 eu-west-1"
        ])
        self.region_combo.setStyleSheet(f"""
            QComboBox {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: {Fonts.BODY};
                min-width: 160px;
            }}
            QComboBox:hover {{
                background: {Colors.SECONDARY};
                border-color: {Colors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.TEXT_SECONDARY};
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.ACCENT};
                selection-color: white;
                border: 1px solid {Colors.BORDER};
                padding: 4px;
            }}
        """)
        layout.addWidget(self.region_combo)
        
        return bar
    
    def _create_status_bar(self):
        """Create bottom status bar"""
        status_bar = QStatusBar()
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
                font-size: 11px;
                color: #555;
            }
        """)
        
        # Status indicators
        status_text = "🟢 CloudSim Running  •  Mode: Local  •  No cloud credentials required"
        status_bar.showMessage(status_text)
        
        self.setStatusBar(status_bar)
        
    def switch_view(self, view_name):
        """Switch to a different view"""
        # Clear current content
        self.clear_content_area()
        
        # Add new view
        if view_name in self.views:
            self.current_view = self.views[view_name]
            self.content_area.addWidget(self.current_view)
        
        # Update sidebar
        self.sidebar.set_active_button(view_name)
    
    def navigate_to_service(self, service_key: str):
        """Navigate to a specific service view"""
        service_map = {
            "compute": "Compute",
            "storage": "Storage",
            "database": "Database",
            "serverless": "Serverless"
        }
        
        view_name = service_map.get(service_key)
        if view_name:
            self.switch_view(view_name)
        
    def clear_content_area(self):
        """Remove all widgets from content area"""
        while self.content_area.count():
            item = self.content_area.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
    
    def resizeEvent(self, event):
        """Handle window resize to update notification position"""
        super().resizeEvent(event)
        if hasattr(self, 'notification_manager'):
            self.notification_manager._update_position()

