"""
Enhanced Instance Detail View - EC2-style detailed instance management
With tabs: Overview, Storage (Volumes), Networking, Monitoring, Tags
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QScrollArea, QDialog, QFormLayout, QSpinBox, QComboBox, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
from services.compute_service import ComputeService
from services.volume_service import VolumeService
from ui.components.action_buttons import ActionButton, ActionButtonGroup, create_action_button
from ui.components.notifications import NotificationManager
from ui.components.confirmation_dialog import confirm_action
from ui.design_system import Colors, Fonts, Spacing
from ui.utils import show_error_dialog, show_permission_denied
from datetime import datetime


class AttachVolumeDialog(QDialog):
    """Dialog to attach a volume to instance"""
    
    def __init__(self, available_volumes: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attach Volume")
        self.setMinimumWidth(450)
        self.available_volumes = available_volumes
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Header
        header = QLabel("Attach EBS Volume to Instance")
        header.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(header)
        
        # Form
        form = QFormLayout()
        form.setSpacing(int(Spacing.MD.replace('px', '')))
        
        # Volume selection
        self.volume_combo = QComboBox()
        if self.available_volumes:
            for vol in self.available_volumes:
                self.volume_combo.addItem(f"{vol.name} ({vol.size_gb} GB) - {vol.id}", vol.id)
        else:
            self.volume_combo.addItem("No available volumes", None)
        
        form.addRow("Volume:", self.volume_combo)
        
        # Device name
        self.device_input = QLineEdit("/dev/sdf")
        form.addRow("Device:", self.device_input)
        
        layout.addLayout(form)
        
        # Info
        info = QLabel(
            "💡 The volume must be in the same availability zone as the instance.<br>"
            "Device name examples: /dev/sdf, /dev/sdg, etc."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid {Colors.INFO};
            border-radius: 6px;
            padding: {Spacing.MD};
            color: {Colors.TEXT_SECONDARY};
            font-size: {Fonts.SMALL};
        """)
        layout.addWidget(info)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel = ActionButton("Cancel", style='secondary', parent=self)
        cancel.clicked.connect(self.reject)
        btn_layout.addWidget(cancel)
        
        attach = ActionButton("Attach", "📎", style='success', parent=self)
        attach.clicked.connect(self.accept)
        btn_layout.addWidget(attach)
        
        layout.addLayout(btn_layout)
        
        self._apply_style()
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.SURFACE}, stop:1 #1a2535);
            }}
            QComboBox, QLineEdit {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 10px;
                color: {Colors.TEXT_PRIMARY};
                min-height: 36px;
            }}
            QComboBox:hover, QLineEdit:hover {{
                border-color: {Colors.ACCENT};
            }}
        """)
    
    def get_values(self):
        return {
            'volume_id': self.volume_combo.currentData(),
            'device': self.device_input.text().strip()
        }


class InstanceDetailView(QWidget):
    """Detailed instance view with EC2-style tabs"""
    
    back_clicked = Signal()
    
    def __init__(self, instance_id: str, compute_service: ComputeService, 
                 volume_service: VolumeService = None, parent=None):
        super().__init__(parent)
        self.instance_id = instance_id
        self.compute_service = compute_service
        self.volume_service = volume_service
        self.instance = self.compute_service.get_instance(instance_id)
        
        if not self.instance:
            raise ValueError(f"Instance {instance_id} not found")
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """Initialize tabbed detail UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with back button and actions
        header = self._create_header()
        layout.addWidget(header)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(self._tab_style())
        
        # Create tabs
        self.tabs.addTab(self._create_overview_tab(), "📋 Overview")
        self.tabs.addTab(self._create_storage_tab(), "💾 Storage")
        self.tabs.addTab(self._create_networking_tab(), "🌐 Networking")
        self.tabs.addTab(self._create_monitoring_tab(), "📊 Monitoring")
        self.tabs.addTab(self._create_tags_tab(), "🏷️ Tags")
        
        layout.addWidget(self.tabs)
    
    def _create_header(self) -> QWidget:
        """Create header with back button and quick actions"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border-bottom: 1px solid {Colors.BORDER};
                padding: {Spacing.LG};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(40, 20, 40, 20)
        
        # Back button
        back_btn = ActionButton("← Back", style='secondary', parent=self)
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        # Instance info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        
        name_label = QLabel(self.instance.name)
        name_label.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        info_layout.addWidget(name_label)
        
        id_label = QLabel(self.instance.id)
        id_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_MUTED};
            font-family: {Fonts.MONOSPACE};
        """)
        info_layout.addWidget(id_label)
        
        layout.addLayout(info_layout)
        
        # Status badge
        self.status_badge = self._create_status_badge()
        layout.addWidget(self.status_badge)
        
        layout.addStretch()
        
        # Quick actions
        self.action_group = ActionButtonGroup('horizontal', self)
        self._update_action_buttons()
        layout.addWidget(self.action_group)
        
        return header
    
    def _create_status_badge(self) -> QLabel:
        """Create animated status badge"""
        status = self.instance.status.lower()
        
        colors = {
            'running': (Colors.SUCCESS, '● Running'),
            'stopped': (Colors.TEXT_MUTED, '■ Stopped'),
            'pending': (Colors.WARNING, '◐ Pending'),
            'stopping': (Colors.WARNING, '◐ Stopping'),
            'rebooting': (Colors.INFO, '↻ Rebooting'),
            'terminated': (Colors.DANGER, '✕ Terminated'),
        }
        
        color, text = colors.get(status, (Colors.TEXT_SECONDARY, f'● {status.title()}'))
        
        badge = QLabel(text)
        badge.setStyleSheet(f"""
            QLabel {{
                background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15);
                color: {color};
                border: 1px solid {color};
                border-radius: 12px;
                padding: 8px 16px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
            }}
        """)
        return badge
    
    def _update_action_buttons(self):
        """Update action buttons based on instance state"""
        self.action_group.clear()
        
        status = self.instance.status.lower()
        
        # State-based actions
        if status == 'stopped':
            self.action_group.add_action(
                "Start", "▶️", "success",
                lambda: self._handle_action('start'),
                "Start the instance"
            )
        elif status == 'running':
            self.action_group.add_action(
                "Stop", "⏸️", "warning",
                lambda: self._handle_action('stop'),
                "Stop the instance"
            )
            self.action_group.add_action(
                "Reboot", "🔄", "info",
                lambda: self._handle_action('reboot'),
                "Reboot the instance"
            )
        
        # Always available (if not terminated)
        if status != 'terminated':
            self.action_group.add_action(
                "Terminate", "🗑️", "danger",
                lambda: self._handle_action('terminate'),
                "Permanently delete this instance"
            )
    
    def _create_overview_tab(self) -> QWidget:
        """Create overview tab with key details"""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        widget.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Instance details section
        layout.addWidget(self._create_section_header("Instance Details"))
        layout.addWidget(self._create_detail_group([
            ("Instance ID", self.instance.id),
            ("Instance Type", getattr(self.instance, 'instance_type', 't3.micro')),
            ("AMI", self.instance.image),
            ("Region", getattr(self.instance, 'region', 'us-east-1')),
            ("Created", getattr(self.instance, 'created_at', 'N/A')),
        ]))
        
        # Compute details
        layout.addWidget(self._create_section_header("Compute Resources"))
        layout.addWidget(self._create_detail_group([
            ("vCPUs", f"{self.instance.cpu} vCPU"),
            ("Memory", f"{self.instance.memory} MB"),
            ("Status", self.instance.status.title()),
        ]))
        
        # Owner info
        if hasattr(self.instance, 'owner') and self.instance.owner:
            layout.addWidget(self._create_section_header("Ownership"))
            layout.addWidget(self._create_detail_group([
                ("Owner", self.instance.owner),
            ]))
        
        layout.addStretch()
        widget.setWidget(content)
        return widget
    
    def _create_storage_tab(self) -> QWidget:
        """Create storage tab showing attached volumes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Header with action
        header_layout = QHBoxLayout()
        header_layout.addWidget(self._create_section_header("Block Devices (EBS Volumes)"))
        header_layout.addStretch()
        
        if self.volume_service and self.instance.status.lower() in ['running', 'stopped']:
            attach_btn = create_action_button('attach', self._attach_volume, self)
            header_layout.addWidget(attach_btn)
        
        layout.addLayout(header_layout)
        
        # Volumes table
        self.volumes_table = QTableWidget()
        self.volumes_table.setColumnCount(5)
        self.volumes_table.setHorizontalHeaderLabels([
            "Volume ID", "Size", "Type", "Device", "Actions"
        ])
        self.volumes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.volumes_table.setStyleSheet(self._table_style())
        self.volumes_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.volumes_table)
        
        self._load_volumes()
        
        return widget
    
    def _create_networking_tab(self) -> QWidget:
        """Create networking tab"""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        widget.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        layout.addWidget(self._create_section_header("Network Configuration"))
        
        # Simulated network info
        layout.addWidget(self._create_detail_group([
            ("VPC ID", "vpc-simulated"),
            ("Subnet", "subnet-1a"),
            ("Private IP", "10.0.1.42"),
            ("Public IP", "54.123.45.67" if self.instance.status == 'running' else "N/A"),
            ("Security Groups", "default"),
        ]))
        
        layout.addWidget(self._create_section_header("Firewall Rules"))
        info = QLabel("Security groups act as virtual firewalls controlling inbound/outbound traffic.")
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SMALL};")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        layout.addStretch()
        widget.setWidget(content)
        return widget
    
    def _create_monitoring_tab(self) -> QWidget:
        """Create monitoring tab"""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        widget.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        layout.addWidget(self._create_section_header("CloudWatch Metrics"))
        
        # Simulated metrics
        metrics_info = QLabel(
            "📊 <b>CPU Utilization:</b> 23%<br>"
            "🌐 <b>Network In:</b> 1.2 MB/s<br>"
            "🌐 <b>Network Out:</b> 0.8 MB/s<br>"
            "💾 <b>Disk Read:</b> 0.5 MB/s<br>"
            "💾 <b>Disk Write:</b> 0.3 MB/s"
        )
        metrics_info.setStyleSheet(f"""
            background: {Colors.CARD};
            border: 1px solid {Colors.BORDER};
            border-radius: 8px;
            padding: {Spacing.LG};
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            line-height: 1.8;
        """)
        layout.addWidget(metrics_info)
        
        layout.addWidget(self._create_section_header("Billing"))
        if hasattr(self.instance, 'billing_hours'):
            layout.addWidget(self._create_detail_group([
                ("Running Hours", f"{self.instance.billing_hours:.2f} hrs"),
                ("Estimated Cost", f"${self.instance.billing_hours * 0.01:.2f}"),
            ]))
        
        layout.addStretch()
        widget.setWidget(content)
        return widget
    
    def _create_tags_tab(self) -> QWidget:
        """Create tags tab"""
        widget = QScrollArea()
        widget.setWidgetResizable(True)
        widget.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        layout.addWidget(self._create_section_header("Tags"))
        
        info = QLabel("Tags help organize and track resources across your AWS account.")
        info.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; font-size: {Fonts.SMALL};")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Display tags
        if hasattr(self.instance, 'tags') and self.instance.tags:
            for key, value in self.instance.tags.items():
                tag_widget = self._create_tag_display(key, value)
                layout.addWidget(tag_widget)
        else:
            no_tags = QLabel("No tags defined")
            no_tags.setStyleSheet(f"color: {Colors.TEXT_MUTED}; font-style: italic;")
            layout.addWidget(no_tags)
        
        layout.addStretch()
        widget.setWidget(content)
        return widget
    
    def _create_section_header(self, title: str) -> QLabel:
        """Create section header label"""
        label = QLabel(title)
        label.setStyleSheet(f"""
            font-size: {Fonts.SUBTITLE};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
            margin-top: {Spacing.MD};
        """)
        return label
    
    def _create_detail_group(self, details: list) -> QFrame:
        """Create a group of key-value details"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: {Spacing.MD};
            }}
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(int(Spacing.SM.replace('px', '')))
        
        for key, value in details:
            row = QHBoxLayout()
            row.setSpacing(int(Spacing.MD.replace('px', '')))
            
            key_label = QLabel(f"{key}:")
            key_label.setStyleSheet(f"""
                color: {Colors.TEXT_MUTED};
                font-size: {Fonts.BODY};
                font-weight: {Fonts.MEDIUM};
                min-width: 150px;
            """)
            row.addWidget(key_label)
            
            value_label = QLabel(str(value))
            value_label.setStyleSheet(f"""
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                font-family: {Fonts.MONOSPACE if 'id' in key.lower() or 'ip' in key.lower() else Fonts.PRIMARY};
            """)
            value_label.setWordWrap(True)
            row.addWidget(value_label)
            row.addStretch()
            
            layout.addLayout(row)
        
        return frame
    
    def _create_tag_display(self, key: str, value: str) -> QFrame:
        """Create tag display widget"""
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: rgba(99, 102, 241, 0.1);
                border: 1px solid {Colors.ACCENT};
                border-radius: 6px;
                padding: {Spacing.SM};
            }}
        """)
        
        layout = QHBoxLayout(frame)
        
        key_label = QLabel(f"🏷️ {key}")
        key_label.setStyleSheet(f"color: {Colors.ACCENT}; font-weight: {Fonts.SEMIBOLD};")
        layout.addWidget(key_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        layout.addWidget(value_label)
        layout.addStretch()
        
        return frame
    
    def _load_volumes(self):
        """Load attached volumes"""
        if not self.volume_service:
            return
        
        self.volumes_table.setRowCount(0)
        
        # Get volumes attached to this instance
        volumes = [v for v in self.volume_service.list_volumes() 
                  if getattr(v, 'instance_id', None) == self.instance.id]
        
        for row, volume in enumerate(volumes):
            self.volumes_table.insertRow(row)
            
            self.volumes_table.setItem(row, 0, QTableWidgetItem(volume.id))
            self.volumes_table.setItem(row, 1, QTableWidgetItem(f"{volume.size_gb} GB"))
            self.volumes_table.setItem(row, 2, QTableWidgetItem(volume.volume_type))
            self.volumes_table.setItem(row, 3, QTableWidgetItem(getattr(volume, 'device', '/dev/sdf')))
            
            # Detach button
            detach_btn = QPushButton("Detach")
            detach_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.WARNING};
                    color: white;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                    font-weight: {Fonts.SEMIBOLD};
                }}
                QPushButton:hover {{
                    background: #d97706;
                }}
            """)
            detach_btn.clicked.connect(lambda checked, vid=volume.id: self._detach_volume(vid))
            self.volumes_table.setCellWidget(row, 4, detach_btn)
    
    def _attach_volume(self):
        """Show attach volume dialog"""
        if not self.volume_service:
            return
        
        # Get available volumes
        all_volumes = self.volume_service.list_volumes()
        available = [v for v in all_volumes if v.status == 'available']
        
        if not available:
            NotificationManager.show_warning("No available volumes to attach")
            return
        
        dialog = AttachVolumeDialog(available, self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            try:
                self.volume_service.attach_volume(
                    values['volume_id'],
                    self.instance.id,
                    values['device']
                )
                
                NotificationManager.show_success(f"Volume attached successfully")
                self._load_volumes()
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Attach Failed", str(e))
    
    def _detach_volume(self, volume_id: str):
        """Detach volume from instance"""
        if not self.volume_service:
            return
        
        if confirm_action(
            self,
            "Detach Volume",
            f"Detach volume {volume_id} from this instance?",
            [
                ("warning", "Instance may lose access to data on this volume"),
                ("info", "Volume will remain available for reattachment"),
            ]
        ):
            try:
                self.volume_service.detach_volume(volume_id)
                
                NotificationManager.show_success("Volume detached successfully")
                self._load_volumes()
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Detach Failed", str(e))
    
    def _handle_action(self, action: str):
        """Handle instance lifecycle actions"""
        action_map = {
            'start': (self.compute_service.start_instance, "Instance starting..."),
            'stop': (self.compute_service.stop_instance, "Instance stopping..."),
            'reboot': (self.compute_service.reboot_instance, "Instance rebooting..."),
        }
        
        if action == 'terminate':
            TERMINATE_CONSEQUENCES = [
                ("danger", "Instance will be permanently deleted"),
                ("danger", "All data on instance storage will be lost"),
                ("warning", "Attached EBS volumes will be detached but preserved"),
                ("info", "You can take a snapshot before terminating"),
            ]
            
            if not confirm_action(
                self,
                "Terminate Instance",
                f"Are you sure you want to terminate '{self.instance.name}'?",
                TERMINATE_CONSEQUENCES
            ):
                return
            
            try:
                self.compute_service.terminate_instance(self.instance.id)
                NotificationManager.show_success("Instance terminated")
                self.back_clicked.emit()
            except Exception as e:
                show_error_dialog(self, "Terminate Failed", str(e))
            return
        
        handler, message = action_map.get(action, (None, None))
        if handler:
            try:
                handler(self.instance.id)
                NotificationManager.show_info(message)
                
                # Refresh instance data
                QTimer.singleShot(500, self._reload_instance)
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, f"{action.title()} Failed", str(e))
    
    def _reload_instance(self):
        """Reload instance data and update UI"""
        self.instance = self.compute_service.get_instance(self.instance.id)
        if self.instance:
            # Update status badge
            new_badge = self._create_status_badge()
            old_badge = self.status_badge
            old_badge.deleteLater()
            self.status_badge = new_badge
            
            # Update action buttons
            self._update_action_buttons()
    
    def _load_data(self):
        """Initial data load"""
        self._load_volumes()
    
    def _tab_style(self) -> str:
        """Tab widget stylesheet"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                background: {Colors.SURFACE};
            }}
            QTabBar::tab {{
                background: {Colors.CARD};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px 24px;
                border: 1px solid {Colors.BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.MEDIUM};
            }}
            QTabBar::tab:selected {{
                background: {Colors.SURFACE};
                color: {Colors.ACCENT};
                border-bottom: 2px solid {Colors.ACCENT};
            }}
            QTabBar::tab:hover {{
                background: {Colors.SURFACE_HOVER};
                color: {Colors.TEXT_PRIMARY};
            }}
        """
    
    def _table_style(self) -> str:
        """Table stylesheet"""
        return f"""
            QTableWidget {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                gridline-color: {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item {{
                padding: 12px;
                border: none;
            }}
            QHeaderView::section {{
                background: {Colors.CARD};
                color: {Colors.TEXT_SECONDARY};
                padding: 12px;
                border: none;
                font-weight: {Fonts.SEMIBOLD};
                font-size: {Fonts.SMALL};
            }}
        """
