"""
Global Notification System - Toast notifications and banners
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal, QPoint
from PySide6.QtGui import QFont
from typing import Literal


class NotificationBanner(QWidget):
    """Toast-style notification banner"""
    
    closed = Signal()
    
    def __init__(self, message: str, notification_type: Literal["success", "error", "warning", "info"], 
                 duration: int = 3000, parent=None):
        super().__init__(parent)
        self.notification_type = notification_type
        self.duration = duration
        self.init_ui(message)
        
        # Auto-hide timer
        if duration > 0:
            QTimer.singleShot(duration, self.hide_notification)
    
    def init_ui(self, message: str):
        """Initialize notification UI"""
        from ui.design_system import Colors
        
        # Styling based on type
        styles = {
            "success": {
                "bg": "#10b981",
                "border": "#059669",
                "icon": "✓"
            },
            "error": {
                "bg": "#ef4444",
                "border": "#dc2626",
                "icon": "✕"
            },
            "warning": {
                "bg": "#f59e0b",
                "border": "#d97706",
                "icon": "⚠"
            },
            "info": {
                "bg": Colors.ACCENT,
                "border": Colors.ACCENT_HOVER,
                "icon": "ℹ"
            }
        }
        
        style = styles.get(self.notification_type, styles["info"])
        
        self.setStyleSheet(f"""
            NotificationBanner {{
                background: {style['bg']};
                border: 2px solid {style['border']};
                border-radius: 8px;
                padding: 0px;
            }}
        """)
        
        self.setFixedHeight(60)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(style['icon'])
        icon_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
        """)
        layout.addWidget(icon_label)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 500;
            color: white;
        """)
        message_label.setWordWrap(True)
        layout.addWidget(message_label, 1)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        close_btn.clicked.connect(self.hide_notification)
        layout.addWidget(close_btn)
        
        # Opacity effect for animations
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Fade in animation
        self.fade_in()
    
    def fade_in(self):
        """Fade in animation"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        self.animation.start()
    
    def hide_notification(self):
        """Fade out and close"""
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(200)
        self.animation.setStartValue(1)
        self.animation.setEndValue(0)
        self.animation.setEasingCurve(QEasingCurve.InCubic)
        self.animation.finished.connect(self._on_fade_complete)
        self.animation.start()
    
    def _on_fade_complete(self):
        """Handle fade completion"""
        self.closed.emit()
        self.deleteLater()


class NotificationManager(QWidget):
    """Manages multiple notifications in a stack"""
    
    _instance = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notifications = []
        self.init_ui()
        NotificationManager._instance = self
    
    @classmethod
    def get_instance(cls, parent=None):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = NotificationManager(parent)
        return cls._instance
    
    def init_ui(self):
        """Initialize notification manager UI"""
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        self.layout.addStretch()
    
    def show_notification(self, message: str, notification_type: Literal["success", "error", "warning", "info"],
                         duration: int = 3000):
        """Show a new notification"""
        notification = NotificationBanner(message, notification_type, duration, self)
        notification.closed.connect(lambda: self._remove_notification(notification))
        
        # Insert before stretch
        self.layout.insertWidget(self.layout.count() - 1, notification)
        self.notifications.append(notification)
        
        # Limit to 5 notifications
        if len(self.notifications) > 5:
            oldest = self.notifications[0]
            oldest.hide_notification()
        
        self._update_position()
        self.show()
    
    def _remove_notification(self, notification):
        """Remove notification from list"""
        if notification in self.notifications:
            self.notifications.remove(notification)
        
        if not self.notifications:
            self.hide()
    
    def _update_position(self):
        """Update position to top-right corner"""
        if self.parent():
            parent_rect = self.parent().rect()
            self.setGeometry(
                parent_rect.width() - 540,
                20,
                520,
                parent_rect.height() - 40
            )
    
    @classmethod
    def show_success(cls, message: str, duration: int = 3000):
        """Show success notification"""
        instance = cls.get_instance()
        if instance:
            instance.show_notification(message, "success", duration)
    
    @classmethod
    def show_error(cls, message: str, duration: int = 5000):
        """Show error notification"""
        instance = cls.get_instance()
        if instance:
            instance.show_notification(message, "error", duration)
    
    @classmethod
    def show_warning(cls, message: str, duration: int = 4000):
        """Show warning notification"""
        instance = cls.get_instance()
        if instance:
            instance.show_notification(message, "warning", duration)
    
    @classmethod
    def show_info(cls, message: str, duration: int = 3000):
        """Show info notification"""
        instance = cls.get_instance()
        if instance:
            instance.show_notification(message, "info", duration)


