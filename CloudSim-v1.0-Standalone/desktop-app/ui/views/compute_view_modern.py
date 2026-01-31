"""
Modern Compute View - Card-based EC2 instance management
Vibrant, depth-layered design with smooth animations
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QDialog, QFormLayout, QLineEdit, QSpinBox, 
    QComboBox, QStackedWidget, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QCursor
from services.compute_service import ComputeService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from ui.components.modern_card import ResourceCard, CardContainer, EmptyStateCard, SkeletonCard
from ui.components.action_buttons import (
    ActionButton, ResourceActionBar, create_action_button, COMMON_ACTIONS
)
from ui.components.tooltips import add_tooltip_to_widget, show_cloud_tooltip
from ui.components.compute_dialogs import AttachVolumeDialog, EditTagsDialog
from ui.components.notifications import NotificationManager
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
            font-size: {Typography.SIZE_3XL};
            font-weight: {Typography.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: {Spacing.MD};
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Configure your virtual server with the specifications below")
        subtitle.setStyleSheet(f"""
            font-size: {Typography.SIZE_BASE};
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
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Typography.WEIGHT_MEDIUM};")
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
        type_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Typography.WEIGHT_MEDIUM};")
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
        cpu_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Typography.WEIGHT_MEDIUM};")
        form_layout.addRow(cpu_label, cpu_container)
        
        # AMI / Image
        self.image_input = QComboBox()
        self.image_input.addItems([
            "Amazon Linux 2023",
            "Ubuntu 22.04 LTS",
            "Windows Server 2022",
            "Red Hat Enterprise Linux 9",
            "Debian 11",
        ])
        add_tooltip_to_widget(self.image_input, 'ami')
        ami_label = QLabel("AMI (Image):")
        ami_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Typography.WEIGHT_MEDIUM};")
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
                padding: {Spacing.BASE};
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.SIZE_SM};
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
                font-size: {Typography.SIZE_BASE};
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
        return {
            "name": self.name_input.text().strip() or f"instance-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "cpu": self.cpu_input.value(),
            "memory": self.memory_input.value(),
            "image": self.image_input.currentText()
        }


