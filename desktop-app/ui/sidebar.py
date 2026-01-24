"""
Sidebar - Refined navigation with collapsible sections and enhanced clarity
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame, 
    QHBoxLayout, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Signal, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QColor
from pathlib import Path
from ui.design_system import Colors


class CollapsibleSection(QWidget):
    """Collapsible section for grouping navigation items"""
    
    def __init__(self, title: str, icon: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.is_expanded = True
        self.items_container = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize collapsible section UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Section header (clickable to expand/collapse)
        self.header = QPushButton(f"{self.icon}  {self.title}")
        self.header.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                border: none;
                text-align: left;
                padding: 8px 20px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                color: #cbd5e1;
            }
        """)
        self.header.clicked.connect(self.toggle_expanded)
        layout.addWidget(self.header)
        
        # Container for section items
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(0)
        layout.addWidget(self.items_container)
    
    def add_item(self, widget):
        """Add an item to this section"""
        self.items_layout.addWidget(widget)
    
    def toggle_expanded(self):
        """Toggle section expanded/collapsed state"""
        self.is_expanded = not self.is_expanded
        self.items_container.setVisible(self.is_expanded)
        
        # Update header icon
        arrow = "▼" if self.is_expanded else "▶"
        self.header.setText(f"{arrow} {self.icon}  {self.title}")


