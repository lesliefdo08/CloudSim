"""
Resource Detail Page Component - Tabbed detail view for resources
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTabWidget, QFrame, QScrollArea,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from typing import Dict, Any, List, Optional


class DetailSection(QFrame):
    """A section in the detail page showing key-value pairs"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.init_ui()
        
    def init_ui(self):
        """Initialize section UI"""
        from ui.design_system import Colors
        self.setStyleSheet(f"""
            DetailSection {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            DetailSection:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 14px;
            color: #f8fafc;
            margin-bottom: 4px;
        """)
        layout.addWidget(title_label)
        
        # Content grid
        self.content_grid = QGridLayout()
        self.content_grid.setSpacing(8)
        self.content_grid.setColumnStretch(1, 1)
        layout.addLayout(self.content_grid)
    
    def add_field(self, label: str, value: str, row: int):
        """Add a field to the section"""
        # Label
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
            font-weight: 500;
        """)
        self.content_grid.addWidget(label_widget, row, 0, Qt.AlignTop)
        
        # Value
        value_widget = QLabel(value)
        value_widget.setStyleSheet("""
            font-size: 12px;
            color: #e2e8f0;
        """)
        value_widget.setWordWrap(True)
        value_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.content_grid.addWidget(value_widget, row, 1)


class OverviewTab(QWidget):
    """Overview tab showing basic resource information"""
    
    def __init__(self, resource_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.resource_data = resource_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize overview tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: #0f172a;
                border: none;
            }
        """)
        
        content = QWidget()
        content.setStyleSheet("background: #0f172a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        
        # Basic information section
        basic_section = DetailSection("Basic Information")
        for i, (key, value) in enumerate(self.resource_data.get("basic", {}).items()):
            basic_section.add_field(key, str(value), i)
        content_layout.addWidget(basic_section)
        
        # Status section
        if "status" in self.resource_data:
            status_section = DetailSection("Status & Health")
            for i, (key, value) in enumerate(self.resource_data["status"].items()):
                status_section.add_field(key, str(value), i)
            content_layout.addWidget(status_section)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)