class ModernComputeView(QWidget):
    """Modern compute view with card-based layout"""
    
    def __init__(self, volume_service=None):
        super().__init__()
        self.compute_service = ComputeService()
        self.volume_service = volume_service
        self.current_instance_id = None
        self._init_ui()
        
        # Initial load with skeleton
        QTimer.singleShot(100, self._load_instances)
        
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
        layout.addWidget(Footer())
    
    def _init_list_view(self):
        """Initialize card-based list view"""
        layout = QVBoxLayout(self.list_widget)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Header section
        header = self._create_header()
        layout.addWidget(header)
        
        # Action bar
        self.action_bar = ResourceActionBar("Instance", self)
        self.action_bar.create_clicked.connect(self.create_instance)
        self.action_bar.refresh_clicked.connect(self._load_instances)
        layout.addWidget(self.action_bar)
        
        # Card container
        self.card_container = CardContainer(self)
        layout.addWidget(self.card_container)
    
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
        icon.setStyleSheet(f"font-size: {Typography.SIZE_4XL};")
        title_row.addWidget(icon)
        
        title = QLabel("EC2 Instances")
        title.setStyleSheet(f"""
            font-size: {Typography.SIZE_3XL};
            font-weight: {Typography.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        add_tooltip_to_widget(title, 'instance')
        title_row.addWidget(title)
        title_row.addStretch()
        
        left_layout.addLayout(title_row)
        
        subtitle = QLabel("Virtual servers in the cloud")
        subtitle.setStyleSheet(f"""
            font-size: {Typography.SIZE_BASE};
            color: {Colors.TEXT_SECONDARY};
        """)
        left_layout.addWidget(subtitle)
        
        header_layout.addWidget(left_container)
        header_layout.addStretch()
        
        # Right side: Stats cards
        self.stats_container = QWidget()
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(int(Spacing.BASE.replace('px', '')))
        
        self.total_stat = self._create_stat_card("0", "Total", Colors.INFO)
        self.running_stat = self._create_stat_card("0", "Running", Colors.SUCCESS)
        self.stopped_stat = self._create_stat_card("0", "Stopped", Colors.TEXT_MUTED)
        
        stats_layout.addWidget(self.total_stat)
        stats_layout.addWidget(self.running_stat)
        stats_layout.addWidget(self.stopped_stat)
        
        header_layout.addWidget(self.stats_container)
        
        return header
    
    def _create_stat_card(self, value: str, label: str, color: str) -> QFrame:
        """Create a mini stat card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.SM};
                padding: {Spacing.BASE};
                min-width: 100px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        
        value_label = QLabel(value)
        value_label.setObjectName("stat_value")
        value_label.setStyleSheet(f"""
            font-size: {Typography.SIZE_3XL};
            font-weight: {Typography.WEIGHT_BOLD};
            color: {color};
        """)
        layout.addWidget(value_label)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: {Typography.SIZE_SM};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(label_widget)
        
        return card
    
    def _update_stats(self):
        """Update statistics cards"""
        stats = self.compute_service.get_stats()
        
        self.total_stat.findChild(QLabel, "stat_value").setText(str(stats['total']))
        self.running_stat.findChild(QLabel, "stat_value").setText(str(stats['running']))
        self.stopped_stat.findChild(QLabel, "stat_value").setText(str(stats['stopped']))
    
    def _load_instances(self):
        """Load instances with skeleton loading"""
        self.action_bar.set_loading(True)
        self.card_container.show_loading(5)
        
        # Simulate loading delay for smooth UX
        QTimer.singleShot(800, self._render_instances)
    
    def _render_instances(self):
        """Render instance cards"""
        self.action_bar.set_loading(False)
        instances = self.compute_service.list_instances()
        self._update_stats()
        
        self.card_container.clear_cards()
        
        if not instances:
            empty = self.card_container.show_empty(
                "No EC2 Instances",
                "Virtual servers for hosting applications, running workloads, and deploying services.",
                "🖥️",
                "Launch Instance"
            )
            empty.create_clicked.connect(self.create_instance)
            return
        
        # Create cards for each instance
        for instance in instances:
            card_data = {
                'icon': '🖥️',
                'name': instance.name,
                'id': instance.id,
                'status': instance.status,
                'details': {
                    'Image': instance.image,
                    'CPU': f"{instance.cpu} vCPU",
                    'Memory': f"{instance.memory} MB",
                    'Launched': instance.launch_time.strftime('%Y-%m-%d %H:%M:%S') if instance.launch_time else 'N/A',
                },
                'actions': self._get_instance_actions(instance.status)
            }
            
            card = ResourceCard(instance.id, card_data, self)
            card.clicked.connect(self.show_instance_details)
            card.action_triggered.connect(self.handle_card_action)
            
            self.card_container.add_card(card)
    
    def _get_instance_actions(self, status: str) -> list:
        """Get available actions based on instance status"""
        if status == 'running':
            return ['stop', 'restart', 'terminate']
        elif status == 'stopped':
            return ['start', 'terminate']
        else:
            return []
    
    def handle_card_action(self, action: str, instance_id: str):
        """Handle action triggered from card"""
        action_map = {
            'start': self.start_instance,
            'stop': self.stop_instance,
            'restart': self.reboot_instance,
            'terminate': self.terminate_instance,
        }
        
        handler = action_map.get(action)
        if handler:
            handler(instance_id)
    
    def create_instance(self):
        """Show create instance dialog"""
        dialog = CreateInstanceDialog(self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            try:
                instance = self.compute_service.create_instance(
                    name=values["name"],
                    cpu=values["cpu"],
                    memory=values["memory"],
                    image=values["image"]
                )
                
                NotificationManager.show_success(
                    f"Instance '{instance.name}' launched successfully!",
                    duration=5000
                )
                
                self._load_instances()
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Failed to create instance", str(e))
    
    def start_instance(self, instance_id: str):
        """Start an instance"""
        try:
            self.compute_service.start_instance(instance_id)
            instance = self.compute_service.get_instance(instance_id)
            
            NotificationManager.show_success(
                f"Instance '{instance.name}' starting...",
                duration=3000
            )
            
            QTimer.singleShot(500, self._load_instances)
            
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, "Failed to start instance", str(e))
    
    def stop_instance(self, instance_id: str):
        """Stop an instance"""
        try:
            self.compute_service.stop_instance(instance_id)
            instance = self.compute_service.get_instance(instance_id)
            
            NotificationManager.show_warning(
                f"Instance '{instance.name}' stopping...",
                duration=3000
            )
            
            QTimer.singleShot(500, self._load_instances)
            
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, "Failed to stop instance", str(e))
    
    def reboot_instance(self, instance_id: str):
        """Reboot an instance"""
        try:
            self.compute_service.reboot_instance(instance_id)
            instance = self.compute_service.get_instance(instance_id)
            
            NotificationManager.show_info(
                f"Instance '{instance.name}' rebooting...",
                duration=3000
            )
            
            QTimer.singleShot(500, self._load_instances)
            
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, "Failed to reboot instance", str(e))
    
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
                    duration=4000
                )
                
                QTimer.singleShot(500, self._load_instances)
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Failed to terminate instance", str(e))
    
    def show_instance_details(self, instance_id: str):
        """Show detailed view for an instance"""
        instance = self.compute_service.get_instance(instance_id)
        if not instance:
            return
        
        self.current_instance_id = instance_id
        
        # Create detail page
        detail_page = ResourceDetailPage(
            resource_type="instance",
            resource_id=instance_id,
            resource_data={
                'name': instance.name,
                'status': instance.status,
                'cpu': f"{instance.cpu} vCPU",
                'memory': f"{instance.memory} MB",
                'image': instance.image,
                'launch_time': instance.launch_time.strftime('%Y-%m-%d %H:%M:%S') if instance.launch_time else 'N/A',
            },
            parent=self
        )
        
        detail_page.back_clicked.connect(self.show_list_view)
        
        # Add to stack
        self.stacked_widget.addWidget(detail_page)
        self.stacked_widget.setCurrentWidget(detail_page)
    
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


# Export modern view as default
ComputeView = ModernComputeView
