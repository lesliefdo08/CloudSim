"""
Modern Card Components - Vibrant, depth-layered cards with animations
Replaces flat tables with rich, interactive card-based layouts
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsOpacityEffect, QSpacerItem, QSizePolicy,
    QScrollArea
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient
from ui.design_system import Colors, Fonts, Spacing, Animations
from ui.components.state_badge import AnimatedStateBadge


class ResourceCard(QFrame):
    """
    Rich card for displaying cloud resources with hover animations
    Replaces flat table rows with depth and visual hierarchy
    """
    clicked = Signal(str)  # Emits resource ID
    action_triggered = Signal(str, str)  # Emits action name and resource ID
    
    def __init__(self, resource_id: str, resource_data: dict, parent=None):
        super().__init__(parent)
        self.resource_id = resource_id
        self.data = resource_data
        self.expanded = False
        
        self._setup_ui()
        self._setup_animations()
        self._apply_styles()
    
    def _setup_ui(self):
        """Create card layout with header and collapsible details"""
        self.setObjectName("resourceCard")
        self.setCursor(Qt.PointingHandCursor)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)
        
        # Header row: icon, title/subtitle, badges, actions
        header = QHBoxLayout()
        header.setSpacing(16)
        
        # Status indicator dot
        self.status_dot = QLabel("●")
        self.status_dot.setFixedSize(12, 12)
        self._update_status_dot()
        header.addWidget(self.status_dot)
        
        # Icon/Avatar
        icon = QLabel(self.data.get('icon', '📦'))
        icon.setStyleSheet(f"""
            font-size: 28px;
            padding: 8px;
            background: rgba(99, 102, 241, 0.1);
            border-radius: 8px;
        """)
        icon.setFixedSize(50, 50)
        icon.setAlignment(Qt.AlignCenter)
        header.addWidget(icon)
        
        # Title and subtitle
        text_container = QVBoxLayout()
        text_container.setSpacing(4)
        
        title = QLabel(self.data.get('name', 'Unnamed Resource'))
        title.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        text_container.addWidget(title)
        
        subtitle = QLabel(self.data.get('id', self.resource_id))
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_MUTED};
            font-family: {Fonts.MONOSPACE};
            opacity: {Colors.SECONDARY_OPACITY};
        """)
        text_container.addWidget(subtitle)
        
        header.addLayout(text_container)
        header.addStretch()
        
        # Animated status badge
        status = self.data.get('status', 'unknown')
        self.status_badge = AnimatedStateBadge(status)
        header.addWidget(self.status_badge)
        
        # Action buttons
        self.action_container = QWidget()
        action_layout = QHBoxLayout(self.action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        
        self.action_buttons = self._create_action_buttons()
        for btn in self.action_buttons:
            action_layout.addWidget(btn)
        
        self.action_container.setVisible(False)  # Hidden until hover
        header.addWidget(self.action_container)
        
        # Expand button
        self.expand_btn = QPushButton("▼")
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.setStyleSheet(self._icon_button_style())
        self.expand_btn.clicked.connect(self._toggle_expand)
        header.addWidget(self.expand_btn)
        
        main_layout.addLayout(header)
        
        # Collapsible details section
        self.details_widget = QWidget()
        self.details_widget.setVisible(False)
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(66, 0, 0, 0)  # Align with content
        details_layout.setSpacing(8)
        
        # Add detail rows
        details_data = self.data.get('details', {})
        for key, value in details_data.items():
            detail_row = self._create_detail_row(key, value)
            details_layout.addWidget(detail_row)
        
        main_layout.addWidget(self.details_widget)
    
    def _create_status_badge(self, status: str) -> QLabel:
        """Create vibrant status badge"""
        status_config = {
            'running': (Colors.SUCCESS, '#10b981', '●  Running'),
            'stopped': (Colors.TEXT_MUTED, '#6b7280', '■  Stopped'),
            'pending': (Colors.WARNING, '#f59e0b', '◐  Pending'),
            'error': (Colors.DANGER, '#ef4444', '✕  Error'),
            'available': (Colors.SUCCESS, '#10b981', '✓  Available'),
            'in-use': (Colors.INFO, '#3b82f6', '◉  In Use'),
            'terminated': (Colors.DANGER, '#ef4444', '✕  Terminated'),
        }
        
        color, border, text = status_config.get(
            status.lower(), 
            (Colors.TEXT_MUTED, '#6b7280', f'●  {status.title()}')
        )
        
        badge = QLabel(text)
        badge.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15),
                    stop:1 rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.05));
                color: {color};
                border: 1px solid {border};
                border-radius: 12px;
                padding: 6px 14px;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
            }}
        """)
        return badge
    
    def _update_status_dot(self):
        """Update status indicator dot color and badge state"""
        status = self.data.get('status', 'unknown').lower()
        color_map = {
            'running': Colors.SUCCESS,
            'stopped': Colors.TEXT_MUTED,
            'pending': Colors.WARNING,
            'error': Colors.DANGER,
            'available': Colors.SUCCESS,
        }
        color = color_map.get(status, Colors.TEXT_MUTED)
        
        self.status_dot.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 20px;
            }}
        """)
        
        # Update animated badge
        if hasattr(self, 'status_badge'):
            self.status_badge.set_state(status)
    
    def _create_action_buttons(self) -> list:
        """Create context-aware action buttons with overflow menu"""
        from PySide6.QtWidgets import QMenu
        from PySide6.QtCore import QPoint
        
        buttons = []
        actions = self.data.get('actions', [])
        
        action_styles = {
            'start': ('▶️', 'Start', Colors.SUCCESS),
            'stop': ('⏸️', 'Stop', Colors.WARNING),
            'restart': ('🔄', 'Restart', Colors.INFO),
            'terminate': ('🗑️', 'Terminate', Colors.DANGER),
            'delete': ('🗑️', 'Delete', Colors.DANGER),
            'edit': ('✏️', 'Edit', Colors.ACCENT),
            'attach': ('📎', 'Attach', Colors.INFO),
            'detach': ('📤', 'Detach', Colors.WARNING),
        }
        
        # Show first 2 actions as buttons, rest in overflow menu
        visible_actions = actions[:2] if len(actions) > 2 else actions
        overflow_actions = actions[2:] if len(actions) > 2 else []
        
        for action in visible_actions:
            icon, tooltip, color = action_styles.get(action, ('●', action.title(), Colors.ACCENT))
            
            btn = QPushButton(icon)
            btn.setToolTip(tooltip)
            btn.setFixedSize(36, 36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.1);
                    border: 1px solid {color};
                    border-radius: 6px;
                    color: {color};
                    font-size: 16px;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2);
                }}
            """)
            btn.clicked.connect(lambda checked, a=action: self._handle_action(a))
            buttons.append(btn)
        
        # Add overflow menu if there are more actions
        if overflow_actions:
            more_btn = QPushButton("⋮")
            more_btn.setToolTip("More actions")
            more_btn.setFixedSize(36, 36)
            more_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.SURFACE};
                    border: 1px solid {Colors.BORDER};
                    border-radius: 6px;
                    color: {Colors.TEXT_SECONDARY};
                    font-size: 18px;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: rgba(99, 102, 241, 0.1);
                    border-color: {Colors.ACCENT};
                    color: {Colors.ACCENT};
                }}
            """)
            
            def show_menu():
                menu = QMenu(more_btn)
                menu.setStyleSheet(f"""
                    QMenu {{
                        background: {Colors.CARD};
                        border: 1px solid {Colors.BORDER};
                        border-radius: 6px;
                        padding: 4px;
                    }}
                    QMenu::item {{
                        color: {Colors.TEXT_PRIMARY};
                        padding: 8px 20px;
                        border-radius: 4px;
                    }}
                    QMenu::item:selected {{
                        background: {Colors.ACCENT};
                        color: white;
                    }}
                """)
                
                for action in overflow_actions:
                    icon, tooltip, color = action_styles.get(action, ('●', action.title(), Colors.ACCENT))
                    menu_action = menu.addAction(f"{icon} {tooltip}")
                    menu_action.triggered.connect(lambda checked=False, a=action: self._handle_action(a))
                
                menu.exec(more_btn.mapToGlobal(QPoint(0, more_btn.height())))
            
            more_btn.clicked.connect(show_menu)
            buttons.append(more_btn)
        
        return buttons
    
    def _create_detail_row(self, key: str, value: str) -> QWidget:
        """Create a key-value detail row with de-emphasized secondary info"""
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Detect if this is secondary info (IDs, timestamps, regions)
        is_secondary = any(x in key.lower() for x in ['id', 'created', 'region', 'zone', 'arn', 'timestamp'])
        opacity = Colors.SECONDARY_OPACITY if is_secondary else "1.0"
        
        key_label = QLabel(f"{key}:")
        key_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_MUTED};
            font-weight: {Fonts.MEDIUM};
            min-width: 120px;
            opacity: {opacity};
        """)
        layout.addWidget(key_label)
        
        value_label = QLabel(str(value))
        value_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_SECONDARY};
            font-family: {Fonts.MONOSPACE if key in ['ID', 'IP', 'ARN'] else Fonts.PRIMARY};
            opacity: {opacity};
        """)
        value_label.setWordWrap(True)
        layout.addWidget(value_label)
        layout.addStretch()
        
        return row
    
    def _icon_button_style(self) -> str:
        """Icon button stylesheet"""
        return f"""
            QPushButton {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                color: {Colors.TEXT_SECONDARY};
                font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(99, 102, 241, 0.1);
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT};
            }}
        """
    
    def _toggle_expand(self):
        """Toggle details section visibility"""
        self.expanded = not self.expanded
        self.details_widget.setVisible(self.expanded)
        self.expand_btn.setText("▲" if self.expanded else "▼")
        
        # Animate expansion
        self._animate_expand()
    
    def _handle_action(self, action: str):
        """Handle action button click"""
        self.action_triggered.emit(action, self.resource_id)
    
    def _setup_animations(self):
        """Setup hover and expansion animations"""
        # Hover lift animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _animate_expand(self):
        """Animate details expansion"""
        if hasattr(self, 'details_widget'):
            # Fade in/out effect
            effect = QGraphicsOpacityEffect()
            self.details_widget.setGraphicsEffect(effect)
            
            opacity = QPropertyAnimation(effect, b"opacity")
            opacity.setDuration(250)
            opacity.setStartValue(0.0 if self.expanded else 1.0)
            opacity.setEndValue(1.0 if self.expanded else 0.0)
            opacity.start()
    
    def _apply_styles(self):
        """Apply card styles with depth"""
        self.setStyleSheet(f"""
            QFrame#resourceCard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 0;
            }}
            QFrame#resourceCard:hover {{
                border-color: {Colors.ACCENT};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD_HOVER}, stop:1 #1f2937);
            }}
        """)
    
    def enterEvent(self, event):
        """Show action buttons on hover"""
        super().enterEvent(event)
        self.action_container.setVisible(True)
    
    def leaveEvent(self, event):
        """Hide action buttons on leave"""
        super().leaveEvent(event)
        if not self.expanded:
            self.action_container.setVisible(False)
    
    def mousePressEvent(self, event):
        """Handle card click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.resource_id)
        super().mousePressEvent(event)


class SkeletonCard(QFrame):
    """Loading skeleton for cards - subtle pulse animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._start_animation()
    
    def _setup_ui(self):
        """Create skeleton structure"""
        self.setFixedHeight(100)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Skeleton elements
        for width in [50, 200, 100, 80]:
            skeleton = QWidget()
            skeleton.setFixedSize(width, 20)
            skeleton.setStyleSheet(f"""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.SURFACE}, 
                    stop:0.5 {Colors.SURFACE_HOVER},
                    stop:1 {Colors.SURFACE});
                border-radius: 4px;
            """)
            layout.addWidget(skeleton)
        
        layout.addStretch()
    
    def _start_animation(self):
        """Pulse animation for skeleton"""
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(0.5)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1)  # Infinite
        self.animation.setEasingCurve(QEasingCurve.InOutSine)
        self.animation.start()


