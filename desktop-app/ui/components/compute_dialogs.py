"""
Compute Dialogs - Dialogs for enhanced compute features
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QSpinBox, 
    QComboBox, QPushButton, QHBoxLayout, QVBoxLayout,
    QTextEdit, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView
)
from PySide6.QtCore import Qt


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
