"""
Volume View - EBS-like storage management interface
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QHeaderView, QTableWidgetItem,
                             QMessageBox, QStackedWidget, QMenu, QDialog)
from PySide6.QtCore import Qt
from services.volume_service import VolumeService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from ui.components.volume_dialogs import (CreateVolumeDialog, CreateSnapshotDialog,
                                          CreateVolumeFromSnapshotDialog)


class VolumeView(QWidget):
    """Volume management view"""
    
    def __init__(self, volume_service: VolumeService, current_user: str, region: str):
        super().__init__()
        self.volume_service = volume_service
        self.current_user = current_user
        self.region = region
        
        self.init_ui()
        self.refresh_volumes()
    
    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for list/detail views
        self.stack = QStackedWidget()
        
        # List view
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Volumes (EBS)")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1976D2;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666;")
        header_layout.addWidget(self.stats_label)
        
        list_layout.addLayout(header_layout)
        list_layout.addSpacing(16)
        
        # Action buttons with modern styling
        from ui.design_system import Styles
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        create_btn = QPushButton("➕ Create Volume")
        create_btn.clicked.connect(self.create_volume_dialog)
        create_btn.setStyleSheet(Styles.success_button())
        button_layout.addWidget(create_btn)
        
        create_from_snapshot_btn = QPushButton("📸 Create from Snapshot")
        create_from_snapshot_btn.clicked.connect(self.create_from_snapshot_dialog)
        create_from_snapshot_btn.setStyleSheet(Styles.secondary_button())
        button_layout.addWidget(create_from_snapshot_btn)
        
        view_snapshots_btn = QPushButton("📂 View Snapshots")
        view_snapshots_btn.clicked.connect(self.view_snapshots)
        view_snapshots_btn.setStyleSheet(Styles.secondary_button())
        button_layout.addWidget(view_snapshots_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_volumes)
        refresh_btn.setStyleSheet(Styles.secondary_button())
        button_layout.addWidget(refresh_btn)
        
        button_layout.addStretch()
        list_layout.addLayout(button_layout)
        list_layout.addSpacing(16)
        
        # Volume table with modern styling and clickable rows
        self.volume_table = QTableWidget()
        self.volume_table.setColumnCount(7)
        self.volume_table.setHorizontalHeaderLabels([
            "ID", "Name", "Size", "Type", "State", "Attached To", "Actions"
        ])
        self.volume_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.volume_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.volume_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.volume_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.volume_table.cellClicked.connect(self.show_volume_details_by_row)
        self.volume_table.setStyleSheet(Styles.table() + """
            QTableWidget::item {
                cursor: pointer;
            }
            QTableWidget::item:hover {
                background: rgba(99, 102, 241, 0.1);
            }
        """)
        self.volume_table.verticalHeader().setVisible(False)
        self.volume_table.setShowGrid(False)
        list_layout.addWidget(self.volume_table)
        
        # Footer
        list_layout.addWidget(Footer())
        
        self.stack.addWidget(list_widget)
        layout.addWidget(self.stack)
        self.setLayout(layout)
    
    def refresh_volumes(self):
        """Refresh volume list"""
        try:
            volumes = self.volume_service.list_volumes(user=self.current_user, region=self.region)
            self.volume_table.setRowCount(len(volumes))
            
            for i, volume in enumerate(volumes):
                # ID
                self.volume_table.setItem(i, 0, QTableWidgetItem(volume.id))
                
                # Name
                self.volume_table.setItem(i, 1, QTableWidgetItem(volume.name))
                
                # Size
                self.volume_table.setItem(i, 2, QTableWidgetItem(f"{volume.size_gb} GB"))
                
                # Type
                self.volume_table.setItem(i, 3, QTableWidgetItem(volume.volume_type))
                
                # State with modern badge
                from ui.design_system import create_status_badge
                state_badge = create_status_badge(volume.state)
                state_container = QWidget()
                state_layout = QHBoxLayout(state_container)
                state_layout.setContentsMargins(8, 4, 8, 4)
                state_layout.addWidget(state_badge)
                state_layout.addStretch()
                self.volume_table.setCellWidget(i, 4, state_container)
                
                # Attached To
                attached_info = volume.get_attachment_info()
                self.volume_table.setItem(i, 5, QTableWidgetItem(attached_info))
                
                # Actions button
                actions_btn = QPushButton("⋮")
                actions_btn.setMaximumWidth(40)
                actions_btn.clicked.connect(lambda checked, v=volume: self.show_volume_actions(v, actions_btn))
                self.volume_table.setCellWidget(i, 6, actions_btn)
            
            # Update stats
            stats = self.volume_service.get_volume_stats()
            self.stats_label.setText(
                f"Total: {stats['total_volumes']} | "
                f"Available: {stats['available_volumes']} | "
                f"In Use: {stats['in_use_volumes']} | "
                f"Storage: {stats['total_storage_gb']} GB | "
                f"Snapshots: {stats['total_snapshots']}"
            )
            
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, f"Error loading volumes: {str(e)}")
    
    def create_volume_dialog(self):
        """Show create volume dialog"""
        dialog = CreateVolumeDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            volume_data = dialog.get_volume_data()
            try:
                self.volume_service.create_volume(
                    name=volume_data["name"],
                    size_gb=volume_data["size_gb"],
                    volume_type=volume_data["volume_type"],
                    region=self.region,
                    availability_zone=volume_data["availability_zone"],
                    user=self.current_user,
                    encrypted=volume_data["encrypted"]
                )
                show_success_dialog(self, f"Volume '{volume_data['name']}' created successfully!")
                self.refresh_volumes()
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, f"Error creating volume: {str(e)}")
    
    def create_from_snapshot_dialog(self):
        """Show create volume from snapshot dialog"""
        try:
            snapshots = self.volume_service.list_snapshots(user=self.current_user)
            if not snapshots:
                QMessageBox.information(self, "No Snapshots", "No snapshots available. Create a snapshot from an existing volume first.")
                return
            
            dialog = CreateVolumeFromSnapshotDialog(snapshots, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                snapshot, volume_name = dialog.get_snapshot_and_name()
                if snapshot:
                    self.volume_service.create_volume(
                        name=volume_name,
                        size_gb=snapshot.size_gb,
                        volume_type=snapshot.volume_type,
                        region=self.region,
                        availability_zone="us-east-1a",
                        user=self.current_user,
                        snapshot_id=snapshot.id
                    )
                    show_success_dialog(self, f"Volume '{volume_name}' created from snapshot!")
                    self.refresh_volumes()
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, f"Error: {str(e)}")
    
    def show_volume_actions(self, volume, button):
        """Show context menu for volume actions"""
        menu = QMenu(self)
        
        # View Details
        details_action = menu.addAction("👁️ View Details")
        details_action.triggered.connect(lambda: self.show_volume_details(volume.id))
        
        menu.addSeparator()
        
        # Detach (only for in-use volumes)
        if volume.is_attached():
            detach_action = menu.addAction("📤 Detach Volume")
            detach_action.triggered.connect(lambda: self.detach_volume(volume.id))
        
        # Create Snapshot
        snapshot_action = menu.addAction("📸 Create Snapshot")
        snapshot_action.triggered.connect(lambda: self.create_snapshot_dialog(volume))
        
        menu.addSeparator()
        
        # Delete (only for available volumes)
        if volume.state == "available":
            delete_action = menu.addAction("🗑️ Delete Volume")
            delete_action.triggered.connect(lambda: self.delete_volume(volume.id))
        
        # Show menu at button position
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))
    
    def detach_volume(self, volume_id):
        """Detach a volume"""
        reply = QMessageBox.question(
            self,
            "Confirm Detach",
            "Are you sure you want to detach this volume?\n\nThe instance may lose access to the data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.volume_service.detach_volume(volume_id, user=self.current_user)
                show_success_dialog(self, "Volume detached successfully!")
                self.refresh_volumes()
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, f"Error detaching volume: {str(e)}")
    
    def create_snapshot_dialog(self, volume):
        """Show create snapshot dialog"""
        dialog = CreateSnapshotDialog(volume.name, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            snapshot_data = dialog.get_snapshot_data()
            try:
                self.volume_service.create_snapshot(
                    volume_id=volume.id,
                    snapshot_name=snapshot_data["name"],
                    description=snapshot_data["description"],
                    user=self.current_user
                )
                show_success_dialog(self, f"Snapshot '{snapshot_data['name']}' created successfully!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, f"Error creating snapshot: {str(e)}")
    
    def delete_volume(self, volume_id):
        """Delete a volume"""
        reply = QMessageBox.warning(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this volume?\n\n⚠️ This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.volume_service.delete_volume(volume_id, user=self.current_user)
                show_success_dialog(self, "Volume deleted successfully!")
                self.refresh_volumes()
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, f"Error deleting volume: {str(e)}")
    
    def show_volume_details_by_row(self, row, column):
        """Show volume details when row clicked"""
        # Skip if clicking the actions column
        if column == 6:
            return
            
        volume_id_item = self.volume_table.item(row, 0)
        if volume_id_item:
            self.show_volume_details(volume_id_item.text())
    
    def show_volume_details(self, volume_id):
        """Show volume detail page"""
        volume = self.volume_service.get_volume(volume_id)
        if not volume:
            return
        
        # Get snapshots for this volume
        snapshots_info = {}
        try:
            snapshots = self.volume_service.list_snapshots(user=self.current_user, volume_id=volume.id)
            if snapshots:
                for i, snap in enumerate(snapshots):
                    snapshots_info[f"Snapshot {i+1}"] = f"{snap.name} ({snap.id}) - {snap.size_gb} GB - Created: {snap.created_at}"
        except:
            pass
        
        # Build resource data for ResourceDetailPage
        resource_data = {
            "overview": {
                "basic": {
                    "Volume ID": volume.id,
                    "Name": volume.name,
                    "Size": f"{volume.size_gb} GB",
                    "Volume Type": volume.volume_type,
                    "State": volume.get_status_display(),
                    "Availability Zone": volume.availability_zone,
                    "Created": volume.created_at,
                    "Encrypted": "Yes" if volume.encrypted else "No"
                },
                "status": {
                    "State": volume.get_status_display(),
                    "Attached To": volume.attached_instance_id or "Not attached",
                    "Device": volume.attached_device or "N/A",
                    "Attached At": volume.attached_at or "N/A"
                }
            },
            "configuration": {
                "Volume Details": {
                    "Volume Type": volume.volume_type,
                    "Size": f"{volume.size_gb} GB",
                    "IOPS": str(volume.iops) if volume.iops else "N/A",
                    "Throughput": f"{volume.throughput} MB/s" if volume.throughput else "N/A",
                    "Encrypted": "Yes" if volume.encrypted else "No",
                    "Snapshot ID": volume.snapshot_id or "N/A"
                },
                "Snapshots": snapshots_info if snapshots_info else {"No snapshots": "Create a snapshot to back up this volume"}
            },
            "monitoring": {
                "Size": f"{volume.size_gb} GB",
                "Usage": "N/A (Future)",
                "Read IOPS": "N/A (Future)",
                "Write IOPS": "N/A (Future)"
            },
            "permissions": {
                "owner": volume.owner or "N/A",
                "created_at": volume.created_at,
                "arn": volume.get_arn()
            },
            "tags": volume.tags
        }
        
        # Create and show detail page
        detail_page = ResourceDetailPage(
            resource_type="EBS Volume",
            resource_name=volume.name,
            resource_data=resource_data,
            parent=self
        )
        
        # Connect back button
        detail_page.back_clicked.connect(self.return_to_list)
        
        # Add to stack and show
        if self.stack.count() > 1:
            old_detail = self.stack.widget(1)
            self.stack.removeWidget(old_detail)
            old_detail.deleteLater()
        
        self.stack.addWidget(detail_page)
        self.stack.setCurrentIndex(1)
    
    def view_snapshots(self):
        """Show snapshots view"""
        try:
            snapshots = self.volume_service.list_snapshots(user=self.current_user)
            
            if not snapshots:
                QMessageBox.information(self, "No Snapshots", "No snapshots found. Create a snapshot from a volume first.")
                return
            
            # Create simple dialog to show snapshots
            dialog = QMessageBox(self)
            dialog.setWindowTitle("Volume Snapshots")
            dialog.setIcon(QMessageBox.Icon.Information)
            
            snapshot_text = "Available Snapshots:\n\n"
            for snap in snapshots:
                snapshot_text += f"📸 {snap.name}\n"
                snapshot_text += f"   ID: {snap.id}\n"
                snapshot_text += f"   Volume: {snap.volume_id}\n"
                snapshot_text += f"   Size: {snap.size_gb} GB ({snap.volume_type})\n"
                snapshot_text += f"   Created: {snap.created_at}\n"
                if snap.description:
                    snapshot_text += f"   Description: {snap.description}\n"
                snapshot_text += "\n"
            
            dialog.setText(snapshot_text)
            dialog.exec()
            
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except Exception as e:
            show_error_dialog(self, f"Error loading snapshots: {str(e)}")
    
    def return_to_list(self):
        """Return to volume list view"""
        self.stack.setCurrentIndex(0)
        self.refresh_volumes()
