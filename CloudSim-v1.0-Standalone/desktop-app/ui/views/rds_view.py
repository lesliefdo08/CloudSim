"""
RDS Service View
Database instances management interface
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QMessageBox, QListWidgetItem,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt
from api.client import APIClient


class RDSView(QWidget):
    """RDS database instances management view"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        self.refresh_instances()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("RDS Database Instances")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #232f3e;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.create_instance_btn = QPushButton("+ Create DB Instance")
        self.create_instance_btn.clicked.connect(self.create_instance)
        self.create_instance_btn.setStyleSheet(self.button_style("#ff9900"))
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_instances)
        self.refresh_btn.setStyleSheet(self.button_style("#232f3e"))
        
        header_layout.addWidget(self.create_instance_btn)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)
        
        # Instances list
        self.instances_list = QListWidget()
        self.instances_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 15px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #e7f3ff;
                color: #000;
            }
        """)
        layout.addWidget(self.instances_list)
        
        # Actions
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.delete_btn = QPushButton("Delete Instance")
        self.delete_btn.clicked.connect(self.delete_instance)
        self.delete_btn.setStyleSheet(self.button_style("#dc3545"))
        
        actions_layout.addWidget(self.delete_btn)
        layout.addLayout(actions_layout)
        
    def button_style(self, bg_color: str) -> str:
        """Get button style"""
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """
        
    def refresh_instances(self):
        """Refresh instances list"""
        instances = self.api_client.list_db_instances()
        if instances is None:
            return
            
        self.instances_list.clear()
        for instance in instances:
            db_id = instance.get("db_instance_id", "N/A")
            engine = instance.get("engine", "N/A")
            status = instance.get("status", "N/A")
            endpoint = instance.get("endpoint", {}).get("address", "N/A")
            
            item_text = f"🗄️ {db_id}\n   Engine: {engine}\n   Status: {status}\n   Endpoint: {endpoint}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, instance)
            self.instances_list.addItem(item)
            
    def create_instance(self):
        """Create new database instance"""
        dialog = CreateDBInstanceDialog(self.api_client, self)
        if dialog.exec():
            self.refresh_instances()
            
    def delete_instance(self):
        """Delete selected instance"""
        current = self.instances_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select an instance to delete")
            return
            
        instance = current.data(Qt.UserRole)
        db_id = instance.get("db_instance_id")
        
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete database instance '{db_id}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.delete_db_instance(db_id):
                QMessageBox.information(self, "Success", f"Instance '{db_id}' deleted")
                self.refresh_instances()


class CreateDBInstanceDialog(QDialog):
    """Dialog for creating RDS instance"""
    
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Create RDS Database Instance")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # DB Instance ID
        self.db_id_input = QLineEdit()
        self.db_id_input.setPlaceholderText("my-database")
        layout.addRow("DB Instance ID:", self.db_id_input)
        
        # Engine
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["postgres", "mysql", "mariadb"])
        layout.addRow("Engine:", self.engine_combo)
        
        # Instance class
        self.instance_class_combo = QComboBox()
        self.instance_class_combo.addItems(["db.t3.micro", "db.t3.small", "db.t3.medium"])
        layout.addRow("Instance Class:", self.instance_class_combo)
        
        # Storage
        self.storage_spin = QSpinBox()
        self.storage_spin.setRange(20, 1000)
        self.storage_spin.setValue(20)
        self.storage_spin.setSuffix(" GB")
        layout.addRow("Storage:", self.storage_spin)
        
        # Master username
        self.username_input = QLineEdit()
        self.username_input.setText("admin")
        layout.addRow("Master Username:", self.username_input)
        
        # Master password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter password")
        layout.addRow("Master Password:", self.password_input)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.create)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(create_btn)
        layout.addRow(buttons_layout)
        
    def create(self):
        """Create the database instance"""
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Please enter a master password")
            return
            
        data = {
            "db_instance_id": self.db_id_input.text() or "my-database",
            "engine": self.engine_combo.currentText(),
            "db_instance_class": self.instance_class_combo.currentText(),
            "allocated_storage": self.storage_spin.value(),
            "master_username": self.username_input.text(),
            "master_user_password": self.password_input.text()
        }
        
        result = self.api_client.create_db_instance(data)
        if result:
            QMessageBox.information(self, "Success", "Database instance created successfully!")
            self.accept()
