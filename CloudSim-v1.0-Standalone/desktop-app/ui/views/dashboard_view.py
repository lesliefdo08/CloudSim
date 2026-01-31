"""
Dashboard View - AWS-style workflow-driven console overview
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QGridLayout, QPushButton, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from pathlib import Path
from datetime import datetime
from ui.design_system import Colors, Fonts, Spacing
from services.compute_service import ComputeService
from services.storage_service import StorageService
from services.database_service import DatabaseService
from services.serverless_service import ServerlessService
from core.events import EventBus
from core.region import RegionRegistry
from core.iam import IAMManager
from ui.components.footer import Footer


class ResourcePanel(QFrame):
    """AWS-style resource panel showing region-scoped counts"""
    
    navigate_to_service = Signal(str)  # Signal to navigate to service
    
    def __init__(self, title: str, region: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.region = region
        self.resources = {}
        self.init_ui()
        
    def init_ui(self):
        """Initialize resource panel UI with modern styling"""
        from ui.design_system import Colors
        self.setStyleSheet(f"""
            ResourcePanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            ResourcePanel:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Header with region
        header_layout = QHBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        header_layout.addWidget(title_label)
        
        region_badge = QLabel(f"🌍 {self.region}")
        region_badge.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
            background: #0f172a;
            padding: 6px 12px;
            border-radius: 8px;
        """)
        header_layout.addWidget(region_badge)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Resource grid
        self.resource_grid = QGridLayout()
        self.resource_grid.setSpacing(8)
        self.resource_grid.setContentsMargins(0, 4, 0, 0)
        layout.addLayout(self.resource_grid)
        
        # Sparkline container (for trend charts)
        self.sparkline_container = QVBoxLayout()
        self.sparkline_container.setSpacing(8)
        self.sparkline_container.setContentsMargins(0, 8, 0, 0)
        layout.addLayout(self.sparkline_container)
    
    def add_resource(self, name: str, icon: str, count: int, service_key: str):
        """Add a resource type to the panel"""
        self.resources[name] = {"count": count, "service_key": service_key}
        self.refresh_display()
    
    def refresh_display(self):
        """Refresh the resource display"""
        # Clear existing
        while self.resource_grid.count():
            child = self.resource_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add resources
        row = 0
        for name, data in self.resources.items():
            # Resource row
            resource_layout = QHBoxLayout()
            
            # Name and icon
            name_label = QLabel(f"{data.get('icon', '📦')} {name}")
            name_label.setStyleSheet("""
                font-size: 13px;
                color: #cbd5e1;
            """)
            resource_layout.addWidget(name_label)
            
            resource_layout.addStretch()
            
            # Count badge with indigo theme
            from ui.design_system import Colors
            count_label = QLabel(str(data["count"]))
            count_label.setStyleSheet(f"""
                font-size: 14px;
                font-weight: 600;
                color: {Colors.ACCENT};
                background: rgba(99, 102, 241, 0.15);
                padding: 2px 10px;
                border-radius: 6px;
                min-width: 30px;
            """)
            count_label.setAlignment(Qt.AlignCenter)
            resource_layout.addWidget(count_label)
            
            # View button
            if data["count"] > 0:
                view_btn = QPushButton("View →")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #60a5fa;
                        border: none;
                        padding: 2px 8px;
                        font-size: 12px;
                        text-align: right;
                    }
                    QPushButton:hover {
                        color: #93c5fd;
                        text-decoration: underline;
                    }
                """)
                view_btn.clicked.connect(lambda checked, k=data["service_key"]: self.navigate_to_service.emit(k))
                resource_layout.addWidget(view_btn)
            
            # Create container
            resource_widget = QWidget()
            resource_widget.setLayout(resource_layout)
            self.resource_grid.addWidget(resource_widget, row, 0)
            row += 1