class ConfigurationTab(QWidget):
    """Configuration tab showing resource settings"""
    
    def __init__(self, config_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config_data = config_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize configuration tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: #0f172a; border: none; }")
        
        content = QWidget()
        content.setStyleSheet("background: #0f172a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)
        
        # Configuration sections
        for section_name, section_data in self.config_data.items():
            section = DetailSection(section_name)
            for i, (key, value) in enumerate(section_data.items()):
                section.add_field(key, str(value), i)
            content_layout.addWidget(section)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)


class MonitoringTab(QWidget):
    """Monitoring tab showing metrics and usage"""
    
    def __init__(self, metrics: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.metrics = metrics
        self.init_ui()
        
    def init_ui(self):
        """Initialize monitoring tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Metrics section
        metrics_section = DetailSection("Resource Metrics")
        for i, (key, value) in enumerate(self.metrics.items()):
            metrics_section.add_field(key, str(value), i)
        layout.addWidget(metrics_section)
        
        # Placeholder for future charts
        placeholder = QLabel("📊 Detailed metrics and charts coming soon...")
        placeholder.setStyleSheet("""
            font-size: 13px;
            color: #64748b;
            padding: 40px;
        """)
        placeholder.setAlignment(Qt.AlignCenter)
        layout.addWidget(placeholder)
        
        layout.addStretch()


class PermissionsTab(QWidget):
    """Permissions tab showing IAM policies and access control"""
    
    def __init__(self, permissions: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.permissions = permissions
        self.init_ui()
        
    def init_ui(self):
        """Initialize permissions tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Owner section
        owner_section = DetailSection("Resource Owner")
        owner_section.add_field("Owner", self.permissions.get("owner", "N/A"), 0)
        owner_section.add_field("Created At", self.permissions.get("created_at", "N/A"), 1)
        layout.addWidget(owner_section)
        
        # Access control section
        if "policies" in self.permissions:
            access_section = DetailSection("Access Control")
            access_section.add_field("IAM Policies", ", ".join(self.permissions["policies"]), 0)
            layout.addWidget(access_section)
        
        # ARN section
        if "arn" in self.permissions:
            arn_section = DetailSection("Resource Identifier")
            arn_section.add_field("ARN", self.permissions["arn"], 0)
            layout.addWidget(arn_section)
        
        layout.addStretch()


class TagsTab(QWidget):
    """Tags tab for managing resource tags"""
    
    edit_tags = Signal()
    
    def __init__(self, tags: Dict[str, str], parent=None):
        super().__init__(parent)
        self.tags = tags
        self.init_ui()
        
    def init_ui(self):
        """Initialize tags tab"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Header with edit button
        header_layout = QHBoxLayout()
        
        title = QLabel("Resource Tags")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        edit_btn = QPushButton("Edit Tags")
        edit_btn.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: #f8fafc;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #3b82f6;
            }
        """)
        edit_btn.clicked.connect(self.edit_tags.emit)
        header_layout.addWidget(edit_btn)
        
        layout.addLayout(header_layout)
        
        # Tags table
        if self.tags:
            self.tags_table = QTableWidget()
            self.tags_table.setColumnCount(2)
            self.tags_table.setHorizontalHeaderLabels(["Key", "Value"])
            self.tags_table.horizontalHeader().setStretchLastSection(True)
            self.tags_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.tags_table.verticalHeader().setVisible(False)
            self.tags_table.setRowCount(len(self.tags))
            
            for i, (key, value) in enumerate(self.tags.items()):
                self.tags_table.setItem(i, 0, QTableWidgetItem(key))
                self.tags_table.setItem(i, 1, QTableWidgetItem(value))
            
            self.tags_table.setStyleSheet("""
                QTableWidget {
                    background: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    color: #e2e8f0;
                    font-size: 12px;
                }
                QTableWidget::item {
                    padding: 8px;
                    border: none;
                }
                QHeaderView::section {
                    background: #0f172a;
                    color: #94a3b8;
                    padding: 8px;
                    border: none;
                    font-weight: 600;
                }
            """)
            
            layout.addWidget(self.tags_table)
        else:
            no_tags = QLabel("🏷️ No tags assigned to this resource")
            no_tags.setStyleSheet("""
                font-size: 13px;
                color: #64748b;
                padding: 40px;
            """)
            no_tags.setAlignment(Qt.AlignCenter)
            layout.addWidget(no_tags)
        
        layout.addStretch()


class ResourceDetailPage(QWidget):
    """Reusable resource detail page with tabs"""
    
    back_clicked = Signal()
    
    def __init__(self, 
                 resource_type: str,
                 resource_name: str,
                 resource_data: Dict[str, Any],
                 parent=None):
        super().__init__(parent)
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.resource_data = resource_data
        self.init_ui()
        
    def init_ui(self):
        """Initialize resource detail page"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Content container
        content = QWidget()
        content.setStyleSheet("background: #0f172a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(self.back_clicked.emit)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.ACCENT};
                border: none;
                padding: 8px 12px;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
                text-decoration: underline;
            }}
        """)
        header_layout.addWidget(back_btn)
        
        header_layout.addStretch()
        
        content_layout.addLayout(header_layout)
        
        # Resource title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        resource_type_label = QLabel(self.resource_type)
        resource_type_label.setStyleSheet("""
            font-size: 13px;
            color: #94a3b8;
        """)
        title_layout.addWidget(resource_type_label)
        
        resource_name_label = QLabel(self.resource_name)
        resource_name_label.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #f8fafc;
        """)
        title_layout.addWidget(resource_name_label)
        
        content_layout.addLayout(title_layout)
        
        # Tabs with modern indigo theme
        from ui.design_system import Colors
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: {Colors.CARD};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px 24px;
                margin-right: 4px;
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border-bottom: 3px solid {Colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                background: {Colors.SURFACE_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        
        # Add tabs
        self.tabs.addTab(
            OverviewTab(self.resource_data.get("overview", {})),
            "Overview"
        )
        
        self.tabs.addTab(
            ConfigurationTab(self.resource_data.get("configuration", {})),
            "Configuration"
        )
        
        # Add Storage tab if storage data exists (for EC2 instances)
        if "storage" in self.resource_data:
            self.tabs.addTab(
                ConfigurationTab(self.resource_data.get("storage", {})),
                "Storage"
            )
        
        self.tabs.addTab(
            MonitoringTab(self.resource_data.get("monitoring", {})),
            "Monitoring"
        )
        
        self.tabs.addTab(
            PermissionsTab(self.resource_data.get("permissions", {})),
            "Permissions"
        )
        
        self.tags_tab = TagsTab(self.resource_data.get("tags", {}))
        self.tabs.addTab(self.tags_tab, "Tags")
        
        content_layout.addWidget(self.tabs)
        
        layout.addWidget(content)
