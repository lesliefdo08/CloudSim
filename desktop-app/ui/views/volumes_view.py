"""
Volumes View - EBS-like block storage management
Volume cards with state indicators, attach/detach modals
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QFrame, QStackedWidget
)
from PySide6.QtCore import Qt, Signal, QTimer
from datetime import datetime
from services.volume_service import VolumeService
from ui.utils import show_permission_denied, show_error_dialog
from ui.components.modern_card import ResourceCard, CardContainer, EmptyStateCard
from ui.components.action_buttons import ActionButton, ResourceActionBar
from ui.components.tooltips import CloudTooltip
from ui.components.storage_tooltips import get_storage_tooltip
from ui.components.notifications import NotificationManager
from ui.design_system import Colors, Fonts, Spacing


class CreateVolumeDialog(QDialog):
    """Dialog for creating new EBS volume"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create EBS Volume")
        self.setMinimumWidth(550)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        
        # Header
        header = QLabel("💾 Create EBS Volume")
        header.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Block storage for EC2 instances")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: {Spacing.MD};
        """)
        layout.addWidget(subtitle)
        
        # Form
        form = QFormLayout()
        form.setSpacing(16)
        
        # Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my-volume")
        form.addRow(self._create_label("Volume Name:"), self.name_input)
        
        # Size
        size_container = QWidget()
        size_layout = QHBoxLayout(size_container)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)
        
        self.size_input = QSpinBox()
        self.size_input.setRange(1, 16384)  # 1 GB to 16 TB
        self.size_input.setValue(100)
        self.size_input.setSuffix(" GB")
        size_layout.addWidget(self.size_input)
        size_layout.addStretch()
        
        form.addRow(self._create_label("Size:"), size_container)
        
        # Volume type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "gp3 - General Purpose SSD (3,000 IOPS)",
            "gp2 - General Purpose SSD (legacy)",
            "io2 - Provisioned IOPS SSD (High performance)",
            "io1 - Provisioned IOPS SSD (legacy)",
            "st1 - Throughput Optimized HDD (Big data)",
            "sc1 - Cold HDD (Lowest cost)"
        ])
        
        # Add tooltip for volume types
        type_tooltip = CloudTooltip(get_storage_tooltip('volume_types'))
        type_tooltip_btn = QPushButton("ℹ️")
        type_tooltip_btn.setFixedSize(24, 24)
        type_tooltip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.ACCENT};
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
            }}
        """)
        type_tooltip_btn.clicked.connect(lambda: type_tooltip.show_at_widget(type_tooltip_btn))
        
        type_container = QWidget()
        type_layout = QHBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(8)
        type_layout.addWidget(self.type_combo)
        type_layout.addWidget(type_tooltip_btn)
        type_layout.addStretch()
        
        form.addRow(self._create_label("Volume Type:"), type_container)
        
        # Availability Zone
        self.az_combo = QComboBox()
        self.az_combo.addItems(["us-east-1a", "us-east-1b", "us-east-1c"])
        form.addRow(self._create_label("Availability Zone:"), self.az_combo)
        
        # Encryption
        self.encryption_check = QCheckBox("Encrypt this volume")
        self.encryption_check.setChecked(True)
        
        # Add tooltip for encryption
        encryption_tooltip = CloudTooltip(get_storage_tooltip('encryption'))
        encryption_tooltip_btn = QPushButton("ℹ️")
        encryption_tooltip_btn.setFixedSize(24, 24)
        encryption_tooltip_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                color: {Colors.ACCENT};
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {Colors.ACCENT_HOVER};
            }}
        """)
        encryption_tooltip_btn.clicked.connect(lambda: encryption_tooltip.show_at_widget(encryption_tooltip_btn))
        
        encryption_container = QWidget()
        encryption_layout = QHBoxLayout(encryption_container)
        encryption_layout.setContentsMargins(0, 0, 0, 0)
        encryption_layout.setSpacing(8)
        encryption_layout.addWidget(self.encryption_check)
        encryption_layout.addWidget(encryption_tooltip_btn)
        encryption_layout.addStretch()
        
        form.addRow("", encryption_container)
        
        layout.addLayout(form)
        
        # Info box
        info_box = QLabel(
            "💡 <b>EBS volumes:</b><br>"
            "• Must be in same AZ as EC2 instance<br>"
            "• Persist independently from instance lifecycle<br>"
            "• Can be attached to one instance at a time (except io2 Multi-Attach)<br>"
            "• Can take snapshots for backup and replication"
        )
        info_box.setWordWrap(True)
        info_box.setStyleSheet(f"""
            QLabel {{
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid {Colors.INFO};
                border-radius: 8px;
                padding: {Spacing.MD};
                color: {Colors.TEXT_SECONDARY};
                font-size: {Fonts.SMALL};
            }}
        """)
        layout.addWidget(info_box)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 20px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                font-weight: {Fonts.MEDIUM};
            }}
            QPushButton:hover {{
                background: {Colors.SURFACE_HOVER};
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Volume")
        create_btn.setFixedWidth(140)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.ACCENT};
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                color: white;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
            }}
            QPushButton:hover {{
                background: {Colors.ACCENT_HOVER};
            }}
        """)
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
    def _create_label(self, text: str) -> QLabel:
        """Create form label"""
        label = QLabel(text)
        label.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-weight: {Fonts.MEDIUM};
            font-size: {Fonts.BODY};
        """)
        return label
        
    def get_volume_data(self) -> dict:
        """Get volume data from form"""
        volume_type = self.type_combo.currentText().split(' - ')[0]
        return {
            'name': self.name_input.text(),
            'size_gb': self.size_input.value(),
            'volume_type': volume_type,
            'availability_zone': self.az_combo.currentText(),
            'encrypted': self.encryption_check.isChecked()
        }


class VolumesView(QWidget):
    """EBS volumes management view"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.volume_service = VolumeService()
        self.stacked_widget = QStackedWidget()
        self._init_ui()
        
    def _init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create list view
        list_view = self._create_list_view()
        self.stacked_widget.addWidget(list_view)
        
        main_layout.addWidget(self.stacked_widget)
        
    def _create_list_view(self) -> QWidget:
        """Create main list view with clear section hierarchy"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)
        
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
        
        # SECTION 2: Action bar
        self.action_bar = ResourceActionBar("Volume", self)
        self.action_bar.create_clicked.connect(self.create_volume)
        self.action_bar.refresh_clicked.connect(self._load_volumes)
        layout.addWidget(self.action_bar)
        
        # Spacing before resource list
        layout.addSpacing(16)
        
        # SECTION 3: Volume cards
        self.card_container = CardContainer()
        layout.addWidget(self.card_container, 1)
        
        # Load volumes
        QTimer.singleShot(100, self._load_volumes)
        
        return container
        
    def _create_header(self) -> QWidget:
        """Create header with stats"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(32)
        
        # Title side
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        title_row = QHBoxLayout()
        title_row.setSpacing(16)
        
        icon = QLabel("💽")
        icon.setStyleSheet(f"font-size: {Fonts.HERO};")
        title_row.addWidget(icon)
        
        title = QLabel("EBS Volumes")
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        
        # Add S3 vs EBS comparison tooltip
        comparison_tooltip = CloudTooltip(get_storage_tooltip('s3_vs_ebs'))
        tooltip_btn = QPushButton("ℹ️ S3 vs EBS")
        tooltip_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid {Colors.ACCENT};
                border-radius: 6px;
                padding: 6px 12px;
                color: {Colors.ACCENT};
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.MEDIUM};
            }}
            QPushButton:hover {{
                background: rgba(99, 102, 241, 0.2);
            }}
        """)
        tooltip_btn.clicked.connect(lambda: comparison_tooltip.show_at_widget(tooltip_btn))
        
        title_row.addWidget(title)
        title_row.addWidget(tooltip_btn)
        title_row.addStretch()
        
        left_layout.addLayout(title_row)
        
        subtitle = QLabel("Block storage for EC2 instances")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        left_layout.addWidget(subtitle)
        
        header_layout.addWidget(left_container)
        header_layout.addStretch()
        
        # Stats
        self.stats_container = QWidget()
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(16)
        
        self.total_volumes_stat = self._create_stat_card("0", "Volumes", Colors.VOLUMES)
        self.available_stat = self._create_stat_card("0", "Available", Colors.SUCCESS)
        self.in_use_stat = self._create_stat_card("0", "In-Use", Colors.WARNING)
        
        stats_layout.addWidget(self.total_volumes_stat)
        stats_layout.addWidget(self.available_stat)
        stats_layout.addWidget(self.in_use_stat)
        
        header_layout.addWidget(self.stats_container)
        
        return header
        
    def _create_stat_card(self, value: str, label: str, color: str) -> QFrame:
        """Create stat card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: {Spacing.MD};
                min-width: 110px;
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
        
    def _update_stats(self, volumes: list):
        """Update statistics"""
        available = sum(1 for v in volumes if v.state == 'available')
        in_use = sum(1 for v in volumes if v.state == 'in-use')
        
        self.total_volumes_stat.findChild(QLabel, "stat_value").setText(str(len(volumes)))
        self.available_stat.findChild(QLabel, "stat_value").setText(str(available))
        self.in_use_stat.findChild(QLabel, "stat_value").setText(str(in_use))
        
    def _load_volumes(self):
        """Load volumes"""
        self.action_bar.set_loading(True)
        self.card_container.show_loading(6)
        
        QTimer.singleShot(300, self._do_load_volumes)
        
    def _do_load_volumes(self):
        """Actually load volumes"""
        try:
            volumes = self.volume_service.list_volumes()
            
            self._update_stats(volumes)
            
            if not volumes:
                empty_card = EmptyStateCard(
                    title="No volumes",
                    message="Block storage volumes for attaching to instances",
                    icon="💽",
                    cta_text="Create Volume"
                )
                empty_card.create_clicked.connect(self.create_volume)
                self.card_container.clear_cards()
                self.card_container.add_card(empty_card)
            else:
                self.card_container.clear_cards()
                for volume in volumes:
                    card = self._create_volume_card(volume)
                    self.card_container.add_card(card)
                    
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, "Failed to load volumes", str(e))
        finally:
            self.action_bar.set_loading(False)
            
    def _create_volume_card(self, volume) -> ResourceCard:
        """Create volume card"""
        # State indicators
        state_colors = {
            'available': Colors.SUCCESS,
            'in-use': Colors.WARNING,
            'creating': Colors.INFO,
            'deleting': Colors.DANGER,
            'error': Colors.DANGER
        }
        
        state_color = state_colors.get(volume.state, Colors.TEXT_SECONDARY)
        
        # Build details list
        details = [
            ('💾 Size', f"{volume.size_gb} GB"),
            ('⚡ Type', volume.volume_type.upper()),
            ('🌍 AZ', volume.availability_zone),
        ]
        
        if volume.state == 'in-use' and volume.attached_instance_id:
            details.append(('🔗 Attached to', volume.attached_instance_id))
            details.append(('📍 Device', volume.device or 'N/A'))
        
        if volume.encrypted:
            details.append(('🔒 Encrypted', 'Yes'))
            
        # Get actions based on state
        actions = self._get_volume_actions(volume)
        
        card_data = {
            'id': volume.id,
            'name': volume.name,
            'status': volume.state,
            'status_color': state_color,
            'details': details,
            'actions': actions,
            'metadata': {
                'Created': volume.created_at.strftime('%Y-%m-%d %H:%M') if volume.created_at else 'N/A',
                'Owner': volume.owner or 'Unknown'
            }
        }
        
        card = ResourceCard(card_data)
        card.action_triggered.connect(self._handle_volume_action)
        
        return card
        
    def _get_volume_actions(self, volume) -> list:
        """Get available actions for volume based on state"""
        if volume.state == 'available':
            return ['attach', 'snapshot', 'delete']
        elif volume.state == 'in-use':
            return ['detach', 'snapshot']
        elif volume.state in ['creating', 'deleting']:
            return []  # No actions during transitions
        else:
            return ['delete']
            
    def _handle_volume_action(self, volume_id: str, action: str):
        """Handle volume action"""
        if action == 'attach':
            self.attach_volume(volume_id)
        elif action == 'detach':
            self.detach_volume(volume_id)
        elif action == 'snapshot':
            self.create_snapshot(volume_id)
        elif action == 'delete':
            self.delete_volume(volume_id)
            
    def create_volume(self):
        """Create new volume"""
        dialog = CreateVolumeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                data = dialog.get_volume_data()
                
                if not data['name']:
                    show_error_dialog(self, "Validation Error", "Volume name is required")
                    return
                    
                volume = self.volume_service.create_volume(
                    name=data['name'],
                    size_gb=data['size_gb'],
                    volume_type=data['volume_type'],
                    availability_zone=data['availability_zone'],
                    encrypted=data['encrypted']
                )
                
                NotificationManager.show_success(
                    f"Volume '{volume.name}' created successfully",
                    duration=4000
                )
                
                QTimer.singleShot(500, self._load_volumes)
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Failed to create volume", str(e))
                
    def attach_volume(self, volume_id: str):
        """Attach volume to instance"""
        # This would open the attach volume dialog (reuse from instance_detail_view)
        NotificationManager.show_info(
            "Attach volume from instance details view",
            duration=3000
        )
        
    def detach_volume(self, volume_id: str):
        """Detach volume"""
        from ui.components.confirmation_dialog import confirm_action
        
        volume = self.volume_service.get_volume(volume_id)
        if not volume:
            return
            
        if confirm_action(
            self,
            "Detach Volume",
            f"Detach volume '{volume.name}' from instance?",
            [
                "Volume will become available",
                "Ensure data is saved before detaching",
                "May cause application errors if in use"
            ]
        ):
            try:
                self.volume_service.detach_volume(volume_id)
                NotificationManager.show_success(f"Volume '{volume.name}' detached")
                QTimer.singleShot(500, self._load_volumes)
            except Exception as e:
                show_error_dialog(self, "Failed to detach volume", str(e))
                
    def create_snapshot(self, volume_id: str):
        """Create snapshot of volume"""
        volume = self.volume_service.get_volume(volume_id)
        if not volume:
            return
            
        try:
            snapshot = self.volume_service.create_snapshot(
                volume_id=volume_id,
                name=f"Snapshot of {volume.name}",
                description=f"Backup taken on {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            NotificationManager.show_success(
                f"Snapshot '{snapshot.name}' created",
                duration=4000
            )
        except Exception as e:
            show_error_dialog(self, "Failed to create snapshot", str(e))
            
    def delete_volume(self, volume_id: str):
        """Delete volume"""
        from ui.components.confirmation_dialog import confirm_action
        
        volume = self.volume_service.get_volume(volume_id)
        if not volume:
            return
            
        consequences = [
            "⚠️ Volume and all data will be permanently deleted",
            "⚠️ Cannot be recovered after deletion",
            "⚠️ Consider creating a snapshot first",
        ]
        
        if volume.state == 'in-use':
            consequences.insert(0, "❌ Volume is currently attached - detach first")
            NotificationManager.show_warning("Volume must be detached before deletion")
            return
            
        if confirm_action(
            self,
            "Delete Volume",
            f"Delete volume '{volume.name}'?",
            consequences
        ):
            try:
                self.volume_service.delete_volume(volume_id)
                NotificationManager.show_success(f"Volume '{volume.name}' deleted")
                QTimer.singleShot(500, self._load_volumes)
            except Exception as e:
                show_error_dialog(self, "Failed to delete volume", str(e))
    
    def show_list_view(self):
        """Return to list view"""
        self.stacked_widget.setCurrentIndex(0)
        self._load_volumes()
