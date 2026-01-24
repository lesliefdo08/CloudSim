"""
Modern Storage View - Card-based S3 bucket management
Vibrant, visual bucket and object browsing
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QFormLayout, QLineEdit, QFileDialog, QStackedWidget,
    QFrame, QScrollArea, QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from services.storage_service import StorageService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from ui.components.modern_card import ResourceCard, CardContainer, EmptyStateCard
from ui.components.action_buttons import ActionButton, ResourceActionBar
from ui.components.tooltips import add_tooltip_to_widget
from ui.components.notifications import NotificationManager
from ui.design_system import Colors, Fonts, Spacing, Animations
from datetime import datetime


class CreateBucketDialog(QDialog):
    """Modern create bucket dialog"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create S3 Bucket")
        self.setMinimumWidth(500)
        self._init_ui()
        self._apply_modern_style()
        
    def _init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Header
        header = QLabel("Create a New S3 Bucket")
        header.setStyleSheet(f"""
            font-size: {Typography.SIZE_3XL};
            font-weight: {Typography.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        layout.addWidget(header)
        
        subtitle = QLabel("Buckets are containers for objects stored in Amazon S3")
        subtitle.setStyleSheet(f"""
            font-size: {Typography.SIZE_BASE};
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: {Spacing.BASE};
        """)
        layout.addWidget(subtitle)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(int(Spacing.LG.replace('px', '')))
        
        # Bucket name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my-unique-bucket-name")
        add_tooltip_to_widget(self.name_input, 'bucket')
        
        name_label = QLabel("Bucket Name:")
        name_label.setStyleSheet(f"color: {Colors.TEXT_PRIMARY}; font-weight: {Typography.WEIGHT_MEDIUM};")
        form_layout.addRow(name_label, self.name_input)
        
        # Public access warning
        self.public_checkbox = QCheckBox("Block all public access (recommended)")
        self.public_checkbox.setChecked(True)
        self.public_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.SIZE_BASE};
            }}
        """)
        form_layout.addRow("", self.public_checkbox)
        
        layout.addLayout(form_layout)
        
        # Info box
        info_box = QLabel(
            "⚠️ <b>Important:</b><br>"
            "Bucket names must be globally unique and DNS-compliant:<br>"
            "• 3-63 characters long<br>"
            "• Lowercase letters, numbers, and hyphens only<br>"
            "• Must start and end with letter or number"
        )
        info_box.setWordWrap(True)
        info_box.setStyleSheet(f"""
            QLabel {{
                background: {Colors.WARNING_BG};
                border: 1px solid {Colors.WARNING};
                border-radius: {Spacing.SM};
                padding: {Spacing.BASE};
                color: {Colors.TEXT_SECONDARY};
                font-size: {Typography.SIZE_SM};
            }}
        """)
        layout.addWidget(info_box)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        button_layout.addStretch()
        
        cancel_btn = ActionButton("Cancel", style='secondary', parent=self)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = ActionButton("Create Bucket", "📦", style='success', parent=self)
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
    
    def _apply_modern_style(self):
        """Apply modern styling"""
        self.setStyleSheet(f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.SURFACE}, stop:1 #1a2535);
            }}
            QLineEdit {{
                background: {Colors.CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: {Spacing.SM};
                padding: 12px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Typography.SIZE_BASE};
                min-height: 40px;
            }}
            QLineEdit:hover {{
                border-color: {Colors.ACCENT};
            }}
            QLineEdit:focus {{
                border-color: {Colors.ACCENT};
                background: {Colors.CARD_HOVER};
            }}
        """)
    
    def get_bucket_name(self):
        """Get bucket name"""
        return self.name_input.text().strip().lower()


class ModernStorageView(QWidget):
    """Modern storage view with card-based layout"""
    
    def __init__(self):
        super().__init__()
        self.storage_service = StorageService()
        self.current_bucket = None
        self._init_ui()
        
        QTimer.singleShot(100, self._load_buckets)
    
    def _init_ui(self):
        """Initialize modern UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Stacked widget for list/detail views
        self.stacked_widget = QStackedWidget()
        
        # List view
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
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Action bar
        self.action_bar = ResourceActionBar("Bucket", self)
        self.action_bar.create_clicked.connect(self.create_bucket)
        self.action_bar.refresh_clicked.connect(self._load_buckets)
        layout.addWidget(self.action_bar)
        
        # Card container
        self.card_container = CardContainer(self)
        layout.addWidget(self.card_container)
    
    def _create_header(self) -> QWidget:
        """Create header with stats"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(int(Spacing.XL.replace('px', '')))
        
        # Title side
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(int(Spacing.SM.replace('px', '')))
        
        title_row = QHBoxLayout()
        title_row.setSpacing(int(Spacing.MD.replace('px', '')))
        
        icon = QLabel("📦")
        icon.setStyleSheet(f"font-size: {Typography.SIZE_4XL};")
        title_row.addWidget(icon)
        
        title = QLabel("S3 Buckets")
        title.setStyleSheet(f"""
            font-size: {Typography.SIZE_3XL};
            font-weight: {Typography.WEIGHT_BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        add_tooltip_to_widget(title, 's3')
        title_row.addWidget(title)
        title_row.addStretch()
        
        left_layout.addLayout(title_row)
        
        subtitle = QLabel("Object storage for any amount of data")
        subtitle.setStyleSheet(f"""
            font-size: {Typography.SIZE_BASE};
            color: {Colors.TEXT_SECONDARY};
        """)
        left_layout.addWidget(subtitle)
        
        header_layout.addWidget(left_container)
        header_layout.addStretch()
        
        # Stats cards
        self.stats_container = QWidget()
        stats_layout = QHBoxLayout(self.stats_container)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.setSpacing(int(Spacing.BASE.replace('px', '')))
        
        self.total_buckets = self._create_stat_card("0", "Buckets", Colors.INFO)
        self.total_objects = self._create_stat_card("0", "Objects", Colors.SUCCESS)
        
        stats_layout.addWidget(self.total_buckets)
        stats_layout.addWidget(self.total_objects)
        
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
        """Update statistics"""
        buckets = self.storage_service.list_buckets()
        total_objects = sum(bucket.object_count for bucket in buckets)
        
        self.total_buckets.findChild(QLabel, "stat_value").setText(str(len(buckets)))
        self.total_objects.findChild(QLabel, "stat_value").setText(str(total_objects))
    
    def _load_buckets(self):
        """Load buckets with skeleton"""
        self.action_bar.set_loading(True)
        self.card_container.show_loading(4)
        
        QTimer.singleShot(600, self._render_buckets)
    
    def _render_buckets(self):
        """Render bucket cards"""
        self.action_bar.set_loading(False)
        buckets = self.storage_service.list_buckets()
        self._update_stats()
        
        self.card_container.clear_cards()
        
        if not buckets:
            empty = self.card_container.show_empty(
                "No S3 Buckets",
                "Store and retrieve any amount of data from anywhere. Supports backups, static websites, and application storage.",
                "📦",
                "Create Bucket"
            )
            empty.create_clicked.connect(self.create_bucket)
            return
        
        # Create cards for each bucket
        for bucket in buckets:
            # Calculate total size
            total_size = sum(obj.get('size', 0) for obj in bucket.objects)
            size_mb = total_size / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB" if size_mb > 0 else "Empty"
            
            card_data = {
                'icon': '📦',
                'name': bucket.name,
                'id': bucket.id,
                'status': 'available',
                'details': {
                    'Objects': f"{bucket.object_count} objects",
                    'Total Size': size_str,
                    'Created': bucket.created_at.strftime('%Y-%m-%d %H:%M') if bucket.created_at else 'N/A',
                    'Region': 'us-east-1',
                },
                'actions': ['delete']
            }
            
            card = ResourceCard(bucket.name, card_data, self)
            card.clicked.connect(self.show_bucket_details)
            card.action_triggered.connect(self.handle_card_action)
            
            self.card_container.add_card(card)
    
    def handle_card_action(self, action: str, bucket_name: str):
        """Handle card action"""
        if action == 'delete':
            self.delete_bucket(bucket_name)
    
    def create_bucket(self):
        """Show create bucket dialog"""
        dialog = CreateBucketDialog(self)
        if dialog.exec() == QDialog.Accepted:
            bucket_name = dialog.get_bucket_name()
            
            if not bucket_name:
                show_error_dialog(self, "Invalid Name", "Bucket name cannot be empty")
                return
            
            # Validate bucket name
            if not self._validate_bucket_name(bucket_name):
                show_error_dialog(
                    self, 
                    "Invalid Bucket Name",
                    "Bucket name must be 3-63 characters, lowercase, and alphanumeric with hyphens"
                )
                return
            
            try:
                bucket = self.storage_service.create_bucket(bucket_name)
                
                NotificationManager.show_success(
                    f"Bucket '{bucket.name}' created successfully!",
                    duration=5000
                )
                
                self._load_buckets()
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Creation Failed", str(e))
            except Exception as e:
                show_error_dialog(self, "Failed to create bucket", str(e))
    
    def _validate_bucket_name(self, name: str) -> bool:
        """Validate S3 bucket name"""
        if len(name) < 3 or len(name) > 63:
            return False
        if not name[0].isalnum() or not name[-1].isalnum():
            return False
        if not all(c.islower() or c.isdigit() or c == '-' for c in name):
            return False
        return True
    
    def delete_bucket(self, bucket_name: str):
        """Delete a bucket"""
        from ui.components.confirmation_dialog import confirm_action, DELETE_BUCKET_CONSEQUENCES
        
        if confirm_action(
            self,
            "Delete Bucket",
            f"Are you sure you want to delete bucket '{bucket_name}'?",
            DELETE_BUCKET_CONSEQUENCES
        ):
            try:
                self.storage_service.delete_bucket(bucket_name)
                
                NotificationManager.show_success(
                    f"Bucket '{bucket_name}' deleted successfully",
                    duration=4000
                )
                
                QTimer.singleShot(500, self._load_buckets)
                
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except Exception as e:
                show_error_dialog(self, "Failed to delete bucket", str(e))
    
    def show_bucket_details(self, bucket_name: str):
        """Show bucket details"""
        bucket = self.storage_service.get_bucket(bucket_name)
        if not bucket:
            return
        
        self.current_bucket = bucket_name
        
        # Calculate size
        total_size = sum(obj.get('size', 0) for obj in bucket.objects)
        size_mb = total_size / (1024 * 1024)
        
        detail_page = ResourceDetailPage(
            resource_type="bucket",
            resource_id=bucket_name,
            resource_data={
                'name': bucket.name,
                'objects': f"{bucket.object_count} objects",
                'size': f"{size_mb:.2f} MB",
                'created': bucket.created_at.strftime('%Y-%m-%d %H:%M') if bucket.created_at else 'N/A',
            },
            parent=self
        )
        
        detail_page.back_clicked.connect(self.show_list_view)
        
        self.stacked_widget.addWidget(detail_page)
        self.stacked_widget.setCurrentWidget(detail_page)
    
    def show_list_view(self):
        """Return to list view"""
        self.stacked_widget.setCurrentIndex(0)
        
        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        self._load_buckets()


# Export as default
StorageView = ModernStorageView
