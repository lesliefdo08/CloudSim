"""
IAM View - User and policy management interface
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QListWidget, QTextEdit, QLineEdit, QGroupBox,
                               QDialog, QDialogButtonBox, QComboBox, QCheckBox,
                               QListWidgetItem, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from services.iam_service import iam_service
from models.iam_policy import Policy, PolicyStatement, SYSTEM_POLICIES
from models.iam_role import Role
from ui.components.notifications import NotificationManager
import json
from datetime import datetime


class PolicyEditorDialog(QDialog):
    """Dialog for creating/editing IAM policies"""
    
    def __init__(self, parent=None, policy_name: str = ""):
        super().__init__(parent)
        self.policy_name = policy_name
        self.setWindowTitle("Policy Editor" if not policy_name else f"Edit Policy: {policy_name}")
        self.setMinimumSize(700, 500)
        self.setup_ui()
        
        if policy_name:
            self.load_policy(policy_name)
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # Policy name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Policy Name:"))
        self.name_input = QLineEdit(self.policy_name)
        self.name_input.setReadOnly(bool(self.policy_name))
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description:"))
        self.desc_input = QLineEdit()
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)
        
        # JSON editor
        layout.addWidget(QLabel("Policy Document (JSON):"))
        self.json_editor = QTextEdit()
        self.json_editor.setPlaceholderText('{\n  "Version": "2012-10-17",\n  "Statement": [\n    {\n      "Effect": "Allow",\n      "Action": "*",\n      "Resource": "*"\n    }\n  ]\n}')
        self.json_editor.setFont(QFont("Consolas", 10))
        layout.addWidget(self.json_editor)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def load_policy(self, policy_name: str):
        """Load existing policy"""
        policy = iam_service.get_policy(policy_name)
        if policy:
            # Convert policy to JSON format
            policy_doc = policy.get_policy_document()
            self.json_editor.setPlainText(json.dumps(policy_doc, indent=2))
            self.desc_input.setText(policy.description or "")
    
    def get_policy_data(self):
        """Get policy data from dialog"""
        return {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip(),
            "json": self.json_editor.toPlainText().strip()
        }
    
    def apply_styles(self):
        """Apply dark theme styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit, QTextEdit {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)


