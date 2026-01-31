"""
Modern Compute View - Card-based EC2 instance management
Vibrant, depth-layered design with smooth animations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, 
    QComboBox, QStackedWidget, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QButtonGroup, QApplication, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCursor, QColor, QFont as QtFont
import random
import string
from ui.utils.realism import generate_realistic_id, copy_to_clipboard
from services.compute_service import ComputeService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.instance_detail_view import InstanceDetailView
from ui.components.footer import Footer
from ui.components.modern_card import ResourceCard, CardContainer, EmptyStateCard, SkeletonCard
from ui.components.state_badge import AnimatedStateBadge
from ui.components.bulk_action_bar import BulkActionBar
from ui.components.action_buttons import (
    ActionButton, ResourceActionBar, create_action_button, COMMON_ACTIONS
)
from ui.components.tooltips import add_tooltip_to_widget, show_cloud_tooltip
from ui.components.notifications import NotificationManager
from ui.components.slide_in_drawer import SlideInDrawer
from ui.design_system import Colors, Fonts, Spacing, Animations
from datetime import datetime


class CreateInstanceDialog(QDialog):
    """Modern create instance dialog with educational tooltips"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Launch New Instance")
        self.setMinimumWidth(500)
        self._init_ui()
        self._apply_modern_style()
        
    def _init_ui(self):
        """Initialize dialog UI with modern styling"""
        layout = QVBoxLayout(self)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Header
        header = QLabel("Launch a New EC2 Instance")
        header.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.MD};
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Configure instance specifications")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: {Spacing.XL};
        """)
        layout.addWidget(subtitle)
        
        # Form fields with tooltips
        form_layout = QFormLayout()
        form_layout.setSpacing(int(Spacing.LG.replace('px', '')))
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Instance name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., web-server-prod")
        add_tooltip_to_widget(self.name_input, 'instance')
        name_label = QLabel("Instance Name:")
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Fonts.MEDIUM};")
        form_layout.addRow(name_label, self.name_input)
        
        # Instance type
        type_container = QWidget()
        type_layout = QHBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(8)
        
        self.type_input = QComboBox()
        self.type_input.addItems([
            "t2.micro (1 vCPU, 1 GB) - Free Tier",
            "t2.small (1 vCPU, 2 GB)",
            "t2.medium (2 vCPU, 4 GB)",
            "t2.large (2 vCPU, 8 GB)",
            "m5.large (2 vCPU, 8 GB)",
            "m5.xlarge (4 vCPU, 16 GB)",
        ])
        add_tooltip_to_widget(self.type_input, 'instance_type')
        type_layout.addWidget(self.type_input)
        
        type_label = QLabel("Instance Type:")
        type_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Fonts.MEDIUM};")
        form_layout.addRow(type_label, type_container)
        
        # Custom CPU/Memory (simplified for demo)
        cpu_container = QWidget()
        cpu_layout = QHBoxLayout(cpu_container)
        cpu_layout.setContentsMargins(0, 0, 0, 0)
        cpu_layout.setSpacing(12)
        
        self.cpu_input = QSpinBox()
        self.cpu_input.setMinimum(1)
        self.cpu_input.setMaximum(64)
        self.cpu_input.setValue(1)
        self.cpu_input.setSuffix(" vCPU")
        cpu_layout.addWidget(self.cpu_input)
        
        self.memory_input = QSpinBox()
        self.memory_input.setMinimum(512)
        self.memory_input.setMaximum(524288)
        self.memory_input.setValue(1024)
        self.memory_input.setSingleStep(512)
        self.memory_input.setSuffix(" MB")
        cpu_layout.addWidget(self.memory_input)
        
        cpu_label = QLabel("Custom Resources:")
        cpu_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Fonts.MEDIUM};")
        form_layout.addRow(cpu_label, cpu_container)
        
        # AMI / Image
        self.image_input = QComboBox()
        self.image_input.addItems([
            "Ubuntu 22.04 LTS",
            "Ubuntu 20.04 LTS",
            "Amazon Linux 2",
            "Debian Latest",
        ])
        # Map UI selections to Docker images
        self.image_map = {
            "Ubuntu 22.04 LTS": "ubuntu:22.04",
            "Ubuntu 20.04 LTS": "ubuntu:20.04",
            "Amazon Linux 2": "amazonlinux:2",
            "Debian Latest": "debian:latest",
        }
        add_tooltip_to_widget(self.image_input, 'ami')
        ami_label = QLabel("AMI (Image):")
        ami_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Fonts.MEDIUM};")
        form_layout.addRow(ami_label, self.image_input)
        
        layout.addLayout(form_layout)
        
        # Info box
        info_box = QLabel(
            "💡 <b>What is an EC2 Instance?</b><br>"
            "A virtual server in the cloud. Launch it in seconds, "
            "pay only for what you use, and scale up or down anytime."
        )
        info_box.setWordWrap(True)
        info_box.setStyleSheet(f"""
            QLabel {{
                background: {Colors.INFO_BG};
                border: 1px solid {Colors.INFO};
                border-radius: {Spacing.SM};
                padding: {Spacing.MD};
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.SMALL};
            }}
        """)
        layout.addWidget(info_box)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = ActionButton("Cancel", style='secondary', parent=self)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = ActionButton("Launch Instance", "🚀", style='success', parent=self)
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def _apply_modern_style(self):
        """Apply modern dialog styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.SURFACE}, stop:1 #1a2535);
                border-radius: 12px;
            }}
            QLineEdit, QSpinBox, QComboBox {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.SM};
                padding: 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                min-height: 40px;
            }}
            QLineEdit:hover, QSpinBox:hover, QComboBox:hover {{
                border-color: {Colors.ACCENT};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.ACCENT};
                background: {Colors.CARD_HOVER};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                selection-background-color: {Colors.ACCENT};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
    
    def get_values(self):
        """Get input values"""
        selected_image = self.image_input.currentText()
        return {
            "name": self.name_input.text().strip() or f"instance-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "cpu": self.cpu_input.value(),
            "memory": self.memory_input.value(),
            "image": self.image_map.get(selected_image, "ubuntu:22.04")  # Map to Docker image
        }


class ModernComputeView(QWidget):
    """Modern compute view with card-based layout"""
    
    def __init__(self, volume_service=None):
        super().__init__()
        self.compute_service = ComputeService()
        self.volume_service = volume_service
        self.current_instance_id = None
        self.table_instance_map = {}  # Row to instance ID mapping
        self.selected_items = []  # Track multi-selection
        self._init_ui()
        
        # Initial load
        QTimer.singleShot(100, self._load_instances)
    
    def resizeEvent(self, event):
        """Position drawer at right edge when window resizes"""
        super().resizeEvent(event)
        if hasattr(self, 'drawer'):
            drawer_width = 600
            self.drawer.setGeometry(
                self.width() - drawer_width,
                0,
                drawer_width,
                self.height()
            )
        
    def _init_ui(self):
        """Initialize modern UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget for list/detail views
        self.stacked_widget = QStackedWidget()
        
        # List view (card-based)
        self.list_widget = QWidget()
        self._init_list_view()
        self.stacked_widget.addWidget(self.list_widget)
        
        layout.addWidget(self.stacked_widget)
        
        # Slide-in drawer for resource details (overlay, positioned at right edge)
        self.drawer = SlideInDrawer(self)
        self.drawer.hide()  # Hidden by default
        
        # Bulk action bar (floating at bottom)
        self.bulk_action_bar = BulkActionBar(resource_type="instance", parent=self)
        self.bulk_action_bar.action_triggered.connect(self._handle_bulk_action)
        self.bulk_action_bar.selection_cleared.connect(self._clear_selection)
        layout.addWidget(self.bulk_action_bar)
        
        layout.addWidget(Footer())
    
    def _init_list_view(self):
        """Initialize card-based list view with clear section hierarchy"""
        layout = QVBoxLayout(self.list_widget)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # SECTION 1: Header with metrics (elevated)
        header = self._create_header()
        layout.addWidget(header)
        
        # Visual separator after metrics
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setLineWidth(2)
        separator.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent, 
                    stop:0.5 {Colors.BORDER}, 
                    stop:1 transparent);
                max-height: 2px;
                margin: {Spacing.LG} 0;
            }}
        """)
        layout.addWidget(separator)
        
        # SECTION 2: Action bar with view toggle
        action_row = QHBoxLayout()
        action_row.setSpacing(16)
        
        self.action_bar = ResourceActionBar("Instance", self)
        self.action_bar.create_clicked.connect(self.create_instance)
        self.action_bar.refresh_clicked.connect(self._load_instances)
        action_row.addWidget(self.action_bar)
        
        # Table-only interface - no view switching
        action_row.addStretch()
        
        layout.addLayout(action_row)
        
        # Spacing before resource list
        layout.addSpacing(int(Spacing.MD.replace('px', '')))
        
        # TABLE-ONLY VIEW (no cards)
        self.table_view = self._create_table_view()
        layout.addWidget(self.table_view)
    
    def _create_header(self) -> QWidget:
        """Create modern header with title and stats"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Left side: Title and icon
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(int(Spacing.SM.replace('px', '')))
        
        title_row = QHBoxLayout()
        title_row.setSpacing(int(Spacing.MD.replace('px', '')))
        
        icon = QLabel("🖥️")
        icon.setStyleSheet(f"font-size: {Fonts.HERO};")
        title_row.addWidget(icon)
        
        title = QLabel("EC2 Instances")
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        add_tooltip_to_widget(title, 'instance')
        title_row.addWidget(title)
        title_row.addStretch()
        
        left_layout.addLayout(title_row)
        
        subtitle = QLabel("Virtual servers in the cloud")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        left_layout.addWidget(subtitle)
        
        header_layout.addWidget(left_container)
        header_layout.addStretch()
        
        # Right side: Stats cards
        self.stats_container = QWidget()
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(int(Spacing.MD.replace('px', '')))
        
        self.total_stat = self._create_stat_card("0", "Total", Colors.INFO)
        self.running_stat = self._create_stat_card("0", "Running", Colors.SUCCESS)
        self.stopped_stat = self._create_stat_card("0", "Stopped", Colors.TEXT_MUTED)
        
        stats_layout.addWidget(self.total_stat)
        stats_layout.addWidget(self.running_stat)
        stats_layout.addWidget(self.stopped_stat)
        
        header_layout.addWidget(self.stats_container)
        
        return header
    
    def _create_stat_card(self, value: str, label: str, color: str) -> QFrame:
        """Create a mini stat card with dominant metrics"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.SM};
                padding: {Spacing.MD};
                min-width: 120px;
            }}
        """)
        # Add elevation shadow for depth
        card.setGraphicsEffect(self._create_shadow_effect())
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)
        
        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet(f"""
            font-size: {Fonts.METRIC_HUGE};
            font-weight: {Fonts.HEAVY};
            color: {color};
            letter-spacing: -1px;
        """)
        layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: {Fonts.METRIC_LABEL};
            color: {Colors.TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: {Fonts.SEMIBOLD};
        """)
        layout.addWidget(label_widget)
        
        return card
    
    def _create_shadow_effect(self):
        """Create elevation shadow for metric cards"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 60))
        shadow.setOffset(0, 4)
        return shadow
    
    def _create_table_view(self) -> QTableWidget:
        """Create AWS-style table with name-first priority and visible actions"""
        table = QTableWidget()
        table.setColumnCount(8)  # Added Actions column
        table.setHorizontalHeaderLabels([
            "", "Name", "Instance ID", "State", "Image", "Type", "Created", "Actions"
        ])
        
        # AWS-style table styling with elevated rows and zebra striping
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {Colors.BACKGROUND};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                gridline-color: transparent;
                selection-background-color: transparent;
            }}
            QTableWidget::item {{
                padding: 0;
                border: none;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background: rgba(59, 130, 246, 0.08);
            }}
            QTableWidget::item:selected {{
                background: rgba(59, 130, 246, 0.12);
            }}
            QHeaderView::section {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px 16px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                font-weight: {Fonts.SEMIBOLD};
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }}
        """)
        
        # AWS-style row configuration
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(72)  # Taller rows for name prominence
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        
        # Enable row clicks to open drawer (AWS behavior)
        table.cellClicked.connect(self._on_table_row_clicked)
        
        # Column widths: Checkbox=40, Name=280, ID=180, State=120, Type=140, Region=120, Created=140
        table.setColumnWidth(0, 40)   # Checkbox
        table.setColumnWidth(1, 280)  # Name (widest - PRIORITY)
        table.setColumnWidth(2, 180)  # Instance ID
        table.setColumnWidth(3, 120)  # State
        table.setColumnWidth(4, 140)  # Type
        table.setColumnWidth(5, 120)  # Region
        table.setColumnWidth(6, 140)  # Created
        
        # Store instance IDs for row mapping
        self.table_instance_map = {}  # row -> instance_id
        
        return table
        
        # Column sizing
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # State
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Region
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Created
        
        # Enable sorting and interaction
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)  # Enable multi-select
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.cellClicked.connect(self._on_table_row_clicked)
        table.doubleClicked.connect(self._on_table_row_double_clicked)
        table.itemSelectionChanged.connect(self._on_table_selection_changed)
        
        return table
    
    def _on_table_row_clicked(self, row, column):
        """Handle single-click on table row to show drawer"""
        instance_id = self.table_view.item(row, 0).data(Qt.UserRole)
        if instance_id:
            self.show_instance_details(instance_id)
    
    def _on_table_row_double_clicked(self, index):
        """Handle double-click on table row"""
        row = index.row()
        instance_id = self.table_view.item(row, 0).data(Qt.UserRole)
        if instance_id:
            self.show_instance_details(instance_id)
    
    def _update_stats(self):
        """Update statistics cards"""
        stats = self.compute_service.get_stats()
        
        self.total_stat.findChild(QLabel, "stat_value").setText(str(stats['total']))
        self.running_stat.findChild(QLabel, "stat_value").setText(str(stats['running']))
        self.stopped_stat.findChild(QLabel, "stat_value").setText(str(stats['stopped']))
    
    def _load_instances(self):
        """Load instances with loading indicator"""
        self.action_bar.set_loading(True)
        
        # Render after short delay
        QTimer.singleShot(200, self._render_instances)
    
    def _render_instances(self):
        """Render instances in table view only"""
        self.action_bar.set_loading(False)
        instances = self.compute_service.list_instances()
        self._update_stats()
        
        # Always populate table with whatever is returned
        self._populate_table(instances)
    
    def _populate_table(self, instances):
        """AWS-style table with Name as PRIMARY anchor and hover-reveal actions"""
        self.table_view.setSortingEnabled(False)
        
        # Clear table before repopulating
        self.table_view.clearContents()
        self.table_view.setRowCount(0)
        
        # Set row count for new instances
        self.table_view.setRowCount(len(instances))
        self.table_instance_map = {}  # Clear mapping
        
        for row, instance in enumerate(instances):
            # Store instance ID for row clicks
            self.table_instance_map[row] = instance.id
            
            # Generate realistic ID if not set
            if not hasattr(instance, 'realistic_id'):
                instance.realistic_id = generate_realistic_id("i")
            
            # Zebra striping - very subtle
            row_bg = "rgba(30, 41, 59, 0.3)" if row % 2 == 0 else "transparent"
            
            # COLUMN 0: Checkbox for bulk selection
            checkbox_widget = QWidget()
            checkbox_widget.setStyleSheet(f"background: {row_bg};")
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(12, 0, 12, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            
            checkbox = QCheckBox()
            checkbox.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: 18px;
                    height: 18px;
                    border: 2px solid {Colors.BORDER};
                    border-radius: 4px;
                    background: {Colors.CARD};
                }}
                QCheckBox::indicator:hover {{
                    border-color: {Colors.COMPUTE};
                }}
                QCheckBox::indicator:checked {{
                    background: {Colors.COMPUTE};
                    border-color: {Colors.COMPUTE};
                    image: url(none);
                }}
            """)
            checkbox_layout.addWidget(checkbox)
            self.table_view.setCellWidget(row, 0, checkbox_widget)
            
            # COLUMN 1: NAME - PRIMARY VISUAL ANCHOR (+20% size, bold, always visible)
            name_widget = QWidget()
            name_widget.setStyleSheet(f"background: {row_bg};")
            name_layout = QVBoxLayout(name_widget)
            name_layout.setContentsMargins(16, 12, 8, 12)
            name_layout.setSpacing(6)
            
            # Instance name - DOMINANT (AWS style)
            display_name = instance.name if instance.name else "Unnamed instance"
            name_label = QLabel(display_name)
            name_font = QtFont()
            name_font.setPixelSize(17)  # +20% over 14px body
            name_font.setWeight(QtFont.DemiBold)  # SemiBold
            name_label.setFont(name_font)
            name_label.setStyleSheet(f"""
                color: {Colors.TEXT_PRIMARY if instance.name else Colors.TEXT_MUTED};
                {'' if instance.name else 'font-style: italic;'}
            """)
            name_label.setWordWrap(True)
            name_label.setMaximumHeight(40)  # Max 2 lines
            name_layout.addWidget(name_label)
            
            self.table_view.setCellWidget(row, 1, name_widget)
            
            # COLUMN 2: Instance ID with copy button (60% opacity)
            id_widget = QWidget()
            id_widget.setStyleSheet(f"background: {row_bg};")
            id_layout = QHBoxLayout(id_widget)
            id_layout.setContentsMargins(12, 0, 8, 0)
            id_layout.setSpacing(8)
            
            id_label = QLabel(instance.realistic_id)
            id_label.setStyleSheet(f"""
                color: {Colors.TEXT_SECONDARY};
                font-family: {Fonts.MONOSPACE};
                font-size: 12px;
                opacity: 0.6;
            """)
            id_layout.addWidget(id_label)
            
            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(24, 24)
            copy_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: none;
                    color: {Colors.TEXT_MUTED};
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    color: {Colors.COMPUTE};
                    background: rgba(59, 130, 246, 0.1);
                    border-radius: 4px;
                }}
            """)
            copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
            copy_btn.setToolTip(f"Copy {instance.realistic_id}")
            copy_btn.clicked.connect(lambda checked, id=instance.realistic_id: self._copy_to_clipboard(id))
            id_layout.addWidget(copy_btn)
            id_layout.addStretch()
            
            self.table_view.setCellWidget(row, 2, id_widget)
            
            # COLUMN 3: State badge (animated, professional)
            state_widget = QWidget()
            state_widget.setStyleSheet(f"background: {row_bg};")
            state_layout = QHBoxLayout(state_widget)
            state_layout.setContentsMargins(8, 0, 8, 0)
            state_layout.setAlignment(Qt.AlignLeft)
            
            state_badge = AnimatedStateBadge(instance.status)
            state_layout.addWidget(state_badge)
            state_layout.addStretch()
            
            self.table_view.setCellWidget(row, 3, state_widget)
            
            # COLUMN 4: Image (OS/AMI)
            image_widget = QWidget()
            image_widget.setStyleSheet(f"background: {row_bg};")
            image_layout = QHBoxLayout(image_widget)
            image_layout.setContentsMargins(12, 0, 8, 0)
            
            image_text = instance.image if instance.image else "ubuntu:22.04"
            image_label = QLabel(image_text)
            image_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px; font-family: {Fonts.MONOSPACE};")
            image_layout.addWidget(image_label)
            image_layout.addStretch()
            
            self.table_view.setCellWidget(row, 4, image_widget)
            
            # COLUMN 5: Instance Type
            type_widget = QWidget()
            type_widget.setStyleSheet(f"background: {row_bg};")
            type_layout = QHBoxLayout(type_widget)
            type_layout.setContentsMargins(12, 0, 8, 0)
            
            type_text = f"{instance.cpu}vCPU / {instance.memory}MB"
            type_label = QLabel(type_text)
            type_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-size: 13px;")
            type_layout.addWidget(type_label)
            type_layout.addStretch()
            
            self.table_view.setCellWidget(row, 5, type_widget)
            
            # COLUMN 6: Created timestamp
            created_widget = QWidget()
            created_widget.setStyleSheet(f"background: {row_bg};")
            created_layout = QHBoxLayout(created_widget)
            created_layout.setContentsMargins(12, 0, 8, 0)
            
            created_text = self._format_relative_time(instance)
            created_label = QLabel(created_text)
            created_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: 13px; opacity: 0.6;")
            created_layout.addWidget(created_label)
            created_layout.addStretch()
            
            self.table_view.setCellWidget(row, 6, created_widget)
            
            # COLUMN 7: Actions
            actions_widget = QWidget()
            actions_widget.setStyleSheet(f"background: {row_bg};")
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(8, 6, 8, 6)
            actions_layout.setSpacing(4)
            
            # Only show terminate button for STOPPED instances
            if instance.status == 'stopped':
                terminate_btn = QPushButton("Terminate")
                terminate_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: #ef4444;
                        border: 1px solid #ef4444;
                        padding: 4px 12px;
                        border-radius: 4px;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{
                        background: rgba(239, 68, 68, 0.1);
                    }}
                """)
                terminate_btn.setCursor(Qt.PointingHandCursor)
                terminate_btn.clicked.connect(lambda checked, id=instance.id: self.terminate_instance(id))
                actions_layout.addWidget(terminate_btn)
            
            actions_layout.addStretch()
            self.table_view.setCellWidget(row, 7, actions_widget)
        
        self.table_view.setSortingEnabled(True)
    
    def _on_table_row_clicked(self, row: int, column: int):
        """Handle table row click - open drawer (AWS behavior, not navigation)"""
        # Skip if clicking checkbox column
        if column == 0:
            return
        
        # Get instance ID from row mapping
        instance_id = self.table_instance_map.get(row)
        if instance_id:
            self.show_instance_details(instance_id)
    
    def _format_relative_time(self, instance) -> str:
        """Format creation time as relative (2h ago, 5m ago)"""
        if not hasattr(instance, 'created_at') or not instance.created_at:
            return 'N/A'
        
        try:
            # Simple relative time for demo
            from datetime import datetime
            # If created_at is a string, parse it
            if isinstance(instance.created_at, str):
                return instance.created_at  # Return as-is for now
            return 'Just now'  # Fallback
        except:
            return 'N/A'
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard and show notification"""
        copy_to_clipboard(text, show_notification=True)
    
    def _table_font(self, bold=False):
        """Get font for table cells"""
        from PySide6.QtGui import QFont
        font = QFont(Fonts.PRIMARY.replace("'", ""))
        font.setPixelSize(14)
        if bold:
            font.setBold(True)
        return font
    
    def _get_instance_actions(self, status: str) -> list:
        """Get available actions based on instance status"""
        status = status.lower()
        
        # State-based action visibility
        if status == 'running':
            return ['terminal', 'stop', 'restart', 'terminate']
        elif status == 'stopped':
            return ['start', 'terminate']
        elif status == 'pending':
            return []  # No actions while starting
        elif status == 'stopping':
            return []  # No actions while stopping
        elif status == 'rebooting':
            return []  # No actions while rebooting
        elif status == 'terminated':
            return []  # No actions on terminated instances
        else:
            return ['terminate']  # Default fallback
    
    def handle_card_action(self, action: str, instance_id: str):
        """Handle action triggered from card"""
        if action == 'terminal':
            self.open_terminal(instance_id)
            return
        
        action_map = {
            'start': self.start_instance,
            'stop': self.stop_instance,
            'restart': self.reboot_instance,
            'terminate': self.terminate_instance,
        }
        
        handler = action_map.get(action)
        if handler:
            handler(instance_id)
    
    def open_terminal(self, instance_id: str):
        """Open terminal dialog for instance"""
        instance = self.compute_service.get_instance(instance_id)
        if not instance:
            NotificationManager.show_error("Instance not found")
            return
        
        # Backend availability check
        if not self.compute_service.backend_available:
            NotificationManager.show_error("Backend not available. Please start the backend server.")
            return
        
        if instance.status != 'running':
            NotificationManager.show_error("Instance must be running to open terminal")
            return
        
        if not instance.container_id:
            NotificationManager.show_error("Container not created. Try stopping and starting the instance.")
            return
        
        # Create terminal dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Terminal - {instance.name}")
        dialog.setMinimumSize(800, 600)
        dialog.setStyleSheet(f"""
            QDialog {{
                background-color: {Colors.BACKGROUND};
            }}
        """)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create terminal widget - backend handles container management
        terminal = InstanceTerminal(
            instance_id=instance.id,
            instance_name=instance.name,
            compute_service=self.compute_service,
            instance_status=instance.status
        )
        layout.addWidget(terminal)
        
        dialog.exec()
    
    def create_instance(self):
        """Show create instance dialog"""
        dialog = CreateInstanceDialog(self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            try:
                # Create instance (backend handles persistence)
                instance = self.compute_service.create_instance(
                    name=values["name"],
                    cpu=values["cpu"],
                    memory=values["memory"],
                    image=values["image"]
                )
                
                # Explicitly refresh instance list
                self._load_instances()
                
                # Show success
                NotificationManager.show_success(
                    f"Instance '{instance.name}' created successfully!\n"
                    f"Instance ID: {instance.id}\n"
                    f"Status: {instance.status.upper()}",
                    duration=4000
                )
                
            except PermissionError as e:
                NotificationManager.show_error(f"Permission denied: {str(e)}")
                show_permission_denied(self, str(e))
            except Exception as e:
                NotificationManager.show_error(f"Failed to create instance: {str(e)}")
                show_error_dialog(self, "Create Instance Failed", str(e))
    
    def terminate_instance(self, instance_id: str):
        """Terminate an instance"""
        from ui.components.confirmation_dialog import confirm_action, TERMINATE_INSTANCE_CONSEQUENCES
        
        instance = self.compute_service.get_instance(instance_id)
        
        if confirm_action(
            self,
            "Terminate Instance",
            f"Are you sure you want to terminate instance '{instance.name}'?",
            TERMINATE_INSTANCE_CONSEQUENCES
        ):
            try:
                self.compute_service.terminate_instance(instance_id)
                
                NotificationManager.show_success(
                    f"Instance '{instance.name}' terminated successfully",
                    duration=3000
                )
                
                self._load_instances()
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Failed to terminate instance", str(e))
    
    def show_instance_details(self, instance_id: str):
        """Show detailed view for an instance in the slide-in drawer"""
        instance = self.compute_service.get_instance(instance_id)
        if not instance:
            NotificationManager.show_error(f"Instance {instance_id} not found")
            return
        
        self.current_instance_id = instance_id
        
        try:
            # Show details in the slide-in drawer instead of navigating to a new page
            self.drawer.show_resource(instance, "instance")
            
        except Exception as e:
            from ui.utils import show_error_dialog
            show_error_dialog(self, "Failed to load instance details", str(e))
    
    def show_list_view(self):
        """Return to list view"""
        self.stacked_widget.setCurrentIndex(0)
        
        # Clean up detail pages
        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Refresh list
        self._load_instances()
    
    def _on_table_selection_changed(self):
        """Handle table selection changes for bulk actions"""
        selected_rows = self.table_view.selectionModel().selectedRows()
        
        if not selected_rows:
            self.selected_items = []
            self.bulk_action_bar.update_selection([])
            return
        
        # Collect selected item data
        self.selected_items = []
        instances = self.compute_service.list_instances()
        
        for row_index in selected_rows:
            row = row_index.row()
            name_item = self.table_view.item(row, 0)
            if name_item:
                instance_id = name_item.data(Qt.UserRole)
                # Find instance by ID
                instance = next((i for i in instances if i.id == instance_id), None)
                if instance:
                    self.selected_items.append({
                        'id': instance.id,
                        'name': instance.name,
                        'status': instance.status,
                        'data': instance
                    })
        
        # Update bulk action bar
        self.bulk_action_bar.update_selection(self.selected_items)
    
    def _clear_selection(self):
        """Clear all selections"""
        self.table_view.clearSelection()
        self.selected_items = []
    
    def _handle_bulk_action(self, action: str, item_ids: list):
        """Handle bulk action execution"""
        if not item_ids:
            return
        
        count = len(item_ids)
        action_labels = {
            'start': ('Start', 'started'),
            'stop': ('Stop', 'stopped'),
            'restart': ('Restart', 'restarted'),
            'terminate': ('Terminate', 'terminated')
        }
        
        action_verb, past_tense = action_labels.get(action, (action.title(), f"{action}ed"))
        
        # Show initiating notification
        NotificationManager.show_info(
            f"{action_verb}ing {count} instance(s)...",
            duration=2000
        )
        
        # Show loading skeleton
        self.card_container.show_loading(count if count <= 3 else 3)
        
        # Confirmation for destructive actions
        if action == 'terminate':
            from ui.components.modern_dialogs import ConfirmationDialog
            
            BULK_TERMINATE_WARNING = [
                f"• {count} instance(s) will be permanently deleted",
                "• All data on instance storage will be lost",
                "• Attached volumes will be detached (but not deleted)",
                "• This action cannot be undone",
                "",
                "⚠️ This is a destructive operation!"
            ]
            
            if not ConfirmationDialog.show_dialog(
                self,
                f"Terminate {count} Instances",
                f"Are you sure you want to terminate {count} selected instance(s)?",
                BULK_TERMINATE_WARNING
            ):
                return
        
        # Execute action on all items
        success_count = 0
        failed_items = []
        
        for item_id in item_ids:
            try:
                if action == 'start':
                    self.compute_service.start_instance(item_id)
                elif action == 'stop':
                    self.compute_service.stop_instance(item_id)
                elif action == 'restart':
                    self.compute_service.restart_instance(item_id)
                elif action == 'terminate':
                    self.compute_service.terminate_instance(item_id)
                
                success_count += 1
                
            except PermissionError as e:
                failed_items.append(f"{item_id}: {str(e)}")
            except Exception as e:
                failed_items.append(f"{item_id}: {str(e)}")
        
        # Show detailed results
        if success_count > 0 and not failed_items:
            # Full success
            NotificationManager.show_success(
                f"✓ {success_count} instance(s) {past_tense} successfully\n"
                f"Operation completed without errors",
                duration=4000
            )
        elif success_count > 0 and failed_items:
            # Partial success
            NotificationManager.show_warning(
                f"⚠ {success_count} instance(s) {past_tense}\n"
                f"{len(failed_items)} operation(s) failed",
                duration=5000
            )
        
        if failed_items:
            error_msg = f"Failed to {action} {len(failed_items)} instance(s):\n"
            error_msg += "\n".join(failed_items[:3])  # Show first 3 errors
            if len(failed_items) > 3:
                error_msg += f"\n...and {len(failed_items) - 3} more"
            
            show_error_dialog(self, f"Bulk {action_verb} Errors", error_msg)
        
        # Clear selection and refresh
        self._clear_selection()
        self.bulk_action_bar.clear()
        QTimer.singleShot(300, self._load_instances)


# Export modern view as default
ComputeView = ModernComputeView