class ActivityPanel(QFrame):
    """CloudTrail-style recent activity panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize activity panel UI with modern styling"""
        from ui.design_system import Colors
        self.setStyleSheet(f"""
            ActivityPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            ActivityPanel:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 Recent Activity")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # CloudTrail badge
        badge = QLabel("CloudTrail-style")
        badge.setStyleSheet("""
            font-size: 11px;
            color: #64748b;
            background: #0f172a;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        header_layout.addWidget(badge)
        
        layout.addLayout(header_layout)
        
        # Activity table with modern styling
        from ui.design_system import Styles
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(4)
        self.activity_table.setHorizontalHeaderLabels(["Time", "User", "Action", "Resource"])
        self.activity_table.horizontalHeader().setStretchLastSection(True)
        self.activity_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.activity_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setSelectionMode(QTableWidget.NoSelection)
        self.activity_table.setShowGrid(False)
        self.activity_table.setMaximumHeight(200)
        self.activity_table.setStyleSheet(Styles.table())
        
        layout.addWidget(self.activity_table)
        
        # Ghost timeline entries for empty state
        from ui.components.sparkline import GhostTimelineEntry
        self.ghost_entries_container = QWidget()
        ghost_layout = QVBoxLayout(self.ghost_entries_container)
        ghost_layout.setContentsMargins(0, 8, 0, 8)
        ghost_layout.setSpacing(8)
        
        # Create 3 ghost entries
        for _ in range(3):
            ghost_entry = GhostTimelineEntry("Awaiting activity…")
            ghost_layout.addWidget(ghost_entry)
        
        self.ghost_entries_container.hide()
        layout.addWidget(self.ghost_entries_container)
    
    def update_activities(self, events):
        """Update activity table with recent events"""
        if not events:
            self.activity_table.hide()
            self.ghost_entries_container.show()
            return
        
        self.activity_table.show()
        self.ghost_entries_container.hide()
        
        self.activity_table.setRowCount(min(len(events), 10))  # Show last 10
        
        for i, event in enumerate(events[:10]):
            # Time
            time_str = event.timestamp.strftime("%H:%M:%S")
            time_item = QTableWidgetItem(time_str)
            time_item.setForeground(Qt.GlobalColor.gray)
            self.activity_table.setItem(i, 0, time_item)
            
            # User
            user = event.username or "system"
            user_item = QTableWidgetItem(user)
            user_item.setForeground(Qt.GlobalColor.cyan)
            self.activity_table.setItem(i, 1, user_item)
            
            # Action (formatted)
            action_parts = event.event_type.value.split('.')
            action = f"{action_parts[0].upper()}: {action_parts[-1].title()}"
            action_item = QTableWidgetItem(action)
            self.activity_table.setItem(i, 2, action_item)
            
            # Resource
            resource = event.resource_id or "N/A"
            region_info = f"({event.region})" if event.region else ""
            resource_item = QTableWidgetItem(f"{resource} {region_info}")
            resource_item.setForeground(Qt.GlobalColor.yellow)
            self.activity_table.setItem(i, 3, resource_item)


class HealthPanel(QFrame):
    """System health indicators panel"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize health panel UI with modern styling"""
        from ui.design_system import Colors
        self.setStyleSheet(f"""
            HealthPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            HealthPanel:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Header
        title = QLabel("🏥 System Health")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        layout.addWidget(title)
        
        # Health indicators
        self.health_grid = QVBoxLayout()
        self.health_grid.setSpacing(8)
        layout.addLayout(self.health_grid)
    
    def add_health_indicator(self, name: str, status: str, status_color: str):
        """Add a health indicator"""
        indicator_layout = QHBoxLayout()
        
        # Status dot
        status_dot = QLabel("●")
        status_dot.setStyleSheet(f"""
            font-size: 16px;
            color: {status_color};
        """)
        indicator_layout.addWidget(status_dot)
        
        # Name
        name_label = QLabel(name)
        name_label.setStyleSheet("""
            font-size: 13px;
            color: #cbd5e1;
        """)
        indicator_layout.addWidget(name_label)
        
        indicator_layout.addStretch()
        
        # Status
        status_label = QLabel(status)
        status_label.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
        """)
        indicator_layout.addWidget(status_label)
        
        # Container
        indicator_widget = QWidget()
        indicator_widget.setLayout(indicator_layout)
        self.health_grid.addWidget(indicator_widget)


class QuickActionsPanel(QFrame):
    """Context-aware quick actions panel that adapts to infrastructure state"""
    
    create_resource = Signal(str)  # Signal to create resource
    start_stopped_instances = Signal()  # Signal to start stopped instances
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.actions_container = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize quick actions panel UI with modern styling"""
        from ui.design_system import Colors
        self.setStyleSheet(f"""
            QuickActionsPanel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            QuickActionsPanel:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 16, 20, 16)
        self.main_layout.setSpacing(12)
        
        # Header
        title = QLabel("⚡ Quick Actions")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        self.main_layout.addWidget(title)
        
        # Container for dynamic actions
        self.actions_container = QVBoxLayout()
        self.actions_container.setSpacing(8)
        self.main_layout.addLayout(self.actions_container)
    
    def update_actions(self, instances=None, buckets=None, databases=None, functions=None):
        """Update actions based on current infrastructure state"""
        # Clear existing actions
        while self.actions_container.count():
            child = self.actions_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        instances = instances or []
        buckets = buckets or []
        databases = databases or []
        functions = functions or []
        
        # Analyze infrastructure state
        has_instances = len(instances) > 0
        stopped_instances = [i for i in instances if i.status == "STOPPED"]
        has_stopped = len(stopped_instances) > 0
        has_buckets = len(buckets) > 0
        has_databases = len(databases) > 0
        
        # --- COMPUTE SECTION ---
        compute_section = self._create_section_label("🖥️ Compute")
        self.actions_container.addWidget(compute_section)
        
        if not has_instances:
            # No instances - primary CTA
            btn = self._create_action_button(
                "Launch your first instance",
                "🚀",
                "compute",
                is_primary=True
            )
            btn.clicked.connect(lambda: self.create_resource.emit("compute"))
            self.actions_container.addWidget(btn)
        elif has_stopped:
            # Has stopped instances - contextual action
            btn = self._create_action_button(
                f"Start {len(stopped_instances)} stopped instance{'s' if len(stopped_instances) != 1 else ''}",
                "▶️",
                "compute",
                is_primary=True
            )
            btn.clicked.connect(lambda: self.start_stopped_instances.emit())
            self.actions_container.addWidget(btn)
            
            # Secondary action - create more
            btn2 = self._create_action_button(
                "Launch new instance",
                "➕",
                "compute",
                is_primary=False
            )
            btn2.clicked.connect(lambda: self.create_resource.emit("compute"))
            self.actions_container.addWidget(btn2)
        else:
            # Has running instances - create more
            btn = self._create_action_button(
                "Launch new instance",
                "➕",
                "compute",
                is_primary=False
            )
            btn.clicked.connect(lambda: self.create_resource.emit("compute"))
            self.actions_container.addWidget(btn)
        
        # --- STORAGE SECTION ---
        storage_section = self._create_section_label("📦 Storage")
        self.actions_container.addWidget(storage_section)
        
        if not has_buckets:
            btn = self._create_action_button(
                "Create your first bucket",
                "🚀",
                "storage",
                is_primary=True
            )
            btn.clicked.connect(lambda: self.create_resource.emit("storage"))
            self.actions_container.addWidget(btn)
        else:
            btn = self._create_action_button(
                "Create new bucket",
                "➕",
                "storage",
                is_primary=False
            )
            btn.clicked.connect(lambda: self.create_resource.emit("storage"))
            self.actions_container.addWidget(btn)
        
        # --- DATABASE SECTION ---
        database_section = self._create_section_label("🗄️ Database")
        self.actions_container.addWidget(database_section)
        
        if not has_databases:
            btn = self._create_action_button(
                "Setup your first database",
                "🚀",
                "database",
                is_primary=True
            )
            btn.clicked.connect(lambda: self.create_resource.emit("database"))
            self.actions_container.addWidget(btn)
        else:
            btn = self._create_action_button(
                "Create new database",
                "➕",
                "database",
                is_primary=False
            )
            btn.clicked.connect(lambda: self.create_resource.emit("database"))
            self.actions_container.addWidget(btn)
    
    def _create_section_label(self, text: str) -> QLabel:
        """Create a section header label"""
        label = QLabel(text)
        label.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #94a3b8;
            margin-top: 8px;
            margin-bottom: 2px;
        """)
        return label
    
    def _create_action_button(self, text: str, icon: str, service_key: str, 
                             is_primary: bool = False) -> QPushButton:
        """Create an action button with appropriate styling and service-specific colors"""
        btn = QPushButton(f"{icon}  {text}")
        
        # Map service keys to their accent colors
        service_colors = {
            'compute': (Colors.COMPUTE, Colors.COMPUTE_HOVER),
            'storage': (Colors.STORAGE, Colors.STORAGE_HOVER),
            'database': (Colors.DATABASE, Colors.DATABASE_HOVER),
            'serverless': (Colors.SERVERLESS, Colors.SERVERLESS_HOVER),
        }
        
        base_color, hover_color = service_colors.get(service_key, (Colors.INFO, Colors.INFO))
        
        if is_primary:
            # Primary action - service-specific gradient
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {base_color}, stop:1 {base_color});
                    color: #f8fafc;
                    border: none;
                    padding: 12px 16px;
                    font-size: 13px;
                    font-weight: 600;
                    border-radius: 6px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {hover_color}, stop:1 {base_color});
                }}
                QPushButton:pressed {{
                    background: {base_color};
                }}
            """)
        else:
            # Secondary action - subtle style
            btn.setStyleSheet("""
                QPushButton {
                    background: #1e293b;
                    color: #cbd5e1;
                    border: 1px solid #334155;
                    padding: 10px 16px;
                    font-size: 13px;
                    font-weight: 500;
                    border-radius: 6px;
                    text-align: left;
                }
                QPushButton:hover {
                    background: #334155;
                    color: #f8fafc;
                    border: 1px solid #475569;
                }
                QPushButton:pressed {
                    background: #1e293b;
                }
            """)
        
        return btn