class Sidebar(QWidget):
    """Refined sidebar with collapsible sections and enhanced visual hierarchy"""
    
    button_clicked = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.active_button = None
        self.resource_counts = {}
        self.count_labels = {}
        self.buttons = {}
        self.sections = {}
        # Map service names to their accent colors
        self.service_colors = {
            'Compute': Colors.COMPUTE,
            'Storage': Colors.STORAGE,
            'Database': Colors.DATABASE,
            'Serverless': Colors.SERVERLESS,
            'Volumes': Colors.COMPUTE,  # Part of compute
        }
        self.init_ui()
        self.connect_to_events()
        self.update_resource_counts()
        
    def init_ui(self):
        """Initialize refined sidebar UI"""
        self.setFixedWidth(240)
        style = (
            "QWidget {"
            "    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,"
            "        stop:0 #1e293b, stop:1 #0f172a);"
            "    border-right: 1px solid rgba(99, 102, 241, 0.2);"
            "}"
        )
        self.setStyleSheet(style)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Compact header
        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 20px 16px;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 24, 16, 16)
        header_layout.setSpacing(8)
        
        # Logo with enhanced styling
        logo_path = Path("logo.png")
        if logo_path.exists():
            logo_container = QWidget()
            logo_container.setStyleSheet("""
                background: transparent;
                border-radius: 8px;
            """)
            logo_container_layout = QVBoxLayout(logo_container)
            logo_container_layout.setContentsMargins(0, 0, 0, 0)
            
            logo_label = QLabel()
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaled(52, 52, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("""
                background: transparent;
                padding: 8px;
            """)
            logo_container_layout.addWidget(logo_label)
            header_layout.addWidget(logo_container)
        
        # Brand
        brand = QLabel("CloudSim")
        brand.setStyleSheet(
            "color: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 rgb(99, 102, 241), stop:1 rgb(129, 140, 248)); "
            "font-size: 20px; "
            "font-weight: 700; "
            "font-family: 'Inter', 'Segoe UI', sans-serif; "
            "background: transparent;"
        )
        brand.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(brand)
        
        version = QLabel("v1.0")
        version.setStyleSheet(
            "color: rgba(148, 163, 184, 0.8); "
            "font-size: 11px; "
            "background: transparent;"
        )
        version.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(version)
        
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "stop:0 transparent, stop:0.5 rgba(99, 102, 241, 0.3), stop:1 transparent); "
            "max-height: 1px; "
            "border: none;"
        )
        layout.addWidget(separator)
        
        layout.addSpacing(16)
        
        # Dashboard (ungrouped)
        dashboard_btn = self.create_nav_button("Dashboard", "📊", show_count=False)
        layout.addWidget(dashboard_btn)
        
        layout.addSpacing(8)
        
        # COMPUTE SECTION
        compute_section = CollapsibleSection("Compute", "▼", self)
        self.sections["Compute"] = compute_section
        
        compute_btn = self.create_nav_button("Compute", "🖥️", show_count=True)
        compute_section.add_item(compute_btn)
        
        volumes_btn = self.create_nav_button("Volumes", "💾", show_count=True)
        compute_section.add_item(volumes_btn)
        
        layout.addWidget(compute_section)
        
        # STORAGE SECTION
        storage_section = CollapsibleSection("Storage", "▼", self)
        self.sections["Storage"] = storage_section
        
        storage_btn = self.create_nav_button("Storage", "📦", show_count=True)
        storage_section.add_item(storage_btn)
        
        layout.addWidget(storage_section)
        
        # DATABASE SECTION
        database_section = CollapsibleSection("Database", "▼", self)
        self.sections["Database"] = database_section
        
        database_btn = self.create_nav_button("Database", "🗄️", show_count=True)
        database_section.add_item(database_btn)
        
        serverless_btn = self.create_nav_button("Serverless", "⚡", show_count=True)
        database_section.add_item(serverless_btn)
        
        layout.addWidget(database_section)
        
        layout.addSpacing(8)
        
        # IAM & Activity (ungrouped)
        iam_btn = self.create_nav_button("IAM", "👤", show_count=False)
        layout.addWidget(iam_btn)
        
        activity_btn = self.create_nav_button("Activity", "📋", show_count=False)
        layout.addWidget(activity_btn)
        
        layout.addStretch()
        
        # Footer
        footer = QLabel("© 2026")
        footer.setStyleSheet("color: rgb(71, 85, 105); font-size: 9px; padding: 12px;")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        
    def create_nav_button(self, text, icon, show_count=False):
        """Create navigation button with enhanced active state and inline count badges"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        button = QPushButton(f"{icon}  {text}")
        style = (
            "QPushButton {"
            "    background: transparent;"
            "    color: rgb(203, 213, 225);"
            "    border: none;"
            "    border-left: 3px solid transparent;"
            "    text-align: left;"
            "    padding: 12px 20px;"
            "    font-size: 14px;"
            "    font-weight: 500;"
            "    font-family: 'Inter', 'Segoe UI', sans-serif;"
            "}"
            "QPushButton:hover {"
            "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            "        stop:0 rgba(99, 102, 241, 0.15), stop:1 transparent);"
            "    color: rgb(165, 180, 252);"
            "    border-left: 3px solid rgb(99, 102, 241);"
            "}"
        )
        button.setStyleSheet(style)
        button.clicked.connect(lambda: self.on_button_click(text))
        container_layout.addWidget(button)
        
        # Add inline count badge
        if show_count:
            count_label = QLabel("0")
            count_label.setStyleSheet("""
                QLabel {
                    background: rgba(99, 102, 241, 0.2);
                    color: rgb(165, 180, 252);
                    border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 12px;
                    padding: 3px 10px;
                    font-size: 11px;
                    font-weight: 700;
                    min-width: 24px;
                }
            """)
            count_label.setAlignment(Qt.AlignCenter)
            count_label.setFixedHeight(22)
            count_label.hide()  # Hide initially if count is 0
            container_layout.addWidget(count_label)
            container_layout.addSpacing(16)
            self.count_labels[text] = count_label
        
        self.buttons[text] = button
        return container
        
    def on_button_click(self, button_name):
        """Handle button click with enhanced visual feedback"""
        self.set_active_button(button_name)
        self.button_clicked.emit(button_name)
    
    def set_active_button(self, button_name):
        """Set active button with service-specific color (background + accent glow)"""
        for name, button in self.buttons.items():
            if name == button_name:
                # Get service-specific color
                service_color = self.service_colors.get(name, Colors.ACCENT)
                service_color_rgb = self._hex_to_rgb(service_color)
                
                # STRONG ACTIVE STATE: Service-colored background + Glow
                active_style = (
                    f"QPushButton {{"
                    f"    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                    f"        stop:0 rgba({service_color_rgb[0]}, {service_color_rgb[1]}, {service_color_rgb[2]}, 0.3), "
                    f"        stop:1 rgba({service_color_rgb[0]}, {service_color_rgb[1]}, {service_color_rgb[2]}, 0.1));"
                    f"    color: rgb(248, 250, 252);"
                    f"    border: none;"
                    f"    border-left: 4px solid {service_color};"
                    f"    border-right: 1px solid rgba({service_color_rgb[0]}, {service_color_rgb[1]}, {service_color_rgb[2]}, 0.4);"
                    f"    text-align: left;"
                    f"    padding: 12px 20px;"
                    f"    font-size: 14px;"
                    f"    font-weight: 700;"
                    f"    font-family: 'Inter', 'Segoe UI', sans-serif;"
                    f"}}"
                )
                button.setStyleSheet(active_style)
                
                # Add service-colored glow effect
                glow = QGraphicsDropShadowEffect()
                glow.setBlurRadius(20)
                glow.setColor(QColor(service_color_rgb[0], service_color_rgb[1], service_color_rgb[2], 100))
                glow.setOffset(0, 0)
                button.setGraphicsEffect(glow)
                
                self.active_button = button
            else:
                # NORMAL STATE
                normal_style = (
                    "QPushButton {"
                    "    background: transparent;"
                    "    color: rgb(203, 213, 225);"
                    "    border: none;"
                    "    border-left: 3px solid transparent;"
                    "    text-align: left;"
                    "    padding: 12px 20px;"
                    "    font-size: 14px;"
                    "    font-weight: 500;"
                    "    font-family: 'Inter', 'Segoe UI', sans-serif;"
                    "}"
                    "QPushButton:hover {"
                    "    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                    "        stop:0 rgba(99, 102, 241, 0.15), stop:1 transparent);"
                    "    color: rgb(165, 180, 252);"
                    "    border-left: 3px solid rgb(99, 102, 241);"
                    "}"
                )
                button.setStyleSheet(normal_style)
                button.setGraphicsEffect(None)  # Remove glow
    
    def connect_to_events(self):
        """Connect to event bus for real-time updates"""
        from core.events import EventBus, EventType
        event_bus = EventBus()
        # Subscribe to relevant event types
        resource_events = [
            EventType.INSTANCE_CREATED, EventType.INSTANCE_TERMINATED,
            EventType.BUCKET_CREATED, EventType.BUCKET_DELETED,
            EventType.VOLUME_CREATED, EventType.VOLUME_DELETED,
            EventType.DATABASE_CREATED, EventType.DATABASE_DELETED,
            EventType.FUNCTION_CREATED, EventType.FUNCTION_DELETED
        ]
        for event_type in resource_events:
            event_bus.subscribe(event_type, self.on_resource_event)
    
    def on_resource_event(self, event):
        """Handle resource events to update counts"""
        # Update counts after a short delay to batch updates
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.update_resource_counts)
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple for use in rgba() CSS"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def update_resource_counts(self):
        """Update resource count badges"""
        try:
            from services.compute_service import ComputeService
            from services.storage_service import StorageService
            from services.database_service import DatabaseService
            from services.serverless_service import ServerlessService
            from services.volume_service import VolumeService
            
            compute_service = ComputeService()
            storage_service = StorageService()
            db_service = DatabaseService()
            serverless_service = ServerlessService()
            volume_service = VolumeService()
            
            counts = {
                "Compute": len(compute_service.list_instances()),
                "Storage": len(storage_service.list_buckets()),
                "Volumes": len(volume_service.list_volumes(user="admin")),
                "Database": len(db_service.list_databases()),
                "Serverless": len(serverless_service.list_functions())
            }
            
            for name, count in counts.items():
                if name in self.count_labels:
                    label = self.count_labels[name]
                    label.setText(str(count))
                    if count > 0:
                        label.show()
                    else:
                        label.hide()
        except:
            pass  # Silently fail if services not available yet
