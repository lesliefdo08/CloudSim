"""
S3 Service View - Bucket and object management with professional styling
Implements: Empty states, design system consistency, improved UX
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QInputDialog, QMessageBox,
    QFileDialog, QSplitter, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from api.client import APIClient
from ui.design_system import Colors, Fonts, Spacing, Styles, create_empty_state


class S3View(QWidget):
    """S3 buckets and objects management view"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.current_bucket = None
        self.setup_ui()
        self.refresh_buckets()
        
    def setup_ui(self):
        """Setup the user interface with professional styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        title = QLabel("S3 Storage")
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.create_bucket_btn = QPushButton("+  Create Bucket")
        self.create_bucket_btn.clicked.connect(self.create_bucket)
        self.create_bucket_btn.setStyleSheet(Styles.primary_button())
        self.create_bucket_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.refresh_buckets)
        self.refresh_btn.setStyleSheet(Styles.secondary_button())
        self.refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        header_layout.addWidget(self.create_bucket_btn)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)
        
        # Split view: Buckets | Objects
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {Colors.BORDER}; }}")
        
        # Buckets list
        buckets_widget = QWidget()
        buckets_layout = QVBoxLayout(buckets_widget)
        buckets_layout.setContentsMargins(0, 0, 0, 0)
        buckets_layout.setSpacing(12)
        
        buckets_label = QLabel("Buckets")
        buckets_label.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
            padding: 8px 0;
        """)
        buckets_layout.addWidget(buckets_label)
        
        self.buckets_list = QListWidget()
        self.buckets_list.itemClicked.connect(self.on_bucket_selected)
        self.buckets_list.setStyleSheet(f"""
            QListWidget {{
                background: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 2px;
                padding: 4px;
                font-size: {Fonts.BODY};
            }}
            QListWidget::item {{
                padding: 12px 10px;
                border: none;
                border-bottom: 1px solid {Colors.TABLE_BORDER};
            }}
            QListWidget::item:hover {{
                background: {Colors.TABLE_ROW_HOVER};
            }}
            QListWidget::item:selected {{
                background: {Colors.TABLE_SELECTED};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        buckets_layout.addWidget(self.buckets_list)
        
        delete_bucket_btn = QPushButton("Delete Bucket")
        delete_bucket_btn.clicked.connect(self.delete_bucket)
        delete_bucket_btn.setStyleSheet(Styles.danger_button())
        delete_bucket_btn.setCursor(QCursor(Qt.PointingHandCursor))
        buckets_layout.addWidget(delete_bucket_btn)
        
        splitter.addWidget(buckets_widget)
        
        # Objects list
        objects_widget = QWidget()
        objects_layout = QVBoxLayout(objects_widget)
        objects_layout.setContentsMargins(0, 0, 0, 0)
        objects_layout.setSpacing(12)
        
        objects_header = QHBoxLayout()
        objects_header.setSpacing(8)
        
        self.objects_label = QLabel("Objects")
        self.objects_label.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
            padding: 8px 0;
        """)
        objects_header.addWidget(self.objects_label)
        objects_header.addStretch()
        
        self.upload_btn = QPushButton("⬆ Upload")
        self.upload_btn.clicked.connect(self.upload_object)
        self.upload_btn.setEnabled(False)
        self.upload_btn.setStyleSheet(Styles.success_button())
        self.upload_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.download_btn = QPushButton("⬇ Download")
        self.download_btn.clicked.connect(self.download_object)
        self.download_btn.setEnabled(False)
        self.download_btn.setStyleSheet(Styles.secondary_button())
        self.download_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        objects_header.addWidget(self.upload_btn)
        objects_header.addWidget(self.download_btn)
        objects_layout.addLayout(objects_header)
        
        self.objects_list = QListWidget()
        self.objects_list.itemClicked.connect(self.on_object_selected)
        self.objects_list.setStyleSheet(f"""
            QListWidget {{
                background: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 2px;
                padding: 4px;
                font-size: {Fonts.BODY};
            }}
            QListWidget::item {{
                padding: 12px 10px;
                border: none;
                border-bottom: 1px solid {Colors.TABLE_BORDER};
            }}
            QListWidget::item:hover {{
                background: {Colors.TABLE_ROW_HOVER};
            }}
            QListWidget::item:selected {{
                background: {Colors.TABLE_SELECTED};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        objects_layout.addWidget(self.objects_list)
        
        delete_object_btn = QPushButton("Delete Object")
        delete_object_btn.clicked.connect(self.delete_object)
        delete_object_btn.setStyleSheet(Styles.danger_button())
        delete_object_btn.setCursor(QCursor(Qt.PointingHandCursor))
        objects_layout.addWidget(delete_object_btn)
        
        splitter.addWidget(objects_widget)
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
    def refresh_buckets(self):
        """Refresh buckets list"""
        buckets = self.api_client.list_buckets()
        if buckets is None:
            return
            
        self.buckets_list.clear()
        for bucket in buckets:
            item = QListWidgetItem(f"📦 {bucket.get('bucket_name', 'N/A')}")
            item.setData(Qt.UserRole, bucket)
            self.buckets_list.addItem(item)
            
    def create_bucket(self):
        """Create new bucket"""
        bucket_name, ok = QInputDialog.getText(
            self, "Create Bucket",
            "Enter bucket name:"
        )
        
        if ok and bucket_name:
            if self.api_client.create_bucket(bucket_name):
                QMessageBox.information(self, "Success", f"Bucket '{bucket_name}' created")
                self.refresh_buckets()
                
    def delete_bucket(self):
        """Delete selected bucket"""
        current = self.buckets_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a bucket to delete")
            return
            
        bucket = current.data(Qt.UserRole)
        bucket_name = bucket.get("bucket_name")
        
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete bucket '{bucket_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.delete_bucket(bucket_name):
                QMessageBox.information(self, "Success", f"Bucket '{bucket_name}' deleted")
                self.refresh_buckets()
                self.objects_list.clear()
                self.current_bucket = None
                
    def on_bucket_selected(self, item: QListWidgetItem):
        """Handle bucket selection"""
        bucket = item.data(Qt.UserRole)
        self.current_bucket = bucket.get("bucket_name")
        self.objects_label.setText(f"Objects in {self.current_bucket}")
        self.upload_btn.setEnabled(True)
        self.refresh_objects()
        
    def refresh_objects(self):
        """Refresh objects list for current bucket"""
        if not self.current_bucket:
            return
            
        objects = self.api_client.list_objects(self.current_bucket)
        if objects is None:
            return
            
        self.objects_list.clear()
        for obj in objects:
            key = obj.get("key", "N/A")
            size = obj.get("size_bytes", 0)
            size_str = self.format_size(size)
            item = QListWidgetItem(f"📄 {key} ({size_str})")
            item.setData(Qt.UserRole, obj)
            self.objects_list.addItem(item)
            
    def format_size(self, bytes: int) -> str:
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
        
    def on_object_selected(self, item: QListWidgetItem):
        """Handle object selection"""
        self.download_btn.setEnabled(True)
        
    def upload_object(self):
        """Upload file to bucket"""
        if not self.current_bucket:
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select File to Upload",
            "", "All Files (*.*)"
        )
        
        if file_path:
            key = file_path.split('/')[-1].split('\\')[-1]
            if self.api_client.upload_object(self.current_bucket, key, file_path):
                QMessageBox.information(self, "Success", f"File uploaded: {key}")
                self.refresh_objects()
                
    def download_object(self):
        """Download selected object"""
        current = self.objects_list.currentItem()
        if not current or not self.current_bucket:
            return
            
        obj = current.data(Qt.UserRole)
        key = obj.get("key")
        
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save File",
            key, "All Files (*.*)"
        )
        
        if save_path:
            if self.api_client.download_object(self.current_bucket, key, save_path):
                QMessageBox.information(self, "Success", f"File downloaded: {key}")
                
    def delete_object(self):
        """Delete selected object"""
        current = self.objects_list.currentItem()
        if not current or not self.current_bucket:
            QMessageBox.warning(self, "No Selection", "Please select an object to delete")
            return
            
        obj = current.data(Qt.UserRole)
        key = obj.get("key")
        
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete '{key}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.delete_object(self.current_bucket, key):
                QMessageBox.information(self, "Success", f"Object '{key}' deleted")
                self.refresh_objects()
