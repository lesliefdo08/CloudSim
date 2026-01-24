"""
Modern View Template Generator
Quickly modernize any CloudSim view with this template
"""

from typing import Callable, Dict, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QTimer
from ui.components.modern_card import ResourceCard, CardContainer, EmptyStateCard
from ui.components.action_buttons import ActionButton, ResourceActionBar
from ui.components.tooltips import add_tooltip_to_widget
from ui.components.notifications import NotificationManager
from ui.components.footer import Footer
from ui.design_system import Colors, Fonts, Spacing, Animations


class ModernViewTemplate(QWidget):
    """
    Template for creating modern card-based resource views
    
    Usage:
        class MyView(ModernViewTemplate):
            def __init__(self):
                super().__init__(
                    resource_name="Volume",
                    icon="💾",
                    subtitle="Block storage for EC2 instances",
                    tooltip_key="ebs"
                )
                self.service = MyService()
            
            def load_resources(self) -> List:
                return self.service.list_resources()
            
            def resource_to_card_data(self, resource) -> dict:
                return {
                    'icon': '💾',
                    'name': resource.name,
                    'id': resource.id,
                    'status': resource.status,
                    'details': {...},
                    'actions': ['attach', 'delete']
                }
    """
    
    def __init__(self, 
                 resource_name: str,
                 icon: str,
                 subtitle: str,
                 tooltip_key: str = None,
                 stats_config: List[Dict] = None,
                 parent=None):
        """
        Initialize modern view
        
        Args:
            resource_name: Display name (e.g., "Instance", "Bucket")
            icon: Emoji icon
            subtitle: Descriptive subtitle
            tooltip_key: Key for educational tooltip
            stats_config: List of stat cards to display
        """
        super().__init__(parent)
        
        self.resource_name = resource_name
        self.icon_emoji = icon
        self.subtitle_text = subtitle
        self.tooltip_key = tooltip_key
        self.stats_config = stats_config or []
        
        self._init_ui()
        QTimer.singleShot(100, self._initial_load)
    
    def _init_ui(self):
        """Initialize UI structure"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 32, 40, 32)
        content_layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Header with stats
        header = self._create_header()
        content_layout.addWidget(header)
        
        # Action bar
        self.action_bar = ResourceActionBar(self.resource_name, self)
        self.action_bar.create_clicked.connect(self.on_create)
        self.action_bar.refresh_clicked.connect(self._initial_load)
        content_layout.addWidget(self.action_bar)
        
        # Card container
        self.card_container = CardContainer(self)
        content_layout.addWidget(self.card_container)
        
        layout.addWidget(content)
        layout.addWidget(Footer())
    
    def _create_header(self) -> QWidget:
        """Create header with title and stats"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Left: Title section
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(int(Spacing.SM.replace('px', '')))
        
        title_row = QHBoxLayout()
        title_row.setSpacing(int(Spacing.MD.replace('px', '')))
        
        icon = QLabel(self.icon_emoji)
        icon.setStyleSheet(f"font-size: {Fonts.HERO};")
        title_row.addWidget(icon)
        
        title = QLabel(f"{self.resource_name}s")
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        if self.tooltip_key:
            add_tooltip_to_widget(title, self.tooltip_key)
        title_row.addWidget(title)
        title_row.addStretch()
        
        left_layout.addLayout(title_row)
        
        subtitle = QLabel(self.subtitle_text)
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        left_layout.addWidget(subtitle)
        
        header_layout.addWidget(left_container)
        header_layout.addStretch()
        
        # Right: Stats
        if self.stats_config:
            self.stats_container = QWidget()
            stats_layout = QHBoxLayout(self.stats_container)
            stats_layout.setContentsMargins(0, 0, 0, 0)
            stats_layout.setSpacing(int(Spacing.MD.replace('px', '')))
            
            self.stat_cards = {}
            for stat_config in self.stats_config:
                stat_card = self._create_stat_card(
                    "0",
                    stat_config['label'],
                    stat_config.get('color', Colors.INFO)
                )
                self.stat_cards[stat_config['key']] = stat_card
                stats_layout.addWidget(stat_card)
            
            header_layout.addWidget(self.stats_container)
        
        return header
    
    def _create_stat_card(self, value: str, label: str, color: str) -> QFrame:
        """Create mini stat card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.SM};
                padding: {Spacing.MD};
                min-width: 100px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {color};
        """)
        layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(label_widget)
        
        return card
    
    def _initial_load(self):
        """Initial load with skeleton"""
        self.action_bar.set_loading(True)
        self.card_container.show_loading(5)
        QTimer.singleShot(600, self._render_resources)
    
    def _render_resources(self):
        """Render resource cards"""
        self.action_bar.set_loading(False)
        
        try:
            resources = self.load_resources()
            self.update_stats(resources)
            
            self.card_container.clear_cards()
            
            if not resources:
                empty = self.card_container.show_empty(
                    f"No {self.resource_name}s",
                    self.get_empty_message(),
                    self.icon_emoji,
                    f"Create {self.resource_name}"
                )
                empty.create_clicked.connect(self.on_create)
                return
            
            for resource in resources:
                card_data = self.resource_to_card_data(resource)
                card = ResourceCard(card_data['id'], card_data, self)
                card.clicked.connect(self.on_resource_click)
                card.action_triggered.connect(self.on_action)
                self.card_container.add_card(card)
                
        except Exception as e:
            from ui.utils import show_error_dialog
            show_error_dialog(self, "Load Failed", str(e))
    
    def update_stat(self, stat_key: str, value: str):
        """Update a stat card value"""
        if stat_key in self.stat_cards:
            self.stat_cards[stat_key].findChild(QLabel, "stat_value").setText(str(value))
    
    # Override these methods in subclasses
    
    def load_resources(self) -> List:
        """Override: Load resources from service"""
        return []
    
    def resource_to_card_data(self, resource) -> dict:
        """Override: Convert resource to card data"""
        return {
            'icon': self.icon_emoji,
            'name': 'Resource',
            'id': 'id',
            'status': 'available',
            'details': {},
            'actions': []
        }
    
    def get_empty_message(self) -> str:
        """Override: Get empty state message"""
        return f"Create your first {self.resource_name.lower()} to get started."
    
    def update_stats(self, resources: List):
        """Override: Update statistics based on resources"""
        if 'total' in self.stat_cards:
            self.update_stat('total', str(len(resources)))
    
    def on_create(self):
        """Override: Handle create action"""
        NotificationManager.show_info(f"Create {self.resource_name} not implemented")
    
    def on_action(self, action: str, resource_id: str):
        """Override: Handle resource action"""
        NotificationManager.show_info(f"Action '{action}' not implemented")
    
    def on_resource_click(self, resource_id: str):
        """Override: Handle resource click"""
        NotificationManager.show_info(f"Details for {resource_id}")