class IAMView(QWidget):
    """IAM Management View"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_data()
    
    def setup_ui(self):
        """Setup the IAM view UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QLabel("IAM Management")
        header.setFont(QFont("Segoe UI", 24, QFont.Bold))
        header.setStyleSheet("color: #e2e8f0; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Main content in horizontal layout
        content_layout = QHBoxLayout()
        
        # Left side - Users
        user_group = QGroupBox("Users")
        user_layout = QVBoxLayout()
        
        # User list
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.on_user_selected)
        user_layout.addWidget(self.user_list)
        
        # User buttons
        user_btn_layout = QHBoxLayout()
        self.new_user_btn = QPushButton("➕ New User")
        self.new_user_btn.clicked.connect(self.create_user)
        user_btn_layout.addWidget(self.new_user_btn)
        user_layout.addLayout(user_btn_layout)
        
        user_group.setLayout(user_layout)
        content_layout.addWidget(user_group, 1)
        
        # Middle - Policies
        policy_group = QGroupBox("Policies")
        policy_layout = QVBoxLayout()
        
        # Policy list
        self.policy_list = QListWidget()
        self.policy_list.itemClicked.connect(self.on_policy_selected)
        policy_layout.addWidget(self.policy_list)
        
        # Policy buttons
        policy_btn_layout = QHBoxLayout()
        self.new_policy_btn = QPushButton("➕ New Policy")
        self.new_policy_btn.clicked.connect(self.create_policy)
        self.edit_policy_btn = QPushButton("✏️ Edit")
        self.edit_policy_btn.clicked.connect(self.edit_policy)
        self.export_policy_btn = QPushButton("📄 Export JSON")
        self.export_policy_btn.clicked.connect(self.export_policy)
        policy_btn_layout.addWidget(self.new_policy_btn)
        policy_btn_layout.addWidget(self.edit_policy_btn)
        policy_btn_layout.addWidget(self.export_policy_btn)
        policy_layout.addLayout(policy_btn_layout)
        
        policy_group.setLayout(policy_layout)
        content_layout.addWidget(policy_group, 1)
        
        # Right side - Details & Actions
        detail_group = QGroupBox("Details & Actions")
        detail_layout = QVBoxLayout()
        
        # User details
        self.user_details = QLabel("Select a user to view details")
        self.user_details.setWordWrap(True)
        self.user_details.setAlignment(Qt.AlignTop)
        detail_layout.addWidget(self.user_details)
        
        # Current user indicator (auth disabled - using local-user)
        current_label = QLabel("<b>Current User:</b> local-user")
        current_label.setStyleSheet("color: #10b981; padding: 10px; background-color: #0f172a; border-radius: 4px;")
        detail_layout.addWidget(current_label)
        
        # Attach/Detach policy buttons
        self.attach_policy_combo = QComboBox()
        self.attach_policy_btn = QPushButton("🔗 Attach Policy to User")
        self.attach_policy_btn.clicked.connect(self.attach_policy)
        detail_layout.addWidget(QLabel("Select policy to attach:"))
        detail_layout.addWidget(self.attach_policy_combo)
        detail_layout.addWidget(self.attach_policy_btn)
        
        detail_layout.addStretch()
        
        detail_group.setLayout(detail_layout)
        content_layout.addWidget(detail_group, 1)
        
        layout.addLayout(content_layout)
        
        self.setLayout(layout)
        self.apply_styles()
    
    def apply_styles(self):
        """Apply dark theme styles"""
        self.setStyleSheet("""
            QWidget {
                background-color: #0f172a;
                color: #e2e8f0;
            }
            QGroupBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
                font-size: 14px;
                font-weight: bold;
                color: #e2e8f0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QListWidget {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px;
                color: #e2e8f0;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
            }
            QListWidget::item:selected {
                background-color: #6366f1;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #4f46e5;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #818cf8);
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QComboBox {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 8px;
                color: #e2e8f0;
            }
        """)
    
    def refresh_data(self):
        """Refresh all data from IAM"""
        # Refresh users (auth disabled - show mock local user)
        self.user_list.clear()
        from models.user import User
        from datetime import datetime
        mock_user = User(
            user_id="local-user-id",
            username="local-user",
            email="local@cloudsim.local",
            password_hash="",
            created_at=datetime.now(),
            is_active=True
        )
        users = [mock_user]  # Mock user list
        for user in users:
            item = QListWidgetItem(f"👤 {user.username}")
            item.setData(Qt.UserRole, user.user_id)
            self.user_list.addItem(item)
        
        # Refresh policies
        self.policy_list.clear()
        self.attach_policy_combo.clear()
        for policy in iam_service.list_policies():
            # Add to list
            system_tag = " (System)" if policy.is_system else ""
            item = QListWidgetItem(f"📜 {policy.name}{system_tag}")
            item.setData(Qt.UserRole, policy.policy_id)
            self.policy_list.addItem(item)
            
            # Add to combo
            self.attach_policy_combo.addItem(policy.name, policy.policy_id)
    
    def on_user_selected(self, item: QListWidgetItem):
        """Handle user selection"""
        user_id = item.data(Qt.UserRole)
        # Get user policies
        user_policies = iam_service.get_user_policies(user_id)
        policies_str = ", ".join([p.name for p in user_policies]) if user_policies else "No policies attached"
        
        # In local mode, show static user details
        details = f"""
        <h3>User: local-user</h3>
        <p><b>User ID:</b> {user_id}</p>
        <p><b>Email:</b> local@cloudsim.local</p>
        <p><b>Created:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><b>Policies:</b> {policies_str}</p>
        """
        self.user_details.setText(details)
    
    def on_policy_selected(self, item: QListWidgetItem):
        """Handle policy selection"""
        policy_id = item.data(Qt.UserRole)
        policy = iam_service.get_policy(policy_id)
        if policy:
            allowed_actions = policy.get_allowed_actions()
            denied_actions = policy.get_denied_actions()
            
            details = f"""
            <h3>Policy: {policy.name}</h3>
            <p><b>Description:</b> {policy.description or 'No description'}</p>
            <p><b>Policy ID:</b> {policy.policy_id}</p>
            <p><b>Statements:</b> {len(policy.statements)}</p>
            <p><b>System Policy:</b> {'Yes' if policy.is_system else 'No'}</p>
            <p><b>Created:</b> {policy.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><b>Allowed Actions:</b> {len(allowed_actions)}</p>
            <p><b>Denied Actions:</b> {len(denied_actions)}</p>
            """
            self.user_details.setText(details)
    
    def create_user(self):
        """Create a new IAM user (disabled in local mode)"""
        NotificationManager.show_info(
            "User management disabled in local mode",
            duration=3000
        )
    
    def create_policy(self):
        """Create a new policy"""
        dialog = PolicyEditorDialog(self)
        if dialog.exec():
            data = dialog.get_policy_data()
            if not data["name"]:
                NotificationManager.show_error("Policy name is required")
                return
            
            try:
                # Parse JSON to extract statements
                policy_doc = json.loads(data["json"])
                statements = []
                
                for stmt in policy_doc.get("Statement", []):
                    statement = PolicyStatement(
                        effect=stmt.get("Effect", "Allow"),
                        actions=stmt.get("Action", []) if isinstance(stmt.get("Action"), list) else [stmt.get("Action", "*")],
                        resources=stmt.get("Resource", []) if isinstance(stmt.get("Resource"), list) else [stmt.get("Resource", "*")]
                    )
                    statements.append(statement)
                
                # Create policy
                policy = Policy.create_new(
                    name=data["name"],
                    description=data["description"],
                    statements=statements
                )
                
                success, message = iam_service.create_policy(policy)
                if success:
                    NotificationManager.show_success(f"Policy '{data['name']}' created successfully!")
                    self.refresh_data()
                else:
                    NotificationManager.show_error(message)
            except json.JSONDecodeError as e:
                NotificationManager.show_error(f"Invalid JSON: {e}")
            except Exception as e:
                NotificationManager.show_error(f"Error: {str(e)}")
    
    def edit_policy(self):
        """Edit selected policy"""
        current_item = self.policy_list.currentItem()
        if not current_item:
            NotificationManager.show_error("Please select a policy to edit")
            return
        
        policy_id = current_item.data(Qt.UserRole)
        policy = iam_service.get_policy(policy_id)
        
        if not policy:
            NotificationManager.show_error("Policy not found")
            return
        
        if policy.is_system:
            NotificationManager.show_error("Cannot edit system policies")
            return
        
        dialog = PolicyEditorDialog(self, policy.policy_id)
        if dialog.exec():
            data = dialog.get_policy_data()
            try:
                # Parse JSON to extract statements
                policy_doc = json.loads(data["json"])
                statements = []
                
                for stmt in policy_doc.get("Statement", []):
                    statement = PolicyStatement(
                        effect=stmt.get("Effect", "Allow"),
                        actions=stmt.get("Action", []) if isinstance(stmt.get("Action"), list) else [stmt.get("Action", "*")],
                        resources=stmt.get("Resource", []) if isinstance(stmt.get("Resource"), list) else [stmt.get("Resource", "*")]
                    )
                    statements.append(statement)
                
                # Update policy
                policy.statements = statements
                policy.description = data["description"]
                
                success, message = iam_service.update_policy(policy.policy_id, policy)
                if success:
                    NotificationManager.show_success(f"Policy '{policy.name}' updated successfully!")
                    self.refresh_data()
                else:
                    NotificationManager.show_error(message)
            except json.JSONDecodeError as e:
                NotificationManager.show_error(f"Invalid JSON: {e}")
            except Exception as e:
                NotificationManager.show_error(f"Error: {str(e)}")
    
    def export_policy(self):
        """Export selected policy as JSON"""
        current_item = self.policy_list.currentItem()
        if not current_item:
            NotificationManager.show_error("Please select a policy to export")
            return
        
        policy_id = current_item.data(Qt.UserRole)
        policy = iam_service.get_policy(policy_id)
        
        if not policy:
            NotificationManager.show_error("Policy not found")
            return
        
        # Get policy document
        policy_doc = policy.get_policy_document()
        json_str = json.dumps(policy_doc, indent=2)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Export Policy: {policy.name}")
        dialog.setMinimumSize(600, 400)
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setPlainText(json_str)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        layout.addWidget(text_edit)
        
        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(lambda: self.copy_to_clipboard(json_str))
        layout.addWidget(copy_btn)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard"""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(text)
        NotificationManager.show_success("Policy JSON copied to clipboard!")
    
    def attach_policy(self):
        """Attach selected policy to selected user"""
        current_user_item = self.user_list.currentItem()
        if not current_user_item:
            NotificationManager.show_error("Please select a user first")
            return
        
        user_id = current_user_item.data(Qt.UserRole)
        policy_id = self.attach_policy_combo.currentData()
        
        if not policy_id:
            NotificationManager.show_error("Please select a policy to attach")
            return
        
        policy = iam_service.get_policy(policy_id)
        if not policy:
            NotificationManager.show_error("Policy not found")
            return
        
        success, message = iam_service.attach_policy_to_user(user_id, policy_id)
        if success:
            NotificationManager.show_success(f"Policy '{policy.name}' attached to user!")
            self.refresh_data()
            # Refresh user details
            self.on_user_selected(current_user_item)
        else:
            NotificationManager.show_error(message)
