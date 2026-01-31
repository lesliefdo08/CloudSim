"""
Enhanced Confirmation Dialog - Shows consequences of actions
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from typing import List


class ConsequenceItem(QFrame):
    """Individual consequence item display"""
    
    def __init__(self, icon: str, text: str, consequence_type: str = "warning", parent=None):
        super().__init__(parent)
        self.init_ui(icon, text, consequence_type)
    
    def init_ui(self, icon: str, text: str, consequence_type: str):
        """Initialize consequence item UI"""
        from ui.design_system import Colors
        
        colors = {
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": Colors.ACCENT
        }
        
        color = colors.get(consequence_type, colors["warning"])
        
        self.setStyleSheet(f"""
            ConsequenceItem {{
                background: rgba(30, 41, 59, 0.5);
                border-left: 3px solid {color};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"""
            font-size: 20px;
            color: {color};
        """)
        layout.addWidget(icon_label)
        
        # Text
        text_label = QLabel(text)
        text_label.setStyleSheet(f"""
            font-size: 13px;
            color: {Colors.TEXT_PRIMARY};
        """)
        text_label.setWordWrap(True)
        layout.addWidget(text_label, 1)


class ConfirmationDialog(QDialog):
    """Enhanced confirmation dialog with consequences"""
    
    def __init__(self, 
                 title: str,
                 message: str,
                 consequences: List[dict],
                 action_text: str = "Confirm",
                 action_type: str = "danger",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.action_type = action_type
        self.init_ui(title, message, consequences, action_text)
    
    def init_ui(self, title: str, message: str, consequences: List[dict], action_text: str):
        """Initialize confirmation dialog UI"""
        from ui.design_system import Colors
        
        self.setStyleSheet(f"""
            QDialog {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        
        # Title with icon
        title_layout = QHBoxLayout()
        
        icon_map = {
            "danger": "⚠️",
            "warning": "⚡",
            "info": "ℹ️"
        }
        
        title_icon = QLabel(icon_map.get(self.action_type, "⚠️"))
        title_icon.setStyleSheet("font-size: 32px;")
        title_layout.addWidget(title_icon)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
        """)
        title_layout.addWidget(title_label, 1)
        
        layout.addLayout(title_layout)
        
        # Message
        message_label = QLabel(message)
        message_label.setStyleSheet(f"""
            font-size: 14px;
            color: {Colors.TEXT_SECONDARY};
            line-height: 1.5;
        """)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Consequences section
        if consequences:
            consequences_title = QLabel("This action will:")
            consequences_title.setStyleSheet(f"""
                font-size: 13px;
                font-weight: 600;
                color: {Colors.TEXT_PRIMARY};
                margin-top: 8px;
            """)
            layout.addWidget(consequences_title)
            
            for consequence in consequences:
                item = ConsequenceItem(
                    consequence.get("icon", "•"),
                    consequence.get("text", ""),
                    consequence.get("type", "warning"),
                    self
                )
                layout.addWidget(item)
        
        layout.addSpacing(8)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.CARD};
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER};
                padding: 0px 24px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {Colors.SURFACE_HOVER};
                border-color: {Colors.ACCENT};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Confirm button
        confirm_btn = QPushButton(action_text)
        confirm_btn.setFixedHeight(40)
        
        button_colors = {
            "danger": ("#ef4444", "#dc2626"),
            "warning": ("#f59e0b", "#d97706"),
            "info": (Colors.ACCENT, Colors.ACCENT_HOVER)
        }
        
        bg_color, hover_color = button_colors.get(self.action_type, button_colors["danger"])
        
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg_color};
                color: white;
                border: none;
                padding: 0px 24px;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {hover_color};
            }}
        """)
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        layout.addLayout(button_layout)


def confirm_action(parent, title: str, message: str, consequences: List[dict], 
                   action_text: str = "Confirm", action_type: str = "danger") -> bool:
    """
    Show confirmation dialog and return True if confirmed
    
    Args:
        parent: Parent widget
        title: Dialog title
        message: Main message
        consequences: List of consequence dicts with 'icon', 'text', and 'type'
        action_text: Text for confirm button
        action_type: Type of action (danger, warning, info)
    
    Returns:
        True if confirmed, False otherwise
    """
    dialog = ConfirmationDialog(title, message, consequences, action_text, action_type, parent)
    return dialog.exec() == QDialog.Accepted


# Predefined consequence templates
TERMINATE_INSTANCE_CONSEQUENCES = [
    {"icon": "🗑️", "text": "Permanently delete this compute instance", "type": "danger"},
    {"icon": "💾", "text": "All data on attached volumes will remain intact", "type": "info"},
    {"icon": "💰", "text": "Stop incurring charges for this instance", "type": "info"},
    {"icon": "⚠️", "text": "This action cannot be undone", "type": "warning"}
]

DELETE_VOLUME_CONSEQUENCES = [
    {"icon": "🗑️", "text": "Permanently delete this volume and all its data", "type": "danger"},
    {"icon": "📸", "text": "All snapshots will be preserved", "type": "info"},
    {"icon": "⚠️", "text": "This action cannot be undone", "type": "warning"},
    {"icon": "💾", "text": "Make sure to backup important data first", "type": "warning"}
]

DELETE_BUCKET_CONSEQUENCES = [
    {"icon": "🗑️", "text": "Permanently delete this bucket", "type": "danger"},
    {"icon": "📄", "text": "All objects in the bucket will be deleted", "type": "danger"},
    {"icon": "⚠️", "text": "This action cannot be undone", "type": "warning"}
]

DELETE_DATABASE_CONSEQUENCES = [
    {"icon": "🗑️", "text": "Permanently delete this database", "type": "danger"},
    {"icon": "📊", "text": "All tables and records will be lost", "type": "danger"},
    {"icon": "⚠️", "text": "This action cannot be undone", "type": "warning"},
    {"icon": "💾", "text": "Consider exporting data first", "type": "warning"}
]

DELETE_FUNCTION_CONSEQUENCES = [
    {"icon": "🗑️", "text": "Permanently delete this Lambda function", "type": "danger"},
    {"icon": "📝", "text": "Function code will be lost", "type": "danger"},
    {"icon": "⚙️", "text": "All environment variables will be deleted", "type": "warning"}
]

DETACH_VOLUME_CONSEQUENCES = [
    {"icon": "📤", "text": "Detach volume from instance", "type": "warning"},
    {"icon": "⚠️", "text": "Instance may lose access to data", "type": "warning"},
    {"icon": "💾", "text": "Volume data will be preserved", "type": "info"}
]
