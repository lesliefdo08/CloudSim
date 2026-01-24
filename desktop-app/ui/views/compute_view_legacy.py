"""
Compute View - EC2-like instance management interface
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QSpinBox, QMessageBox, QComboBox,
    QStackedWidget, QMenu
)
from PySide6.QtCore import Qt
from services.compute_service import ComputeService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from ui.components.compute_dialogs import AttachVolumeDialog, EditTagsDialog
from datetime import datetime


class CreateInstanceDialog(QDialog):
    """Dialog for creating a new instance"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Instance")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Instance name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., web-server-1")
        layout.addRow("Instance Name:", self.name_input)
        
        # CPU
        self.cpu_input = QSpinBox()
        self.cpu_input.setMinimum(1)
        self.cpu_input.setMaximum(8)
        self.cpu_input.setValue(1)
        self.cpu_input.setSuffix(" vCPU")
        layout.addRow("CPU:", self.cpu_input)
        
        # Memory
        self.memory_input = QSpinBox()
        self.memory_input.setMinimum(256)
        self.memory_input.setMaximum(8192)
        self.memory_input.setValue(512)
        self.memory_input.setSingleStep(256)
        self.memory_input.setSuffix(" MB")
        layout.addRow("Memory:", self.memory_input)
        
        # Image
        self.image_input = QComboBox()
        self.image_input.addItems([
            "ubuntu:latest",
            "alpine:latest",
            "python:3.9",
            "node:18"
        ])
        layout.addRow("Image:", self.image_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addRow(button_layout)
    
    def get_values(self):
        """Get input values"""
        return {
            "name": self.name_input.text().strip(),
            "cpu": self.cpu_input.value(),
            "memory": self.memory_input.value(),
            "image": self.image_input.currentText()
        }


class ComputeView(QWidget):
    """View for managing compute instances"""
    
    def __init__(self, volume_service=None):
        super().__init__()
        self.compute_service = ComputeService()
        self.volume_service = volume_service
        self.init_ui()
        self.refresh_instances()
        
    def init_ui(self):
        """Initialize the compute view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between list and detail views
        self.stacked_widget = QStackedWidget()
        
        # List view (instances table)
        self.list_widget = QWidget()
        self.init_list_view()
        self.stacked_widget.addWidget(self.list_widget)
        
        layout.addWidget(self.stacked_widget)
        layout.addWidget(Footer())
        
    def init_list_view(self):
        """Initialize the list view with instances table"""
        layout = QVBoxLayout(self.list_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Compute Instances")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        
        header_layout.addStretch()
        
        # Action buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_instances)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        create_btn = QPushButton("Create Instance")
        create_btn.clicked.connect(self.create_instance)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        header_layout.addWidget(create_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(16)
        
        # Instance table with modern styling and clickable rows
        from ui.design_system import Styles
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Instance ID", "Name", "Status", "CPU", "Memory", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellClicked.connect(self.show_instance_details)
        self.table.setStyleSheet(Styles.table() + """
            QTableWidget::item {
                cursor: pointer;
            }
            QTableWidget::item:hover {
                background: rgba(99, 102, 241, 0.1);
            }
        """)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        layout.addWidget(self.table)
        
    def refresh_instances(self):
        """Refresh the instance list"""
        instances = self.compute_service.list_instances()
        
        # Update stats
        stats = self.compute_service.get_stats()
        self.stats_label.setText(
            f"Total: {stats['total']} | Running: {stats['running']} | "
            f"Stopped: {stats['stopped']}"
        )
        
        # Clear table
        self.table.setRowCount(0)
        
        if not instances:
            # Show modern empty state
            from ui.design_system import create_empty_state
            self.table.setRowCount(1)
            empty_state = create_empty_state(
                "No Instances Yet",
                "Create your first EC2-like compute instance to get started.\nInstances provide virtual servers for running your applications.",
                "🖥️"
            )
            empty_state.setMinimumHeight(300)
            self.table.setCellWidget(0, 0, empty_state)
            self.table.setSpan(0, 0, 1, 6)
            self.table.setShowGrid(False)
            return
        
        # Populate table
        for row, instance in enumerate(instances):
            self.table.insertRow(row)
            
            # Instance ID
            self.table.setItem(row, 0, QTableWidgetItem(instance.id))
            
            # Name
            self.table.setItem(row, 1, QTableWidgetItem(instance.name))
            
            # Status with modern badge
            from ui.design_system import create_status_badge
            status_badge = create_status_badge(instance.status)
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(8, 4, 8, 4)
            status_layout.addWidget(status_badge)
            status_layout.addStretch()
            self.table.setCellWidget(row, 2, status_container)
            
            # CPU
            self.table.setItem(row, 3, QTableWidgetItem(f"{instance.cpu} vCPU"))
            
            # Memory
            self.table.setItem(row, 4, QTableWidgetItem(f"{instance.memory} MB"))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            if instance.status == "stopped":
                start_btn = QPushButton("Start")
                start_btn.clicked.connect(lambda checked, iid=instance.id: self.start_instance(iid))
                start_btn.setStyleSheet("background-color: #3498db; color: white; padding: 4px 8px; border: none; border-radius: 3px;")
                action_layout.addWidget(start_btn)
            elif instance.status == "running":
                stop_btn = QPushButton("Stop")
                stop_btn.clicked.connect(lambda checked, iid=instance.id: self.stop_instance(iid))
                stop_btn.setStyleSheet("background-color: #e67e22; color: white; padding: 4px 8px; border: none; border-radius: 3px;")
                action_layout.addWidget(stop_btn)
                
                reboot_btn = QPushButton("Reboot")
                reboot_btn.clicked.connect(lambda checked, iid=instance.id: self.reboot_instance(iid))
                reboot_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 4px 8px; border: none; border-radius: 3px;")
                action_layout.addWidget(reboot_btn)
            
            # More menu
            more_btn = QPushButton("⋮")
            more_btn.setStyleSheet("background-color: #95a5a6; color: white; padding: 4px 8px; border: none; border-radius: 3px;")
            more_btn.clicked.connect(lambda checked, iid=instance.id: self.show_more_actions(iid, more_btn))
            action_layout.addWidget(more_btn)
            
            self.table.setCellWidget(row, 5, action_widget)
    
    def create_instance(self):
        """Show create instance dialog"""
        dialog = CreateInstanceDialog(self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"]:
                show_error_dialog(self, "Error", "Instance name cannot be empty")
                return
            
            try:
                self.compute_service.create_instance(
                    name=values["name"],
                    cpu=values["cpu"],
                    memory=values["memory"],
                    image=values["image"]
                )
                self.refresh_instances()
                show_success_dialog(self, "Success", f"Instance '{values['name']}' created successfully!")
            except PermissionError as e:
                show_permission_denied(self, e, "create instances")
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def start_instance(self, instance_id: str):
        """Start an instance"""
        try:
            if self.compute_service.start_instance(instance_id):
                self.refresh_instances()
                show_success_dialog(self, "Success", "Instance started successfully!")
            else:
                show_error_dialog(self, "Error", "Failed to start instance")
        except PermissionError as e:
            show_permission_denied(self, e, "start instances")
    
    def stop_instance(self, instance_id: str):
        """Stop an instance"""
        try:
            if self.compute_service.stop_instance(instance_id):
                self.refresh_instances()
                show_success_dialog(self, "Success", "Instance stopped successfully!")
            else:
                show_error_dialog(self, "Error", "Failed to stop instance")
        except PermissionError as e:
            show_permission_denied(self, e, "stop instances")
    
    def reboot_instance(self, instance_id: str):
        """Reboot an instance"""
        try:
            if self.compute_service.reboot_instance(instance_id):
                self.refresh_instances()
                show_success_dialog(self, "Success", "Instance rebooted successfully!")
            else:
                show_error_dialog(self, "Error", "Failed to reboot instance")
        except PermissionError as e:
            show_permission_denied(self, e, "reboot instances")
    
    def terminate_instance(self, instance_id: str):
        """Terminate an instance"""
        reply = QMessageBox.question(
            self, "Confirm Terminate",
            "Are you sure you want to terminate this instance? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.compute_service.terminate_instance(instance_id):
                    self.refresh_instances()
                    show_success_dialog(self, "Success", "Instance terminated successfully!")
                else:
                    show_error_dialog(self, "Error", "Failed to terminate instance")
            except PermissionError as e:
                show_permission_denied(self, e, "terminate instances")
    
    def show_more_actions(self, instance_id: str, button: QPushButton):
        """Show more actions menu"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #34495e;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
        """)
        
        # Attach Volume
        attach_action = menu.addAction("📎 Attach Volume")
        attach_action.triggered.connect(lambda: self.attach_volume_dialog(instance_id))
        
        # Manage Volumes
        volumes_action = menu.addAction("💾 Manage Volumes")
        volumes_action.triggered.connect(lambda: self.manage_volumes_dialog(instance_id))
        
        # Edit Tags
        tags_action = menu.addAction("🏷️ Edit Tags")
        tags_action.triggered.connect(lambda: self.edit_tags_dialog(instance_id))
        
        menu.addSeparator()
        
        # Terminate
        terminate_action = menu.addAction("🗑️ Terminate")
        terminate_action.triggered.connect(lambda: self.terminate_instance(instance_id))
        
        # Show menu at button position
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def attach_volume_dialog(self, instance_id: str):
        """Show attach volume dialog with option for existing volumes"""
        # If we have VolumeService, show option to attach existing volumes
        if self.volume_service:
            from ui.components.volume_dialogs import AttachVolumeToInstanceDialog
            try:
                # Get available volumes
                available_volumes = self.volume_service.list_volumes(
                    user="admin",  # TODO: Use actual current user
                    state="available"
                )
                
                if available_volumes:
                    # Ask user: create new or use existing?
                    reply = QMessageBox.question(
                        self,
                        "Attach Volume",
                        f"Found {len(available_volumes)} available volume(s).\n\n"
                        "Do you want to attach an existing volume?\n\n"
                        "Click 'Yes' to select existing volume\n"
                        "Click 'No' to create a new volume",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Show existing volumes dialog
                        dialog = AttachVolumeToInstanceDialog(available_volumes, self)
                        if dialog.exec() == QDialog.Accepted:
                            volume, device = dialog.get_selected_volume_and_device()
                            if volume and device:
                                try:
                                    self.volume_service.attach_volume(
                                        volume.id,
                                        instance_id,
                                        device,
                                        user="admin"  # TODO: Use actual current user
                                    )
                                    self.refresh_instances()
                                    show_success_dialog(self, "Success", f"Volume '{volume.name}' attached successfully!")
                                except PermissionError as e:
                                    show_permission_denied(self, e, "attach volumes")
                                except Exception as e:
                                    show_error_dialog(self, "Error", str(e))
                        return
                    elif reply == QMessageBox.Cancel:
                        return
                    # If 'No', continue to create new volume below
            except:
                pass  # Fall back to creating new volume
        
        # Original dialog - create new volume
        dialog = AttachVolumeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"] or not values["device"]:
                show_error_dialog(self, "Error", "Volume name and device are required")
                return
            
            try:
                if self.compute_service.attach_volume(
                    instance_id,
                    values["name"],
                    values["size_gb"],
                    values["device"],
                    values["volume_type"]
                ):
                    self.refresh_instances()
                    show_success_dialog(self, "Success", f"Volume '{values['name']}' attached successfully!")
                else:
                    show_error_dialog(self, "Error", "Failed to attach volume")
            except PermissionError as e:
                show_permission_denied(self, e, "attach volumes")
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def manage_volumes_dialog(self, instance_id: str):
        """Show manage volumes dialog"""
        instance = self.compute_service.get_instance(instance_id)
        if not instance:
            return
        
        volumes = instance.get_volumes()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Manage Volumes - {instance.name}")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        
        # Volumes table
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Volume ID", "Name", "Size", "Type", "Device"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setRowCount(len(volumes))
        
        for row, vol in enumerate(volumes):
            table.setItem(row, 0, QTableWidgetItem(vol.id))
            table.setItem(row, 1, QTableWidgetItem(vol.name))
            table.setItem(row, 2, QTableWidgetItem(f"{vol.size_gb} GB"))
            table.setItem(row, 3, QTableWidgetItem(vol.volume_type))
            table.setItem(row, 4, QTableWidgetItem(vol.device or ""))
            
            # Add detach button for non-root volumes
            if vol.device != "/dev/sda1":
                detach_btn = QPushButton("Detach")
                detach_btn.clicked.connect(lambda checked, vid=vol.id: self.detach_volume(instance_id, vid, dialog))
                table.setCellWidget(row, 5, detach_btn)
        
        layout.addWidget(table)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def detach_volume(self, instance_id: str, volume_id: str, parent_dialog: QDialog):
        """Detach a volume"""
        try:
            if self.compute_service.detach_volume(instance_id, volume_id):
                self.refresh_instances()
                parent_dialog.accept()
                show_success_dialog(self, "Success", "Volume detached successfully!")
            else:
                show_error_dialog(self, "Error", "Failed to detach volume")
        except PermissionError as e:
            show_permission_denied(self, e, "detach volumes")
    
    def edit_tags_dialog(self, instance_id: str):
        """Show edit tags dialog"""
        instance = self.compute_service.get_instance(instance_id)
        if not instance:
            return
        
        dialog = EditTagsDialog(instance.tags, self)
        if dialog.exec() == QDialog.Accepted:
            tags = dialog.get_tags()
            
            try:
                if self.compute_service.update_instance_tags(instance_id, tags):
                    self.refresh_instances()
                    show_success_dialog(self, "Success", "Tags updated successfully!")
                else:
                    show_error_dialog(self, "Error", "Failed to update tags")
            except PermissionError as e:
                show_permission_denied(self, e, "update tags")
    
    def delete_instance(self, instance_id: str):
        """Delete an instance"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Are you sure you want to delete this instance?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.compute_service.delete_instance(instance_id):
                    self.refresh_instances()
                    QMessageBox.information(self, "Success", "Instance deleted successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to delete instance")
            except PermissionError as e:
                show_permission_denied(self, e, "delete instances")
    
    def show_instance_details(self, row, column):
        """Show instance detail page"""
        # Skip if clicking the actions column
        if column == 5:
            return
            
        instance_id = self.table.item(row, 0).text()
        instances = self.compute_service.list_instances()
        instance = next((i for i in instances if i.id == instance_id), None)
        
        if not instance:
            return
        
        # Get volumes info
        volumes = instance.get_volumes()
        volumes_info = {}
        for i, vol in enumerate(volumes):
            volumes_info[f"Volume {i+1}"] = f"{vol.name} ({vol.size_gb} GB {vol.volume_type}) @ {vol.device}"
        
        # Get state transitions
        transitions = instance.state_transitions[-5:] if len(instance.state_transitions) > 0 else []
        transition_info = {}
        for i, trans in enumerate(transitions):
            transition_info[f"Transition {i+1}"] = f"{trans['from_state']} → {trans['to_state']} at {trans['timestamp']}"
        
        # Prepare resource data for detail page with Storage tab
        resource_data = {
            "overview": {
                "basic": {
                    "Instance ID": instance.id,
                    "Name": instance.name,
                    "Instance Type": instance.instance_type,
                    "Status": instance.status.upper(),
                    "Image": instance.image,
                    "Region": instance.region
                },
                "status": {
                    "State": instance.status.upper(),
                    "Created": instance.created_at,
                    "Last Started": instance.last_start_time or "Never",
                    "Billing Hours": f"{instance.billing_hours:.2f} hrs",
                    "Estimated Cost": f"${instance.get_billing_cost():.2f}"
                }
            },
            "configuration": {
                "Compute": {
                    "Instance Type": instance.instance_type,
                    "CPU": f"{instance.cpu} vCPU",
                    "Memory": f"{instance.memory} MB"
                },
                "Network": {
                    "VPC": "default",
                    "Subnet": f"{instance.region}-1a",
                    "Private IP": "10.0.1.10"
                },
                "State Transitions": transition_info if transition_info else {"No transitions": "Instance not yet started"}
            },
            "storage": {
                "Attached Volumes": volumes_info,
                "Total Storage": f"{sum(v.size_gb for v in volumes)} GB"
            },
            "monitoring": {
                "Billing Hours": f"{instance.billing_hours:.2f} hrs",
                "Estimated Cost": f"${instance.get_billing_cost():.2f}",
                "CPU Utilization": "N/A (Future)",
                "Memory Usage": "N/A (Future)",
                "Network In": "N/A (Future)",
                "Network Out": "N/A (Future)"
            },
            "permissions": {
                "owner": instance.owner or "Unknown",
                "created_at": instance.created_at,
                "arn": instance.arn()
            },
            "tags": instance.tags
        }
        
        # Create and show detail page
        detail_page = ResourceDetailPage(
            resource_type="EC2 Instance",
            resource_name=instance.name,
            resource_data=resource_data,
            parent=self
        )
        
        # Connect back button
        detail_page.back_clicked.connect(self.show_list_view)
        
        # Add to stacked widget and show
        self.stacked_widget.addWidget(detail_page)
        self.stacked_widget.setCurrentWidget(detail_page)
    
    def show_list_view(self):
        """Show the list view"""
        # Switch back to list view
        self.stacked_widget.setCurrentIndex(0)
        
        # Remove detail pages (keep only list view at index 0)
        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Refresh the list
        self.refresh_instances()
