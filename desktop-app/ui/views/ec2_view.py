"""
EC2 Service View - Instance management with professional AWS-style interface
Implements: Empty states, WCAG-compliant colors, row hover effects
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QStackedWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCursor
from api.client import APIClient
from ui.design_system import Colors, Fonts, Spacing, Styles, create_empty_state


class EC2View(QWidget):
    """EC2 instances management view"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        self.refresh_instances()
        
        # Auto-refresh every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_instances)
        self.refresh_timer.start(30000)
        
    def setup_ui(self):
        """Setup the user interface with modern styling"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(20)
        
        # Header with modern design
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        title = QLabel("🖥️ EC2 Instances")
        title.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Action buttons with modern styling
        self.launch_btn = QPushButton("🚀 Launch Instance")
        self.launch_btn.clicked.connect(self.launch_instance)
        self.launch_btn.setStyleSheet(Styles.primary_button())
        self.launch_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.refresh_instances)
        self.refresh_btn.setStyleSheet(Styles.secondary_button())
        self.refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        header_layout.addWidget(self.launch_btn)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)
        
        # Stacked widget for table/empty state
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Instances table with improved styling
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Instance ID", "Name", "Type", "State", "IP Address", "Actions"
        ])
        
        # Configure table behavior
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Instance ID
        header.setSectionResizeMode(1, QHeaderView.Stretch)           # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # State
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # IP
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Actions
        
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        
        # Apply professional AWS-style table styling with row hover
        self.table.setStyleSheet(Styles.table())
        self.stack.addWidget(self.table)
        
        # Empty state widget
        empty_widget = create_empty_state(
            "No EC2 Instances Yet",
            "Launch your first instance to get started. EC2 instances are virtual servers in the cloud.",
            parent=self
        )
        self.stack.addWidget(empty_widget)
        
    def refresh_instances(self):
        """Refresh instances list and show empty state if needed"""
        instances = self.api_client.list_instances()
        
        # Handle API error
        if instances is None:
            self.stack.setCurrentIndex(1)  # Show empty state on error
            return
        
        # Show empty state or table
        if len(instances) == 0:
            self.stack.setCurrentIndex(1)  # Show empty state
            return
        
        # Show table with data
        self.stack.setCurrentIndex(0)
        self.table.setRowCount(0)
        
        for instance in instances:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Instance data
            self.table.setItem(row, 0, QTableWidgetItem(instance.get("instance_id", "N/A")))
            self.table.setItem(row, 1, QTableWidgetItem(instance.get("name", "unnamed")))
            self.table.setItem(row, 2, QTableWidgetItem(instance.get("instance_type", "N/A")))
            
            # State with color
            state = instance.get("state", "unknown")
            state_item = QTableWidgetItem(state.upper())
            if state == "running":
                state_item.setForeground(Qt.darkGreen)
            elif state == "stopped":
                state_item.setForeground(Qt.red)
            else:
                state_item.setForeground(Qt.darkYellow)
            self.table.setItem(row, 3, state_item)
            
            self.table.setItem(row, 4, QTableWidgetItem(instance.get("private_ip", "N/A")))
            
            # Action buttons with improved styling
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            instance_id = instance.get("instance_id")
            
            if state == "stopped":
                start_btn = QPushButton("▶ Start")
                start_btn.clicked.connect(lambda checked, iid=instance_id: self.start_instance(iid))
                start_btn.setStyleSheet(Styles.success_button())
                start_btn.setCursor(QCursor(Qt.PointingHandCursor))
                actions_layout.addWidget(start_btn)
            elif state == "running":
                stop_btn = QPushButton("⏸ Stop")
                stop_btn.clicked.connect(lambda checked, iid=instance_id: self.stop_instance(iid))
                stop_btn.setStyleSheet(Styles.secondary_button())
                stop_btn.setCursor(QCursor(Qt.PointingHandCursor))
                actions_layout.addWidget(stop_btn)
            
            terminate_btn = QPushButton("× Terminate")
            terminate_btn.clicked.connect(lambda checked, iid=instance_id: self.terminate_instance(iid))
            terminate_btn.setStyleSheet(Styles.danger_button())
            terminate_btn.setCursor(QCursor(Qt.PointingHandCursor))
            actions_layout.addWidget(terminate_btn)
            
            self.table.setCellWidget(row, 5, actions_widget)
            
    def start_instance(self, instance_id: str):
        """Start an instance"""
        if self.api_client.start_instance(instance_id):
            QMessageBox.information(self, "Success", f"Instance {instance_id} started")
            self.refresh_instances()
            
    def stop_instance(self, instance_id: str):
        """Stop an instance"""
        reply = QMessageBox.question(
            self, "Confirm Stop",
            f"Are you sure you want to stop instance {instance_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.stop_instance(instance_id):
                QMessageBox.information(self, "Success", f"Instance {instance_id} stopped")
                self.refresh_instances()
                
    def terminate_instance(self, instance_id: str):
        """Terminate an instance"""
        reply = QMessageBox.warning(
            self, "Confirm Termination",
            f"Are you sure you want to TERMINATE instance {instance_id}?\n\nThis action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.terminate_instance(instance_id):
                QMessageBox.information(self, "Success", f"Instance {instance_id} terminated")
                self.refresh_instances()
                
    def launch_instance(self):
        """Show launch instance dialog"""
        dialog = LaunchInstanceDialog(self.api_client, self)
        if dialog.exec():
            self.refresh_instances()


class LaunchInstanceDialog(QDialog):
    """Dialog for launching new EC2 instance"""
    
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI with professional styling"""
        self.setWindowTitle("Launch EC2 Instance")
        self.setMinimumWidth(450)
        self.setStyleSheet(Styles.dialog())
        
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Instance name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my-web-server")
        self.name_input.setStyleSheet(Styles.input())
        layout.addRow("Instance Name:", self.name_input)
        
        # Instance type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["t2.micro", "t2.small", "t2.medium", "t2.large", "t3.micro", "t3.small"])
        self.type_combo.setStyleSheet(Styles.input())
        layout.addRow("Instance Type:", self.type_combo)
        
        # Image ID
        self.ami_input = QLineEdit()
        self.ami_input.setPlaceholderText("ami-xxxxx (optional)")
        self.ami_input.setStyleSheet(Styles.input())
        layout.addRow("AMI ID:", self.ami_input)
        
        # Help text
        help_label = QLabel("Tip: Leave AMI blank to use the default Amazon Linux image")
        help_label.setStyleSheet(f"color: {Colors.TEXT_TERTIARY}; font-size: {Fonts.SMALL};")
        help_label.setWordWrap(True)
        layout.addRow("", help_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(Styles.secondary_button())
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        
        launch_btn = QPushButton("Launch Instance")
        launch_btn.clicked.connect(self.launch)
        launch_btn.setStyleSheet(Styles.primary_button())
        launch_btn.setCursor(QCursor(Qt.PointingHandCursor))
        launch_btn.setDefault(True)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(launch_btn)
        layout.addRow("", buttons_layout)
        
    def launch(self):
        """Launch the instance"""
        data = {
            "name": self.name_input.text() or "unnamed-instance",
            "instance_type": self.type_combo.currentText(),
            "count": 1
        }
        
        if self.ami_input.text():
            data["image_id"] = self.ami_input.text()
        
        result = self.api_client.create_instance(data)
        if result:
            QMessageBox.information(self, "Success", "Instance launched successfully!")
            self.accept()
