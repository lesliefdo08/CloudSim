"""
Dialogs for Volume (EBS) operations
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QSpinBox, QComboBox,
                             QTextEdit, QCheckBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QMessageBox)
from PySide6.QtCore import Qt


class CreateVolumeDialog(QDialog):
    """Dialog for creating a new volume"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Volume")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Volume name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my-data-volume")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Volume size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size (GB):"))
        self.size_input = QSpinBox()
        self.size_input.setMinimum(1)
        self.size_input.setMaximum(16384)  # 16 TB max
        self.size_input.setValue(10)
        size_layout.addWidget(self.size_input)
        size_layout.addStretch()
        layout.addLayout(size_layout)
        
        # Volume type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Volume Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "gp3 (General Purpose SSD)",
            "gp2 (General Purpose SSD - Previous)",
            "io2 (Provisioned IOPS SSD)",
            "st1 (Throughput Optimized HDD)",
            "sc1 (Cold HDD)",
            "standard (Magnetic)"
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)
        
        # Type description
        self.type_description = QLabel()
        self.type_description.setWordWrap(True)
        self.type_description.setStyleSheet("color: #666; padding: 5px;")
        layout.addWidget(self.type_description)
        self._on_type_changed(0)
        
        # Availability Zone
        az_layout = QHBoxLayout()
        az_layout.addWidget(QLabel("Availability Zone:"))
        self.az_combo = QComboBox()
        self.az_combo.addItems(["us-east-1a", "us-east-1b", "us-east-1c"])
        az_layout.addWidget(self.az_combo)
        az_layout.addStretch()
        layout.addLayout(az_layout)
        
        # Encryption
        self.encrypted_check = QCheckBox("Enable encryption")
        layout.addWidget(self.encrypted_check)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Volume")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px;")
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _on_type_changed(self, index):
        """Update description when volume type changes"""
        descriptions = {
            0: "gp3: Latest generation general purpose SSD. Baseline 3,000 IOPS and 125 MB/s.",
            1: "gp2: Previous generation general purpose SSD. IOPS scale with volume size.",
            2: "io2: High-performance SSD for mission-critical workloads. Up to 64,000 IOPS.",
            3: "st1: Low-cost HDD for frequently accessed, throughput-intensive workloads.",
            4: "sc1: Lowest cost HDD for less frequently accessed workloads.",
            5: "standard: Previous generation magnetic volumes."
        }
        self.type_description.setText(descriptions.get(index, ""))
    
    def get_volume_data(self):
        """Get volume data from form"""
        volume_type = self.type_combo.currentText().split()[0]  # Extract type code
        return {
            "name": self.name_input.text().strip() or "unnamed-volume",
            "size_gb": self.size_input.value(),
            "volume_type": volume_type,
            "availability_zone": self.az_combo.currentText(),
            "encrypted": self.encrypted_check.isChecked()
        }


