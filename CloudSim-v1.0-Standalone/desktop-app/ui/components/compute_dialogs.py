"""
Compute Dialogs - Premium Modern Dialogs
Beautiful dialogs with stunning design
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, 
    QComboBox, QPushButton, QHBoxLayout, QVBoxLayout,
    QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt
from ui.design_system_premium import Colors, Fonts, Spacing, Styles


class AttachVolumeDialog(QDialog):
    """Dialog for attaching a storage volume"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attach Volume")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Volume name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., data-volume")
        layout.addRow("Volume Name:", self.name_input)
        
        # Size
        self.size_input = QSpinBox()
        self.size_input.setMinimum(1)
        self.size_input.setMaximum(1000)
        self.size_input.setValue(10)
        self.size_input.setSuffix(" GB")
        layout.addRow("Size:", self.size_input)
        
        # Volume type
        self.type_input = QComboBox()
        self.type_input.addItems(["gp3", "gp2", "io2", "st1", "sc1"])
        layout.addRow("Volume Type:", self.type_input)
        
        # Device
        self.device_input = QLineEdit()
        self.device_input.setPlaceholderText("e.g., /dev/sdb")
        layout.addRow("Device:", self.device_input)
        
        # Info label
        info = QLabel(
            "Volume Types:\n"
            "• gp3/gp2: General Purpose SSD\n"
            "• io2: Provisioned IOPS SSD\n"
            "• st1: Throughput Optimized HDD\n"
            "• sc1: Cold HDD"
        )
        info.setStyleSheet("color: #666; font-size: 11px;")
        info.setWordWrap(True)
        layout.addRow("", info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        attach_btn = QPushButton("Attach")
        attach_btn.clicked.connect(self.accept)
        attach_btn.setStyleSheet("""
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
        button_layout.addWidget(attach_btn)
        
        layout.addRow(button_layout)
    
    def get_values(self):
        """Get input values"""
        return {
            "name": self.name_input.text().strip(),
            "size_gb": self.size_input.value(),
            "volume_type": self.type_input.currentText(),
            "device": self.device_input.text().strip()
        }


class EditTagsDialog(QDialog):
    """Dialog for editing instance tags"""
    
    def __init__(self, current_tags: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Tags")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.current_tags = current_tags
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        info = QLabel("Add or modify tags (key-value pairs)")
        info.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Tags table
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(2)
        self.tags_table.setHorizontalHeaderLabels(["Key", "Value"])
        self.tags_table.horizontalHeader().setStretchLastSection(True)
        self.tags_table.verticalHeader().setVisible(False)
        
        # Populate with current tags
        self.tags_table.setRowCount(len(self.current_tags) + 5)  # Extra rows for new tags
        row = 0
        for key, value in self.current_tags.items():
            self.tags_table.setItem(row, 0, QTableWidgetItem(key))
            self.tags_table.setItem(row, 1, QTableWidgetItem(value))
            row += 1
        
        layout.addWidget(self.tags_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
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
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def get_tags(self) -> dict:
        """Get tags from table"""
        tags = {}
        for row in range(self.tags_table.rowCount()):
            key_item = self.tags_table.item(row, 0)
            value_item = self.tags_table.item(row, 1)
            
            if key_item and value_item:
                key = key_item.text().strip()
                value = value_item.text().strip()
                if key and value:
                    tags[key] = value
        
        return tags


class CreateInstanceDialog(QDialog):
    """Premium modern create instance dialog"""
    
    def __init__(self, region="us-east-1", parent=None):
        super().__init__(parent)
        self.region = region
        self.setWindowTitle("Launch Instance")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self._init_ui()
        
    def _init_ui(self):
        """Initialize premium dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(int(Spacing.LG.replace("px", "")))
        layout.setContentsMargins(
            int(Spacing.XXL.replace("px", "")),
            int(Spacing.LG.replace("px", "")),
            int(Spacing.XXL.replace("px", "")),
            int(Spacing.XXL.replace("px", ""))
        )
        
        # Header with gradient accent
        header_container = QLabel()
        header_container.setStyleSheet(f"""
            background: {Colors.GRADIENT_PRIMARY};
            color: white;
            padding: 20px;
            border-radius: 12px;
            font-size: {Fonts.SUBTITLE};
            font-weight: {Fonts.BOLD};
        """)
        header_container.setText("🚀 Launch EC2 Instance")
        header_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_container)
        
        # Subtitle
        subtitle = QLabel("Configure your virtual machine")
        subtitle.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: 10px;
        """)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(int(Spacing.MD.replace("px", "")))
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Instance name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("web-server-1")
        self.name_input.setStyleSheet(Styles.input())
        form_layout.addRow("Instance Name:", self.name_input)
        
        # Instance type
        self.type_input = QComboBox()
        self.type_input.addItems([
            "t2.micro",
            "t2.small",
            "t2.medium",
            "t2.large",
            "m5.large",
            "m5.xlarge",
        ])
        self.type_input.setStyleSheet(Styles.input())
        form_layout.addRow("Instance Type:", self.type_input)
        
        # Image
        self.image_input = QComboBox()
        self.image_input.addItems([
            "ubuntu:22.04",
            "ubuntu:20.04",
            "amazonlinux:2",
            "debian:latest",
        ])
        self.image_input.setStyleSheet(Styles.input())
        form_layout.addRow("Image:", self.image_input)
        
        # CPU
        self.cpu_input = QSpinBox()
        self.cpu_input.setMinimum(1)
        self.cpu_input.setMaximum(64)
        self.cpu_input.setValue(1)
        self.cpu_input.setSuffix(" vCPU")
        self.cpu_input.setStyleSheet(Styles.input())
        form_layout.addRow("CPU:", self.cpu_input)
        
        # Memory
        self.memory_input = QSpinBox()
        self.memory_input.setMinimum(512)
        self.memory_input.setMaximum(524288)
        self.memory_input.setValue(1024)
        self.memory_input.setSingleStep(512)
        self.memory_input.setSuffix(" MB")
        self.memory_input.setStyleSheet(Styles.input())
        form_layout.addRow("Memory:", self.memory_input)
        
        layout.addLayout(form_layout)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(int(Spacing.MD.replace("px", "")))
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(Styles.secondary_button())
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        launch_btn = QPushButton("🚀 Launch Instance")
        launch_btn.setStyleSheet(Styles.success_button())
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.clicked.connect(self.accept)
        launch_btn.setDefault(True)
        button_layout.addWidget(launch_btn)
        
        layout.addLayout(button_layout)
        
        # Dialog styling
        self.setStyleSheet(Styles.dialog())
    
    def get_instance_config(self) -> dict:
        """Get instance configuration"""
        return {
            "name": self.name_input.text() or "unnamed-instance",
            "instance_type": self.type_input.currentText(),
            "image": self.image_input.currentText(),
            "cpu": self.cpu_input.value(),
            "memory": self.memory_input.value(),
        }