class EmptyStateCard(QWidget):
    """Vibrant empty state with call-to-action"""
    
    create_clicked = Signal()
    
    def __init__(self, title: str, message: str, icon: str = "📦", 
                 cta_text: str = "Create Resource", parent=None):
        super().__init__(parent)
        self._setup_ui(title, message, icon, cta_text)
    
    def _setup_ui(self, title: str, message: str, icon: str, cta_text: str):
        """Create empty state UI"""
        self.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.SURFACE}, stop:1 #1a2535);
                border: 2px dashed {Colors.BORDER};
                border-radius: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignCenter)
        
        # Icon with gradient background
        icon_container = QLabel(icon)
        icon_container.setStyleSheet(f"""
            font-size: 72px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(99, 102, 241, 0.1), stop:1 rgba(99, 102, 241, 0.05));
            border-radius: 24px;
            padding: 30px;
        """)
        icon_container.setAlignment(Qt.AlignCenter)
        icon_container.setFixedSize(150, 150)
        layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_MUTED};
            line-height: 1.6;
        """)
        msg_label.setAlignment(Qt.AlignCenter)
        msg_label.setWordWrap(True)
        msg_label.setMaximumWidth(400)
        layout.addWidget(msg_label)
        
        # CTA Button
        cta_btn = QPushButton(cta_text)
        cta_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT}, stop:1 {Colors.ACCENT_HOVER});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 14px 32px;
                font-size: {Fonts.HEADING};
                font-weight: {Fonts.SEMIBOLD};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT_HOVER}, stop:1 #a5b4fc);
                padding: 14px 36px;
            }}
        """)
        cta_btn.clicked.connect(self.create_clicked.emit)
        layout.addWidget(cta_btn, alignment=Qt.AlignCenter)


class CardContainer(QScrollArea):
    """Scrollable container for resource cards with grid layout"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup scrollable card container"""
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {Colors.SURFACE};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.BORDER};
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.ACCENT};
            }}
        """)
        
        # Content widget
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        self.setWidget(self.content)
    
    def add_card(self, card: ResourceCard):
        """Add a resource card to the container"""
        self.content_layout.addWidget(card)
    
    def clear_cards(self):
        """Remove all cards"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def show_loading(self, count: int = 3):
        """Show skeleton loaders"""
        self.clear_cards()
        for _ in range(count):
            self.content_layout.addWidget(SkeletonCard())
    
    def show_empty(self, title: str, message: str, icon: str = "📦", cta: str = "Create"):
        """Show empty state"""
        self.clear_cards()
        empty = EmptyStateCard(title, message, icon, cta)
        self.content_layout.addWidget(empty)
        return empty
