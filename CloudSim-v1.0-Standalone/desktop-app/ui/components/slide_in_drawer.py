"""
Slide-In Drawer Component - AWS Console-style resource details panel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QTabWidget, QTextEdit, QTableWidget,
    QTableWidgetItem
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont
from ui.design_system import Colors, Fonts, Spacing


class SlideInDrawer(QWidget):
    """
    AWS Console-style slide-in drawer for resource details
    
    Features:
    - Slides in from right side
    - Keeps list visible in background (with overlay)
    - Tabbed sections: Overview, Networking, IAM, Logs
    - Smooth animations
    - Close button and overlay click to dismiss
    """
    
    closed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resource_data = None
        self.init_ui()
        self.hide()  # Hidden by default
        
    def init_ui(self):
        """Initialize drawer UI"""
        # Drawer should float on top
        self.setWindowFlags(Qt.Widget)
        
        # Fixed width (AWS Console uses ~40-50% of screen)
        self.setFixedWidth(600)
        
        # Styling
        self.setStyleSheet(f"""
            SlideInDrawer {{
                background: {Colors.SURFACE};
                border-left: 1px solid {Colors.BORDER};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with close button
        header = self._create_header()
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(f"background: {Colors.BORDER}; max-height: 1px;")
        layout.addWidget(separator)
        
        # Tabbed content area
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {Colors.BACKGROUND};
            }}
            QTabBar::tab {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px 24px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.MEDIUM};
                border: none;
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                background: {Colors.BACKGROUND};
                color: {Colors.PRIMARY};
                border-bottom: 2px solid {Colors.PRIMARY};
                font-weight: {Fonts.BOLD};
            }}
            QTabBar::tab:hover {{
                color: {Colors.PRIMARY_LIGHT};
            }}
        """)
        
        # Create tab sections
        self.overview_tab = self._create_overview_tab()
        self.networking_tab = self._create_networking_tab()
        self.iam_tab = self._create_iam_tab()
        self.logs_tab = self._create_logs_tab()
        
        self.tabs.addTab(self.overview_tab, "Overview")
        self.tabs.addTab(self.networking_tab, "Networking")
        self.tabs.addTab(self.iam_tab, "IAM")
        self.tabs.addTab(self.logs_tab, "Logs")
        
        layout.addWidget(self.tabs)
    
    def _create_header(self):
        """Create drawer header with title and close button"""
        header = QWidget()
        header.setStyleSheet(f"background: {Colors.SURFACE}; padding: 16px 20px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(12)
        
        # Resource icon and title
        self.title_label = QLabel("Resource Details")
        self.title_label.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {Colors.DANGER};
                color: white;
                border-color: {Colors.DANGER};
            }}
        """)
        close_btn.clicked.connect(self.close_drawer)
        header_layout.addWidget(close_btn)
        
        return header
    
    def _create_overview_tab(self):
        """Create Overview tab content"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Details container
        self.overview_container = QVBoxLayout()
        layout.addLayout(self.overview_container)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll
    
    def _create_networking_tab(self):
        """Create Networking tab content"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        self.networking_container = QVBoxLayout()
        layout.addLayout(self.networking_container)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll
    
    def _create_iam_tab(self):
        """Create IAM tab content"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        self.iam_container = QVBoxLayout()
        layout.addLayout(self.iam_container)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll
    
    def _create_logs_tab(self):
        """Create Logs tab content"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Logs text area
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
        """)
        layout.addWidget(self.logs_text)
        
        scroll.setWidget(content)
        return scroll
    
    def _create_detail_section(self, title, items):
        """Create a detail section with key-value pairs"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        
        section_layout = QVBoxLayout(section)
        section_layout.setSpacing(12)
        
        # Section title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: {Fonts.SUBHEADING};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: 8px;
        """)
        section_layout.addWidget(title_label)
        
        # Key-value pairs
        for key, value in items.items():
            row = QHBoxLayout()
            
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet(f"""
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.BODY};
                font-weight: {Fonts.MEDIUM};
                min-width: 120px;
            """)
            row.addWidget(key_label)
            
            value_label = QLabel(str(value))
            value_label.setStyleSheet(f"""
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
            """)
            value_label.setWordWrap(True)
            row.addWidget(value_label, 1)
            
            section_layout.addLayout(row)
        
        return section
    
    def show_resource(self, resource, resource_type="instance"):
        """Show resource details in drawer"""
        self.resource_data = resource
        self.resource_type = resource_type
        
        # Update title
        if resource_type == "instance":
            self.title_label.setText(f"🖥️  Instance: {resource.name}")
        elif resource_type == "volume":
            self.title_label.setText(f"💾  Volume: {resource.name}")
        elif resource_type == "bucket":
            self.title_label.setText(f"📦  Bucket: {resource.name}")
        
        # Clear existing content
        self._clear_container(self.overview_container)
        self._clear_container(self.networking_container)
        self._clear_container(self.iam_container)
        
        # Populate Overview tab
        if resource_type == "instance":
            self._populate_instance_overview(resource)
            self._populate_instance_networking(resource)
            self._populate_instance_iam(resource)
            self._populate_instance_logs(resource)
        
        # Show drawer with animation
        self.slide_in()
    
    def _populate_instance_overview(self, instance):
        """Populate overview tab for instance"""
        # Basic details
        basic_details = {
            "Instance ID": instance.id,
            "Status": instance.status,
            "Instance Type": f"{instance.cpu} vCPU, {instance.memory} MB RAM",
            "Image": instance.image,
            "Region": instance.region,
            "Created": instance.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "Owner": instance.owner
        }
        section1 = self._create_detail_section("Instance Details", basic_details)
        self.overview_container.addWidget(section1)
        
        # Tags
        if hasattr(instance, 'tags') and instance.tags:
            tags_section = self._create_detail_section("Tags", instance.tags)
            self.overview_container.addWidget(tags_section)
    
    def _populate_instance_networking(self, instance):
        """Populate networking tab for instance"""
        networking_details = {
            "Private IP": getattr(instance, 'private_ip', 'N/A'),
            "Public IP": getattr(instance, 'public_ip', 'N/A'),
            "VPC": getattr(instance, 'vpc_id', 'Default VPC'),
            "Subnet": getattr(instance, 'subnet_id', 'N/A'),
            "Security Groups": getattr(instance, 'security_groups', 'default')
        }
        section = self._create_detail_section("Network Configuration", networking_details)
        self.networking_container.addWidget(section)
    
    def _populate_instance_iam(self, instance):
        """Populate IAM tab for instance"""
        iam_details = {
            "IAM Role": getattr(instance, 'iam_role', 'None'),
            "Instance Profile": getattr(instance, 'instance_profile', 'N/A'),
            "Owner": instance.owner,
            "Permissions": "Full Control"
        }
        section = self._create_detail_section("IAM & Permissions", iam_details)
        self.iam_container.addWidget(section)
    
    def _populate_instance_logs(self, instance):
        """Populate logs tab for instance"""
        # Simulated logs
        logs = f"""[{instance.created_at.strftime("%Y-%m-%d %H:%M:%S")}] Instance {instance.id} created
