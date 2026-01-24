"""
Modern Action Buttons - Icon + text with semantic styling
Always visible, context-aware, and accessible
"""

from PySide6.QtWidgets import QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from ui.design_system import Colors, Fonts


class ActionButton(QPushButton):
    """
    Modern action button with icon, text, and semantic styling
    Includes hover glow and micro-animations
    """
    
    STYLES = {
        'primary': {
            'bg': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.ACCENT}, stop:1 {Colors.ACCENT_HOVER})',
            'bg_hover': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.ACCENT_HOVER}, stop:1 #a5b4fc)',
            'color': 'white',
            'border': 'none',
        },
        'secondary': {
            'bg': 'transparent',
            'bg_hover': f'rgba(99, 102, 241, 0.1)',
            'color': Colors.TEXT_PRIMARY,
            'border': f'1px solid {Colors.BORDER}',
            'border_hover': f'1px solid {Colors.ACCENT}',
        },
        'success': {
            'bg': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.SUCCESS}, stop:1 #059669)',
            'bg_hover': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 {Colors.SUCCESS})',
            'color': 'white',
            'border': 'none',
        },
        'danger': {
            'bg': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.DANGER}, stop:1 #dc2626)',
            'bg_hover': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f87171, stop:1 {Colors.DANGER})',
            'color': 'white',
            'border': 'none',
        },
        'warning': {
            'bg': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.WARNING}, stop:1 #d97706)',
            'bg_hover': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #fbbf24, stop:1 {Colors.WARNING})',
            'color': 'white',
            'border': 'none',
        },
        'info': {
            'bg': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {Colors.INFO}, stop:1 #2563eb)',
            'bg_hover': f'qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60a5fa, stop:1 {Colors.INFO})',
            'color': 'white',
            'border': 'none',
        },
    }
    
    def __init__(self, text: str, icon: str = "", style: str = 'secondary', 
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        
        self.icon_text = icon
        self.button_style = style
        self.is_loading = False
        
        # Set text with icon
        display_text = f"{icon}  {text}" if icon else text
        self.setText(display_text)
        
        if tooltip:
            self.setToolTip(tooltip)
        
        self._apply_style()
        self.setCursor(Qt.PointingHandCursor)
    
    def _apply_style(self):
        """Apply semantic button style"""
        style_config = self.STYLES.get(self.button_style, self.STYLES['secondary'])
        
        border = style_config.get('border', 'none')
        border_hover = style_config.get('border_hover', border)
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: {style_config['bg']};
                color: {style_config['color']};
                border: {border};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
                min-height: 40px;
            }}
            QPushButton:hover {{
                background: {style_config['bg_hover']};
                border: {border_hover};
                padding: 12px 28px;
            }}
            QPushButton:pressed {{
                background: {style_config['bg']};
                padding: 12px 24px;
            }}
            QPushButton:disabled {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_DISABLED};
                border: 1px solid {Colors.BORDER};
            }}
        """)
    
    def set_loading(self, loading: bool):
        """Show loading state"""
        self.is_loading = loading
        if loading:
            self.setText(f"⏳  {self.text().replace(self.icon_text, '').strip()}")
            self.setEnabled(False)
        else:
            display_text = f"{self.icon_text}  {self.text().replace('⏳', '').strip()}" if self.icon_text else self.text().replace('⏳', '').strip()
            self.setText(display_text)
            self.setEnabled(True)


class IconButton(QPushButton):
    """Small icon-only button for compact spaces"""
    
    def __init__(self, icon: str, tooltip: str = "", color: str = Colors.TEXT_SECONDARY, parent=None):
        super().__init__(icon, parent)
        self.icon_color = color
        self.setToolTip(tooltip)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()
    
    def _apply_style(self):
        """Apply icon button style"""
        self.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.SURFACE};
                color: {self.icon_color};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                font-size: 16px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(99, 102, 241, 0.1);
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT};
            }}
            QPushButton:pressed {{
                background: rgba(99, 102, 241, 0.2);
            }}
            QPushButton:disabled {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_DISABLED};
                border-color: {Colors.BORDER};
            }}
        """)


