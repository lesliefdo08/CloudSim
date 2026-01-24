"""
Enhanced Bucket Detail View with Object Management
Object preview, drag-and-drop upload, and object actions
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QFileDialog, QScrollArea, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal, QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from ui.design_system import Colors, Fonts, Spacing
from ui.components.action_buttons import ActionButton
from ui.components.notifications import NotificationManager
from ui.components.storage_tooltips import get_storage_tooltip
from ui.utils import show_error_dialog
from datetime import datetime
import os


class ObjectPreviewPanel(QFrame):
    """Panel showing preview of selected object"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
            }}
        """)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize preview UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("📄 Object Preview")
        header.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(header)
        
        # Object name
        self.object_name = QLabel("Select an object to preview")
        self.object_name.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
            padding: {Spacing.SM};
        """)
        self.object_name.setWordWrap(True)
        layout.addWidget(self.object_name)
        
        # Metadata section
        self.metadata_container = QWidget()
        metadata_layout = QVBoxLayout(self.metadata_container)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(8)
        
        self.size_label = self._create_metadata_row("Size:", "—")
        self.type_label = self._create_metadata_row("Type:", "—")
        self.modified_label = self._create_metadata_row("Modified:", "—")
        
        metadata_layout.addWidget(self.size_label)
        metadata_layout.addWidget(self.type_label)
        metadata_layout.addWidget(self.modified_label)
        
        layout.addWidget(self.metadata_container)
        self.metadata_container.setVisible(False)
        
        # Preview area (for text files, images)
        self.preview_area = QTextEdit()
        self.preview_area.setReadOnly(True)
        self.preview_area.setPlaceholderText("Preview not available for this file type")
        self.preview_area.setStyleSheet(f"""
            QTextEdit {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                color: {Colors.TEXT_PRIMARY};
                font-family: {Fonts.MONOSPACE};
                font-size: {Fonts.SMALL};
                padding: {Spacing.MD};
            }}
        """)
        layout.addWidget(self.preview_area)
        self.preview_area.setVisible(False)
        
        layout.addStretch()
        
    def _create_metadata_row(self, label: str, value: str) -> QFrame:
        """Create metadata row"""
        row = QFrame()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)
        
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            font-weight: {Fonts.MEDIUM};
            color: {Colors.TEXT_SECONDARY};
            min-width: 80px;
        """)
        
        value_widget = QLabel(value)
        value_widget.setObjectName("value")
        value_widget.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_PRIMARY};
        """)
        
        row_layout.addWidget(label_widget)
        row_layout.addWidget(value_widget)
        row_layout.addStretch()
        
        return row
        
    def show_preview(self, object_name: str, object_data: dict):
        """Show preview for object"""
        self.object_name.setText(object_name)
        self.metadata_container.setVisible(True)
        
        # Update metadata
        size_mb = object_data.get('size', 0) / (1024 * 1024)
        self.size_label.findChild(QLabel, "value").setText(f"{size_mb:.2f} MB")
        self.type_label.findChild(QLabel, "value").setText(object_data.get('type', 'Unknown'))
        self.modified_label.findChild(QLabel, "value").setText(object_data.get('modified', 'Unknown'))
        
        # Try to show preview for text files
        file_path = object_data.get('path')
        if file_path and self._is_text_file(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(5000)  # First 5KB
                    if len(content) == 5000:
                        content += "\n\n... (preview truncated)"
                    self.preview_area.setPlainText(content)
                    self.preview_area.setVisible(True)
            except Exception:
                self.preview_area.setVisible(False)
        else:
            self.preview_area.setVisible(False)
            
    def _is_text_file(self, path: str) -> bool:
        """Check if file is likely text"""
        text_extensions = ['.txt', '.log', '.json', '.xml', '.csv', '.md', '.py', '.js', '.html', '.css']
        return any(path.lower().endswith(ext) for ext in text_extensions)
        
    def clear_preview(self):
        """Clear preview"""
        self.object_name.setText("Select an object to preview")
        self.metadata_container.setVisible(False)
        self.preview_area.setVisible(False)
        self.preview_area.clear()


class DropZoneWidget(QFrame):
    """Drag-and-drop upload zone"""
    
    files_dropped = Signal(list)  # List of file paths
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        self._init_ui()
        self._apply_style(False)
        
    def _init_ui(self):
        """Initialize drop zone UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        
        icon = QLabel("📤")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"font-size: 48px;")
        layout.addWidget(icon)
        
        title = QLabel("Drop files here to upload")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("or click to browse")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(subtitle)
        
    def _apply_style(self, dragging: bool):
        """Apply style based on drag state"""
        if dragging:
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba(99, 102, 241, 0.2), stop:1 rgba(99, 102, 241, 0.1));
                    border: 2px dashed {Colors.ACCENT};
                    border-radius: 8px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {Colors.SURFACE};
                    border: 2px dashed {Colors.BORDER};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {Colors.ACCENT};
                    background: rgba(99, 102, 241, 0.05);
                }}
            """)
            
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._apply_style(True)
            
    def dragLeaveEvent(self, event):
        """Handle drag leave"""
        self._apply_style(False)
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop"""
        self._apply_style(False)
        
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
                
        if files:
            self.files_dropped.emit(files)
            
    def mousePressEvent(self, event):
        """Handle click to browse"""
        if event.button() == Qt.MouseButton.LeftButton:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Files to Upload",
                "",
                "All Files (*.*)"
            )
            if files:
                self.files_dropped.emit(files)


class BucketDetailView(QWidget):
    """Enhanced bucket detail view with object management"""
    
    back_clicked = Signal()
    
    def __init__(self, bucket_name: str, storage_service, parent=None):
        super().__init__(parent)
        self.bucket_name = bucket_name
        self.storage_service = storage_service
        self._init_ui()
        self._load_objects()
        
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with back button
        header = self._create_header()
        layout.addWidget(header)
        
        # Usage visualization
        usage_bar = self._create_usage_bar()
        layout.addWidget(usage_bar)
        
        # Drop zone
        self.drop_zone = DropZoneWidget()
        self.drop_zone.files_dropped.connect(self._handle_files_dropped)
        layout.addWidget(self.drop_zone)
        
        # Splitter for objects and preview
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {Colors.BORDER};
                width: 2px;
            }}
        """)
        
        # Objects table
        objects_container = self._create_objects_table()
        splitter.addWidget(objects_container)
        
        # Preview panel
        self.preview_panel = ObjectPreviewPanel()
        splitter.addWidget(self.preview_panel)
        
        splitter.setSizes([600, 400])
        layout.addWidget(splitter, 1)
        
    def _create_header(self) -> QWidget:
        """Create header"""
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background: {Colors.CARD};
                border-bottom: 1px solid {Colors.BORDER};
                padding: {Spacing.LG};
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(16)
        
        # Back button
        back_btn = ActionButton(
            text="← Back",
            icon="",
            style="secondary"
        )
        back_btn.clicked.connect(self.back_clicked.emit)
        layout.addWidget(back_btn)
        
        # Bucket info
        bucket_info = QWidget()
        info_layout = QVBoxLayout(bucket_info)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        name = QLabel(f"🪣 {self.bucket_name}")
        name.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        info_layout.addWidget(name)
        
        subtitle = QLabel("Object storage bucket")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_SECONDARY};
        """)
        info_layout.addWidget(subtitle)
        
        layout.addWidget(bucket_info)
        layout.addStretch()
        
        # Actions
        refresh_btn = ActionButton(
            text="Refresh",
            icon="🔄",
            style="secondary"
        )
        refresh_btn.clicked.connect(self._load_objects)
        layout.addWidget(refresh_btn)
        
        return header
        
    def _create_usage_bar(self) -> QWidget:
        """Create storage usage bar"""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background: {Colors.SURFACE};
                border-bottom: 1px solid {Colors.BORDER};
                padding: {Spacing.MD};
            }}
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(8)
        
        # Usage label
        self.usage_label = QLabel("Storage: 0 MB used")
        self.usage_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_SECONDARY};
        """)
        layout.addWidget(self.usage_label)
        
        # Progress bar
        self.usage_bar = QFrame()
        self.usage_bar.setFixedHeight(8)
        self.usage_bar.setStyleSheet(f"""
            QFrame {{
                background: {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        
        bar_layout = QHBoxLayout(self.usage_bar)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        
        self.usage_fill = QFrame()
        self.usage_fill.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT}, stop:1 {Colors.ACCENT_HOVER});
                border-radius: 4px;
            }}
        """)
        bar_layout.addWidget(self.usage_fill)
        bar_layout.addStretch()
        
        layout.addWidget(self.usage_bar)
        
        return container
        
    def _create_objects_table(self) -> QWidget:
        """Create objects table"""
        container = QWidget()
        container.setStyleSheet(f"background: {Colors.BACKGROUND};")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Table header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)
        
        title = QLabel("📦 Objects")
        title.setStyleSheet(f"""
            font-size: {Fonts.HEADING};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        
        self.object_count_label = QLabel("0 objects")
        self.object_count_label.setStyleSheet(f"""
            font-size: {Fonts.SMALL};
            color: {Colors.TEXT_SECONDARY};
        """)
        header_layout.addWidget(self.object_count_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Table
        self.objects_table = QTableWidget()
        self.objects_table.setColumnCount(4)
        self.objects_table.setHorizontalHeaderLabels(["Name", "Size", "Modified", "Actions"])
        self.objects_table.horizontalHeader().setStretchLastSection(False)
        self.objects_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.objects_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.objects_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.objects_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.objects_table.setColumnWidth(1, 100)
        self.objects_table.setColumnWidth(2, 150)
        self.objects_table.setColumnWidth(3, 150)
        self.objects_table.verticalHeader().setVisible(False)
        self.objects_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.objects_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.objects_table.setAlternatingRowColors(True)
        self.objects_table.itemSelectionChanged.connect(self._on_selection_changed)
        
        self.objects_table.setStyleSheet(f"""
            QTableWidget {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                gridline-color: {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
            }}
            QTableWidget::item {{
                padding: 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: rgba(99, 102, 241, 0.2);
            }}
            QHeaderView::section {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_SECONDARY};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                font-weight: {Fonts.SEMIBOLD};
                font-size: {Fonts.SMALL};
            }}
            QTableWidget::item:alternate {{
                background: rgba(255, 255, 255, 0.02);
            }}
        """)
        
        layout.addWidget(self.objects_table)
        
        return container
        
    def _load_objects(self):
        """Load objects from bucket"""
        try:
            bucket = self.storage_service.get_bucket(self.bucket_name)
            if not bucket:
                return
                
            objects = self.storage_service.list_objects(self.bucket_name)
            
            # Update usage bar
            size_mb = bucket.total_size / (1024 * 1024)
            self.usage_label.setText(f"Storage: {size_mb:.2f} MB used • {len(objects)} objects")
            
            # Update usage fill (example: show percentage of 1GB)
            percentage = min(100, (size_mb / 1024) * 100)
            self.usage_fill.setFixedWidth(int(self.usage_bar.width() * percentage / 100))
            
            # Update table
            self.objects_table.setRowCount(len(objects))
            self.object_count_label.setText(f"{len(objects)} objects")
            
            for row, obj in enumerate(objects):
                # Name
                name_item = QTableWidgetItem(obj.key)
                name_item.setData(Qt.ItemDataRole.UserRole, obj)
                self.objects_table.setItem(row, 0, name_item)
                
                # Size
                size_mb = obj.size / (1024 * 1024)
                size_item = QTableWidgetItem(f"{size_mb:.2f} MB")
                self.objects_table.setItem(row, 1, size_item)
                
                # Modified
                modified = obj.last_modified.strftime('%Y-%m-%d %H:%M') if obj.last_modified else 'Unknown'
                modified_item = QTableWidgetItem(modified)
                self.objects_table.setItem(row, 2, modified_item)
                
                # Actions
                actions_widget = self._create_object_actions(obj)
                self.objects_table.setCellWidget(row, 3, actions_widget)
                
        except Exception as e:
            show_error_dialog(self, "Failed to load objects", str(e))
            
    def _create_object_actions(self, obj) -> QWidget:
        """Create action buttons for object"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)
        
        # Download button
        download_btn = QPushButton("⬇️")
        download_btn.setToolTip("Download")
        download_btn.setFixedSize(32, 32)
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid {Colors.INFO};
                border-radius: 4px;
                color: {Colors.INFO};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: rgba(59, 130, 246, 0.2);
            }}
        """)
        download_btn.clicked.connect(lambda: self._download_object(obj))
        layout.addWidget(download_btn)
        
        # Delete button
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("Delete")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(239, 68, 68, 0.1);
                border: 1px solid {Colors.DANGER};
                border-radius: 4px;
                color: {Colors.DANGER};
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.2);
            }}
        """)
        delete_btn.clicked.connect(lambda: self._delete_object(obj))
        layout.addWidget(delete_btn)
        
        layout.addStretch()
        
        return container
        
    def _on_selection_changed(self):
        """Handle object selection"""
        selected_items = self.objects_table.selectedItems()
        if selected_items:
            obj = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if obj:
                object_path = self.storage_service.storage_root / self.bucket_name / obj.key
                self.preview_panel.show_preview(obj.key, {
                    'size': obj.size,
                    'type': obj.content_type or 'Unknown',
                    'modified': obj.last_modified.strftime('%Y-%m-%d %H:%M') if obj.last_modified else 'Unknown',
                    'path': str(object_path)
                })
        else:
            self.preview_panel.clear_preview()
            
    def _handle_files_dropped(self, files: list):
        """Handle dropped files"""
        for file_path in files:
            try:
                file_name = os.path.basename(file_path)
                self.storage_service.upload_object(self.bucket_name, file_name, file_path)
                NotificationManager.show_success(f"Uploaded {file_name}")
            except Exception as e:
                NotificationManager.show_error(f"Failed to upload {file_name}: {str(e)}")
                
        self._load_objects()
        
    def _download_object(self, obj):
        """Download object"""
        try:
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Object",
                obj.key,
                "All Files (*.*)"
            )
            
            if save_path:
                self.storage_service.download_object(self.bucket_name, obj.key, save_path)
                NotificationManager.show_success(f"Downloaded {obj.key}")
        except Exception as e:
            show_error_dialog(self, "Failed to download", str(e))
            
    def _delete_object(self, obj):
        """Delete object"""
        from ui.components.confirmation_dialog import confirm_action
        
        if confirm_action(
            self,
            "Delete Object",
            f"Are you sure you want to delete '{obj.key}'?",
            ["Object will be permanently deleted", "This action cannot be undone"]
        ):
            try:
                self.storage_service.delete_object(self.bucket_name, obj.key)
                NotificationManager.show_success(f"Deleted {obj.key}")
                self._load_objects()
            except Exception as e:
                show_error_dialog(self, "Failed to delete", str(e))