# Example usage:
"""
from ui.components.modern_view_template import ModernViewTemplate

class VolumesView(ModernViewTemplate):
    def __init__(self):
        super().__init__(
            resource_name="Volume",
            icon="💾",
            subtitle="Persistent block storage for EC2 instances",
            tooltip_key="ebs",
            stats_config=[
                {'key': 'total', 'label': 'Total', 'color': Colors.INFO},
                {'key': 'available', 'label': 'Available', 'color': Colors.SUCCESS},
                {'key': 'in_use', 'label': 'In Use', 'color': Colors.WARNING},
            ]
        )
        self.service = VolumeService()
    
    def load_resources(self):
        return self.service.list_volumes()
    
    def resource_to_card_data(self, volume):
        return {
            'icon': '💾',
            'name': volume.name,
            'id': volume.id,
            'status': volume.status,
            'details': {
                'Size': f"{volume.size} GB",
                'Type': volume.type,
                'Attached': volume.instance_id or 'Not attached',
            },
            'actions': ['attach' if volume.status == 'available' else 'detach', 'delete']
        }
    
    def update_stats(self, volumes):
        available = sum(1 for v in volumes if v.status == 'available')
        in_use = sum(1 for v in volumes if v.status == 'in-use')
        
        self.update_stat('total', str(len(volumes)))
        self.update_stat('available', str(available))
        self.update_stat('in_use', str(in_use))
"""
