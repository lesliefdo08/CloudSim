"""
Demo: Slide-in Drawer Implementation
Shows AWS Console-style resource detail drawer
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt
from ui.components.slide_in_drawer import SlideInDrawer
from ui.design_system import Colors, Fonts, Spacing


class DrawerDemo(QMainWindow):
    """Demo window to test slide-in drawer"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slide-in Drawer Demo")
        self.setMinimumSize(1200, 800)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize demo UI"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("AWS Console-Style Slide-in Drawer")
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("Click buttons below to simulate clicking on resources")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: 20px;
        """)
        layout.addWidget(subtitle)
        
        # Demo instance buttons
        instances = [
            {
                "id": "i-abc123",
                "name": "web-server-prod",
                "state": "running",
                "type": "t2.micro",
                "image": "ami-ubuntu-20.04",
                "region": "us-east-1",
                "created": "2024-01-15 10:30:00",
                "owner": "admin",
                "tags": {"Environment": "Production", "Team": "DevOps"},
                "private_ip": "10.0.1.15",
                "public_ip": "54.123.45.67",
                "vpc": "vpc-12345",
                "subnet": "subnet-abc123",
                "security_groups": ["sg-web", "sg-ssh"],
                "iam_role": "EC2-WebServer-Role",
                "iam_profile": "web-server-profile"
            },
            {
                "id": "i-def456",
                "name": "database-prod",
                "state": "stopped",
                "type": "r5.large",
                "image": "ami-postgres-14",
                "region": "us-west-2",
                "created": "2024-02-20 14:15:00",
                "owner": "dba-team",
                "tags": {"Environment": "Production", "Database": "PostgreSQL"},
                "private_ip": "10.0.2.30",
                "public_ip": "None",
                "vpc": "vpc-67890",
                "subnet": "subnet-def456",
                "security_groups": ["sg-database"],
                "iam_role": "EC2-Database-Role",
                "iam_profile": "db-backup-profile"
            },
            {
                "id": "i-ghi789",
                "name": "analytics-worker",
                "state": "running",
                "type": "c5.xlarge",
                "image": "ami-python-3.10",
                "region": "eu-west-1",
                "created": "2024-03-10 09:00:00",
                "owner": "data-team",
                "tags": {"Environment": "Staging", "Purpose": "Analytics"},
                "private_ip": "10.0.3.45",
                "public_ip": "34.56.78.90",
                "vpc": "vpc-analytics",
                "subnet": "subnet-ghi789",
                "security_groups": ["sg-workers", "sg-ssh"],
                "iam_role": "EC2-Analytics-Role",
                "iam_profile": "analytics-profile"
            }
        ]
        
        for inst in instances:
            btn = QPushButton(f"🖥️ {inst['name']} ({inst['state']})")
            btn.setFixedHeight(60)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {Colors.CARD}, stop:1 #1a2535);
                    border: 1px solid {Colors.BORDER};
                    border-radius: 8px;
                    color: {Colors.TEXT_PRIMARY};
                    font-size: {Fonts.BODY};
                    font-weight: {Fonts.SEMIBOLD};
                    text-align: left;
                    padding: 0 20px;
                }}
                QPushButton:hover {{
                    border-color: {Colors.ACCENT};
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 {Colors.SURFACE_HOVER}, stop:1 #1f2d42);
                }}
                QPushButton:pressed {{
                    background: {Colors.SURFACE};
                }}
            """)
            btn.clicked.connect(lambda checked, i=inst: self.show_resource(i))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Create drawer (overlay on top)
        self.drawer = SlideInDrawer(self)
        self.drawer.hide()
        
        # Apply dark theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background: {Colors.BACKGROUND};
            }}
            QWidget {{
                background: {Colors.BACKGROUND};
            }}
        """)
    
    def show_resource(self, instance):
        """Show resource in drawer"""
        self.drawer.show_resource(instance, "instance")
    
    def resizeEvent(self, event):
        """Position drawer at right edge"""
        super().resizeEvent(event)
        if hasattr(self, 'drawer'):
            drawer_width = 600
            self.drawer.setGeometry(
                self.width() - drawer_width,
                0,
                drawer_width,
                self.height()
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set dark theme globally
    app.setStyleSheet(f"""
        * {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
    """)
    
    demo = DrawerDemo()
    demo.show()
    
    sys.exit(app.exec())
