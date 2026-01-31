"""
IAM View - Identity and Access Management with professional AWS-style interface
Implements: Empty states, WCAG-compliant colors, design system consistency
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QInputDialog, QMessageBox,
    QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from api.client import APIClient
from ui.design_system import Colors, Fonts, Spacing, Styles, create_empty_state


class IAMViewSimple(QWidget):
    """IAM users management view with professional styling"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        self.refresh_users()
        
    def setup_ui(self):
        """Setup the user interface with professional styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 24, 30, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        title = QLabel("IAM Users")
        title.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.BOLD};
            color: {Colors.TEXT_PRIMARY};
        """)
        title_layout.addWidget(title)
        
        subtitle = QLabel("Manage Identity and Access Management users")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
        """)
        title_layout.addWidget(subtitle)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Action buttons
        self.create_user_btn = QPushButton("+ Create User")
        self.create_user_btn.clicked.connect(self.create_user)
        self.create_user_btn.setStyleSheet(Styles.primary_button())
        self.create_user_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.refresh_users)
        self.refresh_btn.setStyleSheet(Styles.secondary_button())
        self.refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        header_layout.addWidget(self.create_user_btn)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)
        
        # Stacked widget for list/empty state
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Users list
        self.users_list = QListWidget()
        self.users_list.setStyleSheet(f"""
            QListWidget {{
                background: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 2px;
                padding: 4px;
                font-size: {Fonts.BODY};
            }}
            QListWidget::item {{
                padding: 16px 12px;
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
        self.stack.addWidget(self.users_list)
        
        # Empty state
        empty_widget = create_empty_state(
            "No IAM Users Yet",
            "Create your first user to manage access and permissions. IAM users control who can access your cloud resources.",
            parent=self
        )
        self.stack.addWidget(empty_widget)
        
        # Actions footer
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.delete_user_btn = QPushButton("Delete User")
        self.delete_user_btn.clicked.connect(self.delete_user)
        self.delete_user_btn.setStyleSheet(Styles.danger_button())
        self.delete_user_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        footer_layout.addWidget(self.delete_user_btn)
        layout.addLayout(footer_layout)
        
    def refresh_users(self):
        """Refresh users list and show empty state if needed"""
        users = self.api_client.list_users()
        if users is None:
            return
        
        # Show empty state or list
        if len(users) == 0:
            self.stack.setCurrentIndex(1)  # Show empty state
        else:
            self.stack.setCurrentIndex(0)  # Show list
        
        self.users_list.clear()
        
        for user in users:
            user_name = user.get("user_name", "N/A")
            user_id = user.get("user_id", "N/A")
            created = user.get("created_at", "N/A")
            
            item_text = f"👤 {user_name}\nID: {user_id} | Created: {created}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, user)
            self.users_list.addItem(item)
            
    def create_user(self):
        """Create new user"""
        username, ok = QInputDialog.getText(
            self, "Create IAM User",
            "Enter username:",
            QLineEdit.Normal,
            "user-" + str(hash(str(id(self))))[-6:]
        )
        
        if ok and username:
            data = {"user_name": username}
            if self.api_client.create_user(data):
                QMessageBox.information(self, "Success", f"User '{username}' created successfully!")
                self.refresh_users()
                
    def delete_user(self):
        """Delete selected user"""
        current = self.users_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a user to delete")
            return
            
        user = current.data(Qt.UserRole)
        username = user.get("user_name")
        
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete user '{username}'?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.delete_user(username):
                QMessageBox.information(self, "Success", f"User '{username}' deleted successfully!")
                self.refresh_users()