[{instance.created_at.strftime("%Y-%m-%d %H:%M:%S")}] Status: PENDING
[{instance.created_at.strftime("%Y-%m-%d %H:%M:%S")}] Allocating resources...
[{instance.created_at.strftime("%Y-%m-%d %H:%M:%S")}] Starting instance...
[{instance.created_at.strftime("%Y-%m-%d %H:%M:%S")}] Status: {instance.status}
[{instance.created_at.strftime("%Y-%m-%d %H:%M:%S")}] Instance ready for use
"""
        self.logs_text.setText(logs)
    
    def _clear_container(self, layout):
        """Clear all widgets from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def slide_in(self):
        """Animate drawer sliding in from right"""
        self.show()
        
        # Position drawer off-screen to the right
        parent_width = self.parent().width() if self.parent() else 800
        self.setGeometry(parent_width, 0, 600, self.parent().height() if self.parent() else 600)
        
        # Animate sliding in
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(300)
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos().translated(-600, 0))
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
    
    def close_drawer(self):
        """Animate drawer sliding out and close"""
        self.animation = QPropertyAnimation(self, b"pos")
        self.animation.setDuration(250)
        self.animation.setStartValue(self.pos())
        self.animation.setEndValue(self.pos().translated(600, 0))
        self.animation.setEasingCurve(QEasingCurve.InCubic)
        self.animation.finished.connect(self.hide)
        self.animation.finished.connect(self.closed.emit)
        self.animation.start()