class GlobalActivityFeed(QWidget):
    """Real-time global activity feed widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_activities = 50
        self.init_ui()
        self.connect_to_events()
    
    def init_ui(self):
        """Initialize activity feed UI"""
        from ui.design_system import Colors
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet(f"""
            background: {Colors.CARD};
            border-bottom: 1px solid {Colors.BORDER};
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        
        title = QLabel("Recent Activity")
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        
        self.count_label = QLabel("0 events")
        self.count_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_SECONDARY};
        """)
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # Activity list
        from PySide6.QtWidgets import QScrollArea, QVBoxLayout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {Colors.SURFACE};
                border: none;
            }}
        """)
        
        self.activity_container = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_container)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(1)
        self.activity_layout.addStretch()
        
        scroll.setWidget(self.activity_container)
        layout.addWidget(scroll)
    
    def connect_to_events(self):
        """Connect to event bus"""
        from core.events import EventBus, EventType
        event_bus = EventBus()
        # Subscribe to all event types
        for event_type in EventType:
            event_bus.subscribe(event_type, self.on_event_logged)
    
    def on_event_logged(self, event):
        """Handle new event"""
        self.add_activity(event)
    
    def add_activity(self, event):
        """Add activity to feed"""
        from ui.design_system import Colors
        from datetime import datetime
        
        activity_item = QWidget()
        activity_item.setStyleSheet(f"""
            QWidget {{
                background: {Colors.CARD};
                border-bottom: 1px solid {Colors.BORDER};
            }}
            QWidget:hover {{
                background: {Colors.SURFACE_HOVER};
            }}
        """)
        
        item_layout = QVBoxLayout(activity_item)
        item_layout.setContentsMargins(16, 12, 16, 12)
        item_layout.setSpacing(4)
        
        # Header with user and time
        header_layout = QHBoxLayout()
        
        user_label = QLabel(f"👤 {event.username}")
        user_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 600;
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(user_label)
        
        header_layout.addStretch()
        
        time_label = QLabel(event.timestamp.strftime("%H:%M:%S"))
        time_label.setStyleSheet(f"""
            font-size: 11px;
            color: {Colors.TEXT_SECONDARY};
        """)
        header_layout.addWidget(time_label)
        
        item_layout.addLayout(header_layout)
        
        # Action
        action_label = QLabel(f"{self._get_action_icon(event.event_type)} {event.event_type}")
        action_label.setStyleSheet(f"""
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
        """)
        item_layout.addWidget(action_label)
        
        # Resource
        if event.resource_id:
            resource_label = QLabel(f"Resource: {event.resource_id}")
            resource_label.setStyleSheet(f"""
                font-size: 11px;
                color: {Colors.TEXT_SECONDARY};
            """)
            item_layout.addWidget(resource_label)
        
        # Insert at top (before stretch)
        self.activity_layout.insertWidget(0, activity_item)
        
        # Update count
        count = self.activity_layout.count() - 1  # Subtract stretch
        self.count_label.setText(f"{count} events")
        
        # Limit activities
        if count > self.max_activities:
            old_item = self.activity_layout.itemAt(self.max_activities)
            if old_item and old_item.widget():
                old_item.widget().deleteLater()
    
    def _get_action_icon(self, event_type: str) -> str:
        """Get icon for event type"""
        icons = {
            "InstanceCreated": "🖥️",
            "InstanceStarted": "▶️",
            "InstanceStopped": "⏸️",
            "InstanceTerminated": "🗑️",
            "VolumeCreated": "💾",
            "VolumeAttached": "📎",
            "VolumeDetached": "📤",
            "VolumeDeleted": "🗑️",
            "BucketCreated": "🪣",
            "BucketDeleted": "🗑️",
            "DatabaseCreated": "🗄️",
            "DatabaseDeleted": "🗑️",
            "FunctionCreated": "⚡",
            "FunctionInvoked": "▶️",
            "UserCreated": "👤",
            "PolicyCreated": "📜",
        }
        return icons.get(event_type, "📋")
