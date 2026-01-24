"""
Storage View - S3-like bucket management interface
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QFileDialog,
    QSplitter, QStackedWidget
)
from PySide6.QtCore import Qt
from services.storage_service import StorageService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from datetime import datetime


class CreateBucketDialog(QDialog):
    """Dialog for creating a new bucket"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Bucket")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Bucket name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., my-data-bucket")
        layout.addRow("Bucket Name:", self.name_input)
        
        # Info label
        info = QLabel("Bucket names must be lowercase, 3-63 characters, alphanumeric with dashes")
        info.setStyleSheet("color: #666; font-size: 11px;")
        info.setWordWrap(True)
        layout.addRow("", info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2980b9;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #21618c;
            }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addRow(button_layout)
    
    def get_bucket_name(self):
        """Get bucket name"""
        return self.name_input.text().strip()


class StorageView(QWidget):
    """View for managing storage buckets"""
    
    def __init__(self):
        super().__init__()
        self.storage_service = StorageService()
        self.current_bucket = None
        self.init_ui()
        self.refresh_buckets()
        
    def init_ui(self):
        """Initialize the storage view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between list and detail views
        self.stacked_widget = QStackedWidget()
        
        # List view (buckets and objects)
        self.list_widget = QWidget()
        self.init_list_view()
        self.stacked_widget.addWidget(self.list_widget)
        
        layout.addWidget(self.stacked_widget)
        layout.addWidget(Footer())
        
    def init_list_view(self):
        """Initialize the list view with buckets table"""
        layout = QVBoxLayout(self.list_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Storage Buckets")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        
        header_layout.addStretch()
        
        # Action buttons with modern styling
        from ui.design_system import Styles
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_buckets)
        refresh_btn.setStyleSheet(Styles.secondary_button())
        header_layout.addWidget(refresh_btn)
        
        create_btn = QPushButton("Create Bucket")
        create_btn.clicked.connect(self.create_bucket)
        create_btn.setStyleSheet(Styles.success_button())
        header_layout.addWidget(create_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Create splitter for buckets and objects
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Bucket table
        bucket_widget = QWidget()
        bucket_layout = QVBoxLayout(bucket_widget)
        bucket_layout.setContentsMargins(0, 0, 0, 0)
        
        bucket_label = QLabel("Buckets")
        bucket_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        bucket_layout.addWidget(bucket_label)
        
        self.bucket_table = QTableWidget()
        self.bucket_table.setColumnCount(4)
        self.bucket_table.setHorizontalHeaderLabels(["Bucket Name", "Objects", "Size", "Actions"])
        self.bucket_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.bucket_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.bucket_table.setSelectionMode(QTableWidget.SingleSelection)
        self.bucket_table.setShowGrid(False)
        self.bucket_table.verticalHeader().setVisible(False)
        self.bucket_table.itemSelectionChanged.connect(self.on_bucket_selected)
        self.bucket_table.cellClicked.connect(self.show_bucket_details)
        self.bucket_table.setStyleSheet(Styles.table() + """
            QTableWidget::item {
                cursor: pointer;
            }
            QTableWidget::item:hover {
                background: rgba(99, 102, 241, 0.1);
            }
        """)
        bucket_layout.addWidget(self.bucket_table)
        
        splitter.addWidget(bucket_widget)
        
        # Right side - Object list
        object_widget = QWidget()
        object_layout = QVBoxLayout(object_widget)
        object_layout.setContentsMargins(0, 0, 0, 0)
        
        object_header = QHBoxLayout()
        self.object_label = QLabel("Select a bucket to view objects")
        self.object_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        object_header.addWidget(self.object_label)
        
        object_header.addStretch()
        
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.clicked.connect(self.upload_object)
        self.upload_btn.setEnabled(False)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 6px 12px;
                font-size: 11px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        object_header.addWidget(self.upload_btn)
        
        object_layout.addLayout(object_header)
        
        self.object_table = QTableWidget()
        self.object_table.setColumnCount(4)
        self.object_table.setHorizontalHeaderLabels(["Object Key", "Size", "Last Modified", "Actions"])
        self.object_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.object_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.object_table.setSelectionMode(QTableWidget.NoSelection)
        self.object_table.setShowGrid(False)
        self.object_table.verticalHeader().setVisible(False)
        self.object_table.setStyleSheet(Styles.table())
        object_layout.addWidget(self.object_table)
        
        splitter.addWidget(object_widget)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
    def refresh_buckets(self):
        """Refresh the bucket list"""
        buckets = self.storage_service.list_buckets()
        
        # Update stats
        total_buckets = len(buckets)
        total_objects = sum(b.object_count for b in buckets)
        total_size = sum(b.total_size for b in buckets)
        self.stats_label.setText(
            f"Buckets: {total_buckets} | Objects: {total_objects} | "
            f"Total Size: {self.format_size(total_size)}"
        )
        
        # Clear table
        self.bucket_table.setRowCount(0)
        
        if not buckets:
            # Show placeholder
            self.bucket_table.setRowCount(1)
            placeholder = QLabel("No buckets created yet. Click 'Create Bucket' to get started.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #888; padding: 40px;")
            self.bucket_table.setCellWidget(0, 0, placeholder)
            self.bucket_table.setSpan(0, 0, 1, 4)
            return
        
        # Populate table
        for row, bucket in enumerate(buckets):
            self.bucket_table.insertRow(row)
            
            # Bucket name
            self.bucket_table.setItem(row, 0, QTableWidgetItem(bucket.name))
            
            # Object count
            self.bucket_table.setItem(row, 1, QTableWidgetItem(str(bucket.object_count)))
            
            # Size
            self.bucket_table.setItem(row, 2, QTableWidgetItem(self.format_size(bucket.total_size)))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, name=bucket.name: self.delete_bucket(name))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    padding: 4px 8px;
                    border: none;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            action_layout.addWidget(delete_btn)
            
            self.bucket_table.setCellWidget(row, 3, action_widget)
    
    def on_bucket_selected(self):
        """Handle bucket selection"""
        selected_rows = self.bucket_table.selectedIndexes()
        if not selected_rows:
            self.current_bucket = None
            self.object_label.setText("Select a bucket to view objects")
            self.upload_btn.setEnabled(False)
            self.object_table.setRowCount(0)
            return
        
        # Get bucket name from first column of selected row
        row = selected_rows[0].row()
        bucket_name_item = self.bucket_table.item(row, 0)
        
        if bucket_name_item:
            self.current_bucket = bucket_name_item.text()
            self.object_label.setText(f"Objects in '{self.current_bucket}'")
            self.upload_btn.setEnabled(True)
            self.refresh_objects()
    
    def refresh_objects(self):
        """Refresh the object list for current bucket"""
        if not self.current_bucket:
            return
        
        try:
            objects = self.storage_service.list_objects(self.current_bucket)
            
            # Clear table
            self.object_table.setRowCount(0)
            
            if not objects:
                # Show placeholder
                self.object_table.setRowCount(1)
                placeholder = QLabel("No objects in this bucket. Click 'Upload File' to add files.")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("color: #888; padding: 40px;")
                self.object_table.setCellWidget(0, 0, placeholder)
                self.object_table.setSpan(0, 0, 1, 4)
                return
            
            # Populate table
            for row, obj in enumerate(objects):
                self.object_table.insertRow(row)
                
                # Object key
                self.object_table.setItem(row, 0, QTableWidgetItem(obj.key))
                
                # Size
                self.object_table.setItem(row, 1, QTableWidgetItem(self.format_size(obj.size)))
                
                # Last modified
                self.object_table.setItem(row, 2, QTableWidgetItem(obj.last_modified))
                
                # Actions
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 4, 4, 4)
                
                download_btn = QPushButton("Download")
                download_btn.clicked.connect(lambda checked, key=obj.key: self.download_object(key))
                download_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                action_layout.addWidget(download_btn)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, key=obj.key: self.delete_object(key))
                delete_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #e74c3c;
                        color: white;
                        padding: 4px 8px;
                        border: none;
                        border-radius: 3px;
                    }
                    QPushButton:hover {
                        background-color: #c0392b;
                    }
                """)
                action_layout.addWidget(delete_btn)
                
                self.object_table.setCellWidget(row, 3, action_widget)
                
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def create_bucket(self):
        """Show create bucket dialog"""
        dialog = CreateBucketDialog(self)
        if dialog.exec() == QDialog.Accepted:
            bucket_name = dialog.get_bucket_name()
            
            if not bucket_name:
                show_error_dialog(self, "Error", "Bucket name cannot be empty")
                return
            
            try:
                self.storage_service.create_bucket(bucket_name)
                self.refresh_buckets()
                show_success_dialog(self, "Success", f"Bucket '{bucket_name}' created successfully!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def delete_bucket(self, bucket_name: str):
        """Delete a bucket"""
        bucket = self.storage_service.get_bucket(bucket_name)
        
        if bucket and bucket.object_count > 0:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Bucket '{bucket_name}' contains {bucket.object_count} object(s). "
                f"Are you sure you want to delete it and all its contents?",
                QMessageBox.Yes | QMessageBox.No
            )
        else:
            reply = QMessageBox.question(
                self, "Confirm Delete",
                f"Are you sure you want to delete bucket '{bucket_name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
        
        if reply == QMessageBox.Yes:
            try:
                self.storage_service.delete_bucket(bucket_name, force=True)
                if self.current_bucket == bucket_name:
                    self.current_bucket = None
                    self.object_table.setRowCount(0)
                    self.upload_btn.setEnabled(False)
                self.refresh_buckets()
                show_success_dialog(self, "Success", f"Bucket '{bucket_name}' deleted successfully!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def upload_object(self):
        """Upload a file to the current bucket"""
        if not self.current_bucket:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Upload",
            "",
            "All Files (*.*)"
        )
        
        if file_path:
            try:
                self.storage_service.upload_object(self.current_bucket, file_path)
                self.refresh_objects()
                self.refresh_buckets()  # Update bucket stats
                show_success_dialog(self, "Success", "File uploaded successfully!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def download_object(self, object_key: str):
        """Download an object from the current bucket"""
        if not self.current_bucket:
            return
        
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            object_key,
            "All Files (*.*)"
        )
        
        if dest_path:
            try:
                self.storage_service.download_object(self.current_bucket, object_key, dest_path)
                show_success_dialog(self, "Success", "File downloaded successfully!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def delete_object(self, object_key: str):
        """Delete an object from the current bucket"""
        if not self.current_bucket:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{object_key}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.storage_service.delete_object(self.current_bucket, object_key)
                self.refresh_objects()
                self.refresh_buckets()  # Update bucket stats
                show_success_dialog(self, "Success", "Object deleted successfully!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def show_bucket_details(self, row, column):
        """Show bucket detail page"""
        # Skip if clicking the actions column
        if column == 3:
            return
            
        bucket_name = self.bucket_table.item(row, 0).text()
        buckets = self.storage_service.list_buckets()
        bucket = next((b for b in buckets if b.name == bucket_name), None)
        
        if not bucket:
            return
        
        # Get objects in bucket
        objects = self.storage_service.list_objects(bucket_name)
        
        # Prepare resource data for detail page
        resource_data = {
            "overview": {
                "basic": {
                    "Bucket Name": bucket.name,
                    "Region": bucket.region,
                    "Object Count": str(bucket.object_count),
                    "Total Size": self.format_size(bucket.total_size)
                },
                "status": {
                    "Status": "Active",
                    "Created": bucket.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(bucket, 'created_at') else "N/A"
                }
            },
            "configuration": {
                "Storage": {
                    "Storage Class": "STANDARD",
                    "Versioning": "Disabled"
                },
                "Access": {
                    "Block Public Access": "Enabled",
                    "Encryption": "AES-256"
                }
            },
            "monitoring": {
                "Total Objects": str(bucket.object_count),
                "Total Size": self.format_size(bucket.total_size),
                "Average Object Size": self.format_size(bucket.total_size // bucket.object_count) if bucket.object_count > 0 else "0 B"
            },
            "permissions": {
                "owner": bucket.owner,
                "created_at": bucket.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(bucket, 'created_at') else "N/A",
                "arn": bucket.arn()
            },
            "tags": bucket.tags
        }
        
        # Create and show detail page
        detail_page = ResourceDetailPage(
            resource_type="S3 Bucket",
            resource_name=bucket.name,
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
        self.refresh_buckets()
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