class AttachVolumeToInstanceDialog(QDialog):
    """Dialog for attaching a volume to an instance"""
    
    def __init__(self, available_volumes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attach Volume to Instance")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Instructions
        info_label = QLabel("Select a volume to attach to this instance:")
        layout.addWidget(info_label)
        
        # Volume table
        self.volume_table = QTableWidget()
        self.volume_table.setColumnCount(5)
        self.volume_table.setHorizontalHeaderLabels(["ID", "Name", "Size", "Type", "AZ"])
        self.volume_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.volume_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.volume_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Populate volumes
        self.volume_table.setRowCount(len(available_volumes))
        for i, volume in enumerate(available_volumes):
            self.volume_table.setItem(i, 0, QTableWidgetItem(volume.id))
            self.volume_table.setItem(i, 1, QTableWidgetItem(volume.name))
            self.volume_table.setItem(i, 2, QTableWidgetItem(f"{volume.size_gb} GB"))
            self.volume_table.setItem(i, 3, QTableWidgetItem(volume.volume_type))
            self.volume_table.setItem(i, 4, QTableWidgetItem(volume.availability_zone))
        
        layout.addWidget(self.volume_table)
        
        # Device path
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Device:"))
        self.device_input = QLineEdit()
        self.device_input.setPlaceholderText("/dev/sdb")
        self.device_input.setText("/dev/sdb")
        device_layout.addWidget(self.device_input)
        layout.addLayout(device_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        attach_btn = QPushButton("Attach")
        attach_btn.clicked.connect(self._validate_and_accept)
        attach_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        button_layout.addWidget(attach_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.available_volumes = available_volumes
    
    def _validate_and_accept(self):
        """Validate selection before accepting"""
        if not self.volume_table.selectedItems():
            QMessageBox.warning(self, "No Selection", "Please select a volume to attach.")
            return
        
        if not self.device_input.text().strip():
            QMessageBox.warning(self, "Invalid Device", "Please enter a device path (e.g., /dev/sdb).")
            return
        
        self.accept()
    
    def get_selected_volume_and_device(self):
        """Get selected volume and device path"""
        selected_row = self.volume_table.currentRow()
        if selected_row >= 0:
            volume = self.available_volumes[selected_row]
            device = self.device_input.text().strip()
            return volume, device
        return None, None


class CreateSnapshotDialog(QDialog):
    """Dialog for creating a snapshot"""
    
    def __init__(self, volume_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Create Snapshot - {volume_name}")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Snapshot name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Snapshot Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(f"{volume_name}-snapshot")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Description
        layout.addWidget(QLabel("Description (optional):"))
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Enter a description for this snapshot...")
        layout.addWidget(self.description_input)
        
        # Info
        info_label = QLabel(
            "💡 Snapshots are point-in-time copies of volumes. "
            "You can create new volumes from snapshots for backup or cloning purposes."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; padding: 10px; background: #f5f5f5; border-radius: 3px;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Snapshot")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 15px;")
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_snapshot_data(self):
        """Get snapshot data from form"""
        return {
            "name": self.name_input.text().strip() or "unnamed-snapshot",
            "description": self.description_input.toPlainText().strip() or None
        }


class CreateVolumeFromSnapshotDialog(QDialog):
    """Dialog for creating a volume from a snapshot"""
    
    def __init__(self, snapshots, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Volume from Snapshot")
        self.setModal(True)
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        
        # Instructions
        info_label = QLabel("Select a snapshot to restore:")
        layout.addWidget(info_label)
        
        # Snapshot table
        self.snapshot_table = QTableWidget()
        self.snapshot_table.setColumnCount(4)
        self.snapshot_table.setHorizontalHeaderLabels(["ID", "Name", "Size", "Created"])
        self.snapshot_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.snapshot_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.snapshot_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # Populate snapshots
        self.snapshot_table.setRowCount(len(snapshots))
        for i, snapshot in enumerate(snapshots):
            self.snapshot_table.setItem(i, 0, QTableWidgetItem(snapshot.id))
            self.snapshot_table.setItem(i, 1, QTableWidgetItem(snapshot.name))
            self.snapshot_table.setItem(i, 2, QTableWidgetItem(f"{snapshot.size_gb} GB"))
            self.snapshot_table.setItem(i, 3, QTableWidgetItem(snapshot.created_at))
        
        layout.addWidget(self.snapshot_table)
        
        # Volume name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("New Volume Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("restored-volume")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Volume")
        create_btn.clicked.connect(self._validate_and_accept)
        create_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px;")
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.snapshots = snapshots
    
    def _validate_and_accept(self):
        """Validate selection before accepting"""
        if not self.snapshot_table.selectedItems():
            QMessageBox.warning(self, "No Selection", "Please select a snapshot.")
            return
        
        self.accept()
    
    def get_snapshot_and_name(self):
        """Get selected snapshot and volume name"""
        selected_row = self.snapshot_table.currentRow()
        if selected_row >= 0:
            snapshot = self.snapshots[selected_row]
            volume_name = self.name_input.text().strip() or f"{snapshot.name}-restored"
            return snapshot, volume_name
        return None, None