class ActionButtonGroup(QWidget):
    """
    Group of related action buttons with proper spacing
    Ensures consistent layout and visibility
    """
    
    def __init__(self, orientation='horizontal', parent=None):
        super().__init__(parent)
        
        if orientation == 'horizontal':
            self.layout = QHBoxLayout(self)
        else:
            self.layout = QVBoxLayout(self)
        
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(12)
        self.buttons = []
    
    def add_button(self, button: QPushButton):
        """Add button to group"""
        self.layout.addWidget(button)
        self.buttons.append(button)
        return button
    
    def add_action(self, text: str, icon: str = "", style: str = 'secondary', 
                   callback=None, tooltip: str = "") -> ActionButton:
        """Add an action button"""
        btn = ActionButton(text, icon, style, tooltip, self)
        if callback:
            btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        self.buttons.append(btn)
        return btn
    
    def add_icon_button(self, icon: str, callback=None, tooltip: str = "", 
                       color: str = Colors.TEXT_SECONDARY) -> IconButton:
        """Add an icon button"""
        btn = IconButton(icon, tooltip, color, self)
        if callback:
            btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        self.buttons.append(btn)
        return btn
    
    def add_spacer(self):
        """Add flexible spacer"""
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout.addItem(spacer)
    
    def set_enabled(self, enabled: bool):
        """Enable/disable all buttons"""
        for btn in self.buttons:
            btn.setEnabled(enabled)
    
    def clear(self):
        """Remove all buttons"""
        for btn in self.buttons:
            btn.deleteLater()
        self.buttons.clear()


class ResourceActionBar(QWidget):
    """
    Comprehensive action bar for resource views
    Includes: Create, Refresh, Bulk Actions, Search, Filters
    """
    
    create_clicked = Signal()
    refresh_clicked = Signal()
    search_changed = Signal(str)
    filter_changed = Signal(str)
    bulk_action = Signal(str)
    
    def __init__(self, resource_type: str, parent=None):
        super().__init__(parent)
        self.resource_type = resource_type
        self._setup_ui()
    
    def _setup_ui(self):
        """Create action bar UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Primary actions (left side)
        primary_group = ActionButtonGroup('horizontal', self)
        
        # Create button - always visible and prominent
        self.create_btn = primary_group.add_action(
            f"Create {self.resource_type}",
            icon="＋",
            style='success',
            callback=self.create_clicked.emit,
            tooltip=f"Launch a new {self.resource_type}"
        )
        
        # Refresh button
        self.refresh_btn = primary_group.add_icon_button(
            icon="↻",
            callback=self.refresh_clicked.emit,
            tooltip="Refresh resource list"
        )
        
        layout.addWidget(primary_group)
        layout.addStretch()
        
        # Secondary actions (right side)
        secondary_group = ActionButtonGroup('horizontal', self)
        
        # Search button
        self.search_btn = secondary_group.add_icon_button(
            icon="🔍",
            tooltip="Search resources"
        )
        
        # Filter button
        self.filter_btn = secondary_group.add_icon_button(
            icon="⚙️",
            tooltip="Filter resources"
        )
        
        # More actions menu
        self.more_btn = secondary_group.add_icon_button(
            icon="⋮",
            tooltip="More actions"
        )
        
        layout.addWidget(secondary_group)
    
    def set_loading(self, loading: bool):
        """Set loading state"""
        self.create_btn.set_loading(loading)
        self.refresh_btn.setEnabled(not loading)


class BulkActionBar(QWidget):
    """
    Appears when items are selected - bulk operations
    Slides in from top with animation
    """
    
    action_triggered = Signal(str, list)  # action, selected_ids
    cancel_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_ids = []
        self._setup_ui()
        self.hide()
    
    def _setup_ui(self):
        """Create bulk action bar UI"""
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.ACCENT}, stop:1 {Colors.ACCENT_HOVER});
                border-radius: 8px;
                padding: 12px 20px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Selection count
        self.count_label = QLabel("0 selected")
        self.count_label.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            font-weight: {Fonts.SEMIBOLD};
            color: white;
        """)
        layout.addWidget(self.count_label)
        
        layout.addStretch()
        
        # Bulk actions
        action_group = ActionButtonGroup('horizontal', self)
        
        # Start (for instances)
        self.start_btn = action_group.add_action(
            "Start",
            icon="▶️",
            style='secondary',
            callback=lambda: self._trigger_action('start')
        )
        
        # Stop
        self.stop_btn = action_group.add_action(
            "Stop",
            icon="⏸️",
            style='secondary',
            callback=lambda: self._trigger_action('stop')
        )
        
        # Delete
        self.delete_btn = action_group.add_action(
            "Delete",
            icon="🗑️",
            style='danger',
            callback=lambda: self._trigger_action('delete')
        )
        
        layout.addWidget(action_group)
        
        # Cancel selection
        cancel_btn = IconButton("✕", "Clear selection", parent=self)
        cancel_btn.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(cancel_btn)
    
    def set_selection(self, selected_ids: list):
        """Update selected items"""
        self.selected_ids = selected_ids
        count = len(selected_ids)
        
        if count > 0:
            self.count_label.setText(f"{count} selected")
            self.show_animated()
        else:
            self.hide_animated()
    
    def show_animated(self):
        """Slide in from top"""
        self.show()
        # Could add QPropertyAnimation here for slide effect
    
    def hide_animated(self):
        """Slide out to top"""
        self.hide()
    
    def _trigger_action(self, action: str):
        """Trigger bulk action"""
        self.action_triggered.emit(action, self.selected_ids)