class DashboardView(QWidget):
    """AWS-style workflow-driven dashboard with region-scoped resources"""
    
    navigate_to_service = Signal(str)  # Signal to navigate to a service
    
    def __init__(self):
        super().__init__()
        self.compute_service = ComputeService()
        self.storage_service = StorageService()
        self.database_service = DatabaseService()
        self.serverless_service = ServerlessService()
        self.event_bus = EventBus()
        self.region_registry = RegionRegistry()
        self.iam = IAMManager()
        self.init_ui()
        self.refresh_dashboard()
        
    def init_ui(self):
        """Initialize workflow-driven dashboard UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background: #0f172a;
                border: none;
            }
            QScrollBar:vertical {
                background: #1e293b;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
        """)
        
        # Content widget
        content = QWidget()
        content.setStyleSheet("background: #0f172a;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)
        
        # Header section
        header_layout = QHBoxLayout()
        
        # Title and current user
        title_section = QVBoxLayout()
        title = QLabel("CloudSim Console")
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            color: #f8fafc;
            font-family: 'Segoe UI', sans-serif;
        """)
        title_section.addWidget(title)
        
        # User and region info (auth disabled - using local-user)
        current_region = self.region_registry.get_current_region()
        user_info = QLabel(f"👤 local-user | 🌍 {current_region.name}")
        user_info.setStyleSheet("""
            font-size: 13px;
            color: #94a3b8;
            margin-top: 4px;
        """)
        title_section.addWidget(user_info)
        
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("⟳ Refresh")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #334155;
                color: #f8fafc;
                border: 1px solid #f59e0b;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        content_layout.addLayout(header_layout)
        
        # Multi-region warning banner (soft warning for realism)
        warning_banner = self._create_multi_region_warning()
        content_layout.addWidget(warning_banner)
        
        # Main grid: left column (70%) and right column (30%)
        main_grid = QHBoxLayout()
        main_grid.setSpacing(16)
        
        # Left column - Resources and Activity
        left_column = QVBoxLayout()
        left_column.setSpacing(16)
        
        # Resource panel
        self.resource_panel = ResourcePanel(
            f"Resources in {current_region.code}",
            current_region.code
        )
        self.resource_panel.navigate_to_service.connect(self.on_navigate_to_service)
        left_column.addWidget(self.resource_panel)
        
        # Activity panel
        self.activity_panel = ActivityPanel()
        left_column.addWidget(self.activity_panel)
        
        # Insights panel (actionable recommendations)
        self.insights_panel = self.create_insights_panel()
        left_column.addWidget(self.insights_panel)
        
        # Health panel
        self.health_panel = HealthPanel()
        self.health_panel.add_health_indicator("IAM Service", "Operational", "#10b981")
        self.health_panel.add_health_indicator("Compute Service", "Operational", "#10b981")
        self.health_panel.add_health_indicator("Storage Service", "Operational", "#10b981")
        self.health_panel.add_health_indicator("Database Service", "Operational", "#10b981")
        self.health_panel.add_health_indicator("Serverless Service", "Operational", "#10b981")
        left_column.addWidget(self.health_panel)
        
        main_grid.addLayout(left_column, 70)
        
        # Right column - Quick Actions and Recommendations
        right_column = QVBoxLayout()
        right_column.setSpacing(16)
        
        # Quick actions
        self.quick_actions = QuickActionsPanel()
        self.quick_actions.create_resource.connect(self.on_create_resource)
        self.quick_actions.start_stopped_instances.connect(self.on_start_stopped_instances)
        right_column.addWidget(self.quick_actions)
        
        # Getting started panel
        getting_started = self.create_getting_started_panel()
        right_column.addWidget(getting_started)
        
        # Cost estimate panel
        cost_panel = self.create_cost_estimate_panel()
        right_column.addWidget(cost_panel)
        
        right_column.addStretch()
        
        main_grid.addLayout(right_column, 30)
        
        content_layout.addLayout(main_grid)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        # Add footer
        main_layout.addWidget(Footer())
    
    def create_getting_started_panel(self):
        """Create getting started panel"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        
        title = QLabel("💡 Getting Started")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        layout.addWidget(title)
        
        steps = [
            "1. Create compute instances (EC2-like)",
            "2. Store files in buckets (S3-like)",
            "3. Setup databases (RDS/DynamoDB)",
            "4. Deploy serverless functions",
            "5. Manage IAM users & policies"
        ]
        
        for step in steps:
            step_label = QLabel(step)
            step_label.setStyleSheet("""
                font-size: 12px;
                color: #94a3b8;
                padding: 2px 0;
            """)
            layout.addWidget(step_label)
        
        return panel
    
    def create_insights_panel(self):
        """Create insights panel with actionable recommendations"""
        from ui.design_system import Colors
        from ui.components.sparkline import InsightCard
        
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        
        # Header
        title = QLabel("💡 Insights & Recommendations")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        layout.addWidget(title)
        
        # Container for dynamic insights
        self.insights_container = QVBoxLayout()
        self.insights_container.setSpacing(8)
        layout.addLayout(self.insights_container)
        
        return panel
    
    def create_cost_estimate_panel(self):
        """Create cost estimate panel"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1e293b, stop:1 #1e3a4b);
                border: 1px solid #334155;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)
        
        title = QLabel("💰 Estimated Monthly Cost")
        title.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #f8fafc;
        """)
        layout.addWidget(title)
        
        cost = QLabel("$0.00")
        cost.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #10b981;
            margin: 8px 0;
        """)
        layout.addWidget(cost)
        
        note = QLabel("Simulated pricing for educational purposes")
        note.setStyleSheet("""
            font-size: 11px;
            color: #64748b;
        """)
        layout.addWidget(note)
        
        return panel
    
    def refresh_dashboard(self):
        """Refresh all dashboard data"""
        from ui.components.sparkline import SparklineChart, InsightCard
        
        # Get current region
        current_region = self.region_registry.get_current_region()
        
        # Update resource counts
        try:
            instances = self.compute_service.list_instances(region=current_region.code)
            buckets = self.storage_service.list_buckets(region=current_region.code)
            databases = self.database_service.list_databases(region=current_region.code)
            functions = self.serverless_service.list_functions(region=current_region.code)
            
            # Update resource panel
            self.resource_panel.add_resource("EC2 Instances", "🖥️", len(instances), "compute")
            self.resource_panel.add_resource("S3 Buckets", "📦", len(buckets), "storage")
            self.resource_panel.add_resource("RDS Databases", "🗄️", len(databases), "database")
            self.resource_panel.add_resource("Lambda Functions", "⚡", len(functions), "serverless")
            
            # Clear existing sparklines
            while self.resource_panel.sparkline_container.count():
                child = self.resource_panel.sparkline_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
            
            # Add sparkline for instance count trend (simulated data)
            import random
            instance_trend_data = [len(instances) + random.randint(-2, 2) for _ in range(10)]
            instance_sparkline_label = QLabel("Instance count trend (7 days):")
            instance_sparkline_label.setStyleSheet("""
                font-size: 11px;
                color: #94a3b8;
                margin-top: 8px;
            """)
            self.resource_panel.sparkline_container.addWidget(instance_sparkline_label)
            
            instance_sparkline = SparklineChart(instance_trend_data)
            self.resource_panel.sparkline_container.addWidget(instance_sparkline)
            
            # Add sparkline for storage usage trend (simulated data)
            storage_trend_data = [len(buckets) * 100 + random.randint(-20, 30) for _ in range(10)]
            storage_sparkline_label = QLabel("Storage usage trend (7 days):")
            storage_sparkline_label.setStyleSheet("""
                font-size: 11px;
                color: #94a3b8;
                margin-top: 4px;
            """)
            self.resource_panel.sparkline_container.addWidget(storage_sparkline_label)
            
            storage_sparkline = SparklineChart(storage_trend_data, color="#3b82f6")
            self.resource_panel.sparkline_container.addWidget(storage_sparkline)
            
            # Generate insights based on resource analysis
            self._update_insights(instances, buckets, databases, functions)
            
            # Update context-aware quick actions
            self.quick_actions.update_actions(instances, buckets, databases, functions)
            
        except PermissionError:
            # User may not have list permissions
            pass
        
        # Update recent activity
        recent_events = self.event_bus.get_events(limit=10)
        self.activity_panel.update_activities(recent_events)
    
    def on_navigate_to_service(self, service_key: str):
        """Handle navigation to service"""
        self.navigate_to_service.emit(service_key)
    
    def _update_insights(self, instances, buckets, databases, functions):
        """Update insights panel with actionable recommendations"""
        from ui.components.sparkline import InsightCard
        
        # Clear existing insights
        while self.insights_container.count():
            child = self.insights_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Analyze stopped instances
        stopped_instances = [i for i in instances if i.status == "STOPPED"]
        if len(stopped_instances) > 0:
            stopped_insight = InsightCard(
                icon="⚠️",
                title=f"{len(stopped_instances)} stopped instance{'s' if len(stopped_instances) != 1 else ''} — potential waste",
                message="Stopped instances still incur storage costs. Consider terminating unused instances.",
                severity="warning"
            )
            self.insights_container.addWidget(stopped_insight)
        
        # Analyze bucket usage
        if len(buckets) == 0 and len(instances) > 0:
            storage_insight = InsightCard(
                icon="📦",
                title="No S3 buckets created yet",
                message="Store backups, logs, and static assets in cost-effective S3 buckets.",
                severity="info"
            )
            self.insights_container.addWidget(storage_insight)
        
        # Analyze running instances (cost optimization)
        running_instances = [i for i in instances if i.status == "RUNNING"]
        if len(running_instances) > 5:
            cost_insight = InsightCard(
                icon="💰",
                title=f"{len(running_instances)} running instances detected",
                message="Review instance sizes and consider right-sizing to optimize costs.",
                severity="info"
            )
            self.insights_container.addWidget(cost_insight)
        
        # Encourage healthy practices
        if len(instances) == 0 and len(buckets) == 0 and len(databases) == 0:
            welcome_insight = InsightCard(
                icon="🚀",
                title="Start building",
                message="Launch an EC2 instance or create an S3 bucket to begin.",
                severity="success"
            )
            self.insights_container.addWidget(welcome_insight)
    
    def on_create_resource(self, service_key: str):
        """Handle quick create action"""
        # Navigate to service for creation
        self.navigate_to_service.emit(service_key)
    
    def on_start_stopped_instances(self):
        """Handle starting all stopped instances"""
        from ui.components.notifications import NotificationManager
        
        try:
            current_region = self.region_registry.get_current_region()
            instances = self.compute_service.list_instances(region=current_region.code)
            stopped_instances = [i for i in instances if i.status == "STOPPED"]
            
            if not stopped_instances:
                NotificationManager.show_info(
                    "No Stopped Instances",
                    "There are no stopped instances to start."
                )
                return
            
            # Show confirmation
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Start Stopped Instances")
            msg.setText(f"Start {len(stopped_instances)} stopped instance{'s' if len(stopped_instances) != 1 else ''}?")
            msg.setInformativeText("This will restart all stopped instances in the current region.")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.Yes)
            
            if msg.exec() == QMessageBox.Yes:
                NotificationManager.show_info(
                    "Starting Instances",
                    f"Starting {len(stopped_instances)} instance{'s' if len(stopped_instances) != 1 else ''}...",
                    duration=2000
                )
                
                # Start each instance
                success_count = 0
                for instance in stopped_instances:
                    try:
                        self.compute_service.start_instance(instance.id)
                        success_count += 1
                    except Exception as e:
                        print(f"Failed to start instance {instance.id}: {e}")
                
                # Show result
                if success_count > 0:
                    NotificationManager.show_success(
                        "Instances Started",
                        f"✓ {success_count} instance{'s' if success_count != 1 else ''} started successfully"
                    )
                    # Refresh dashboard
                    self.refresh_dashboard()
                else:
                    NotificationManager.show_error(
                        "Start Failed",
                        "Failed to start instances. Check permissions."
                    )
        except PermissionError:
            NotificationManager.show_error(
                "Permission Denied",
                "You don't have permission to start instances."
            )
        except Exception as e:
            NotificationManager.show_error(
                "Error",
                f"Failed to start instances: {str(e)}"
            )
    
    def _create_multi_region_warning(self) -> QFrame:
        """Create soft warning banner for multi-region resources"""
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: rgba(245, 158, 11, 0.08);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 8px;
                padding: 12px 16px;
            }
        """)
        
        layout = QHBoxLayout(banner)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)
        
        # Warning icon
        icon = QLabel("⚠️")
        icon.setStyleSheet("font-size: 18px;")
        layout.addWidget(icon)
        
        # Message
        message = QLabel(
            "<b>Resources detected in multiple regions</b><br>"
            "<span style='color: #94a3b8; font-size: 12px;'>"
            "You have resources across us-east-1, us-west-2, and eu-west-1. "
            "Switch regions to view all resources.</span>"
        )
        message.setStyleSheet("""
            color: #f59e0b;
            font-size: 13px;
        """)
        layout.addWidget(message)
        
        layout.addStretch()
        
        # Dismiss button
        dismiss_btn = QPushButton("✕")
        dismiss_btn.setFixedSize(24, 24)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #f59e0b;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #fbbf24;
            }
        """)
        dismiss_btn.clicked.connect(lambda: banner.hide())
        layout.addWidget(dismiss_btn)
        
        return banner


