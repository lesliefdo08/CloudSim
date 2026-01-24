"""
Activity Log View - Audit trail of user actions
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QTableWidget, QTableWidgetItem, QComboBox,
                               QLineEdit, QHeaderView)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from core.events import EventBus, EventType
from core.iam import IAMManager
from datetime import datetime


class ActivityLogView(QWidget):
    """Activity Log Viewer - Shows audit trail of all user actions"""
    
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()
        self.iam = IAMManager()
        self.auto_refresh = True
        self.setup_ui()
        self.load_activity_log()
        
        # Auto-refresh every 5 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_activity_log)
        self.refresh_timer.start(5000)
    
    def setup_ui(self):
        """Setup the activity log UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("Activity Log")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #e2e8f0;")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Auto-refresh toggle
        self.refresh_btn = QPushButton("🔄 Auto-Refresh: ON")
        self.refresh_btn.clicked.connect(self.toggle_auto_refresh)
        header_layout.addWidget(self.refresh_btn)
        
        # Manual refresh
        refresh_now_btn = QPushButton("↻ Refresh Now")
        refresh_now_btn.clicked.connect(self.load_activity_log)
        header_layout.addWidget(refresh_now_btn)
        
        layout.addLayout(header_layout)
        
        # Filters
        filter_layout = QHBoxLayout()
        
        # User filter
        filter_layout.addWidget(QLabel("Filter by user:"))
        self.user_filter = QComboBox()
        self.user_filter.addItem("All Users")
        for user in self.iam.list_users():
            self.user_filter.addItem(user.username)
        self.user_filter.currentTextChanged.connect(self.load_activity_log)
        filter_layout.addWidget(self.user_filter)
        
        # Event type filter
        filter_layout.addWidget(QLabel("Event type:"))
        self.event_filter = QComboBox()
        self.event_filter.addItem("All Events")
        for event_type in EventType:
            self.event_filter.addItem(event_type.value)
        self.event_filter.currentTextChanged.connect(self.load_activity_log)
        filter_layout.addWidget(self.event_filter)
        
        # Region filter
        filter_layout.addWidget(QLabel("Region:"))
        self.region_filter = QComboBox()
        self.region_filter.addItem("All Regions")
        for region in ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "local"]:
            self.region_filter.addItem(region)
        self.region_filter.currentTextChanged.connect(self.load_activity_log)
        filter_layout.addWidget(self.region_filter)
        
        filter_layout.addStretch()
        
        # Clear filters
        clear_btn = QPushButton("✖ Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        layout.addLayout(filter_layout)
        
        # Stats
        self.stats_label = QLabel("Total events: 0")
        self.stats_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.stats_label)
        
        # Activity table with modern styling
        from ui.design_system import Styles
        self.activity_table = QTableWidget()
        self.activity_table.setColumnCount(6)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Action", "Resource", "Region", "Details"
        ])
        
        # Set column widths
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # User
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Action
        header.setSectionResizeMode(3, QHeaderView.Stretch)           # Resource
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Region
        header.setSectionResizeMode(5, QHeaderView.Stretch)           # Details
        
        self.activity_table.setSelectionMode(QTableWidget.NoSelection)
        self.activity_table.setShowGrid(False)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.setStyleSheet(Styles.table())
        
        layout.addWidget(self.activity_table)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def apply_styles(self):
        """Apply dark theme styles"""
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QTableWidget {
                background-color: #1e293b;
                alternate-background-color: #0f172a;
                gridline-color: #334155;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3b82f6;
                color: white;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #e2e8f0;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #3b82f6;
                font-weight: bold;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QComboBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                color: #e2e8f0;
            }
            QComboBox:drop-down {
                border: none;
            }
            QLabel {
                color: #e2e8f0;
            }
        """)
    
    def load_activity_log(self):
        """Load and display activity log"""
        # Get filters
        user_filter = self.user_filter.currentText()
        event_filter = self.event_filter.currentText()
        region_filter = self.region_filter.currentText()
        
        # Get events from event bus
        username = None if user_filter == "All Users" else user_filter
        events = self.event_bus.get_events(username=username, limit=1000)
        
        # Apply additional filters
        if event_filter != "All Events":
            events = [e for e in events if e.event_type.value == event_filter]
        
        if region_filter != "All Regions":
            events = [e for e in events if e.region == region_filter]
        
        # Update stats
        self.stats_label.setText(f"Total events: {len(events)} | Showing last 500")
        events = events[:500]  # Limit display to 500 most recent
        
        # Populate table
        self.activity_table.setRowCount(len(events))
        
        for row, event in enumerate(events):
            # Timestamp
            timestamp_item = QTableWidgetItem(
                event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
            timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
            self.activity_table.setItem(row, 0, timestamp_item)
            
            # User
            user_item = QTableWidgetItem(event.username or "system")
            user_item.setFlags(user_item.flags() & ~Qt.ItemIsEditable)
            if event.username:
                user_item.setForeground(Qt.green)
            else:
                user_item.setForeground(Qt.gray)
            self.activity_table.setItem(row, 1, user_item)
            
            # Action (pretty format)
            action = event.event_type.value.split('.')[-1].title()
            action_item = QTableWidgetItem(action)
            action_item.setFlags(action_item.flags() & ~Qt.ItemIsEditable)
            # Color code by action type
            if "created" in event.event_type.value:
                action_item.setForeground(Qt.green)
            elif "deleted" in event.event_type.value or "terminated" in event.event_type.value:
                action_item.setForeground(Qt.red)
            elif "started" in event.event_type.value or "invoked" in event.event_type.value:
                action_item.setForeground(Qt.cyan)
            else:
                action_item.setForeground(Qt.yellow)
            self.activity_table.setItem(row, 2, action_item)
            
            # Resource
            resource_type = event.event_type.value.split('.')[1]
            resource_str = f"{resource_type}: {event.resource_id or 'N/A'}"
            resource_item = QTableWidgetItem(resource_str)
            resource_item.setFlags(resource_item.flags() & ~Qt.ItemIsEditable)
            self.activity_table.setItem(row, 3, resource_item)
            
            # Region
            region_item = QTableWidgetItem(event.region)
            region_item.setFlags(region_item.flags() & ~Qt.ItemIsEditable)
            self.activity_table.setItem(row, 4, region_item)
            
            # Details (show relevant detail keys)
            details_str = ", ".join([f"{k}={v}" for k, v in list(event.details.items())[:3]])
            if len(event.details) > 3:
                details_str += "..."
            details_item = QTableWidgetItem(details_str or "No details")
            details_item.setFlags(details_item.flags() & ~Qt.ItemIsEditable)
            details_item.setForeground(Qt.gray)
            self.activity_table.setItem(row, 5, details_item)
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh on/off"""
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.refresh_timer.start(5000)
            self.refresh_btn.setText("🔄 Auto-Refresh: ON")
            self.refresh_btn.setStyleSheet("background-color: #10b981;")
        else:
            self.refresh_timer.stop()
            self.refresh_btn.setText("🔄 Auto-Refresh: OFF")
            self.refresh_btn.setStyleSheet("background-color: #ef4444;")
    
    def clear_filters(self):
        """Clear all filters"""
        self.user_filter.setCurrentIndex(0)
        self.event_filter.setCurrentIndex(0)
        self.region_filter.setCurrentIndex(0)