# Preset button configurations for common actions
COMMON_ACTIONS = {
    'create_instance': {
        'text': 'Launch Instance',
        'icon': '＋',
        'style': 'success',
        'tooltip': 'Launch a new EC2 instance'
    },
    'create_bucket': {
        'text': 'Create Bucket',
        'icon': '＋',
        'style': 'success',
        'tooltip': 'Create a new S3 bucket'
    },
    'create_volume': {
        'text': 'Create Volume',
        'icon': '＋',
        'style': 'success',
        'tooltip': 'Create a new EBS volume'
    },
    'create_database': {
        'text': 'Create Database',
        'icon': '＋',
        'style': 'success',
        'tooltip': 'Create a new RDS database'
    },
    'create_function': {
        'text': 'Create Function',
        'icon': '＋',
        'style': 'success',
        'tooltip': 'Create a new Lambda function'
    },
    'start': {
        'text': 'Start',
        'icon': '▶️',
        'style': 'success',
        'tooltip': 'Start the selected resource'
    },
    'stop': {
        'text': 'Stop',
        'icon': '⏸️',
        'style': 'warning',
        'tooltip': 'Stop the selected resource'
    },
    'restart': {
        'text': 'Restart',
        'icon': '🔄',
        'style': 'info',
        'tooltip': 'Restart the selected resource'
    },
    'terminate': {
        'text': 'Terminate',
        'icon': '🗑️',
        'style': 'danger',
        'tooltip': 'Permanently delete this resource'
    },
    'delete': {
        'text': 'Delete',
        'icon': '🗑️',
        'style': 'danger',
        'tooltip': 'Delete this resource'
    },
    'attach': {
        'text': 'Attach',
        'icon': '📎',
        'style': 'info',
        'tooltip': 'Attach to an instance'
    },
    'detach': {
        'text': 'Detach',
        'icon': '📤',
        'style': 'warning',
        'tooltip': 'Detach from instance'
    },
    'refresh': {
        'text': 'Refresh',
        'icon': '↻',
        'style': 'secondary',
        'tooltip': 'Refresh resource list'
    },
}


def create_action_button(action_key: str, callback=None, parent=None) -> ActionButton:
    """
    Create a pre-configured action button
    
    Args:
        action_key: Key from COMMON_ACTIONS
        callback: Click handler
        parent: Parent widget
    
    Returns:
        Configured ActionButton
    """
    config = COMMON_ACTIONS.get(action_key, {
        'text': action_key.title(),
        'icon': '',
        'style': 'secondary',
        'tooltip': ''
    })
    
    btn = ActionButton(
        config['text'],
        config['icon'],
        config['style'],
        config['tooltip'],
        parent
    )
    
    if callback:
        btn.clicked.connect(callback)
    
    return btn
