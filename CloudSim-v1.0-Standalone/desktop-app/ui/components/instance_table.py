"""
Instance Table - Premium Modern EC2 Table
Stunning instance management with beautiful design
"""

from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QCheckBox, QWidget, QHBoxLayout, QHeaderView
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor
from ui.design_system_premium import Colors, Fonts, Styles
from datetime import datetime


class InstanceTable(QTableWidget):
    """Premium modern instance table with beautiful styling"""
    
    instance_selected = Signal(str)  # instance_id when row clicked
    selection_changed = Signal(list, list)  # (selected_instances, running_instances_selected)
    
    def __init__(self):
        super().__init__()
        self.checkboxes = {}  # instance_id -> checkbox
        self.instance_data = {}  # instance_id -> instance object
        self._setup_table()
        self.itemClicked.connect(self._on_item_clicked)
    
    def _setup_table(self):
        """Setup premium table"""
        # Columns: Checkbox, Instance ID, State, Instance Type, Image, Launch Time
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "", "Instance ID", "State", "Instance type", "Image", "Launch time"
        ])
        
        # Premium styling
        self.setStyleSheet(Styles.table())
        
        # Table settings - Premium spacing
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(52)  # Generous row height
        self.setShowGrid(False)  # Clean modern look
        
        # Column widths
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 50)  # Checkbox
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable sorting
        self.setSortingEnabled(True)
    
    def add_instance(self, instance):
        """Add instance to table"""
        row = self.rowCount()
        self.insertRow(row)
        self.instance_data[instance.id] = instance
        
        # Checkbox
        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkboxes[instance.id] = checkbox
        checkbox_layout.addWidget(checkbox)
        
        self.setCellWidget(row, 0, checkbox_widget)
        
        # Instance ID (link style, clickable)
        id_item = QTableWidgetItem(instance.id)
        id_item.setForeground(QColor(Colors.TEXT_LINK))
        id_item.setData(Qt.ItemDataRole.UserRole, instance.id)  # Store ID
        self.setItem(row, 1, id_item)
        
        # State (with color)
        state_text = instance.status.lower()
        state_item = QTableWidgetItem(state_text)
        state_color = {
            "running": Colors.STATE_RUNNING,
            "stopped": Colors.STATE_STOPPED,
            "pending": Colors.STATE_PENDING,
            "terminated": Colors.STATE_TERMINATED,
        }.get(state_text, Colors.TEXT_PRIMARY)
        state_item.setForeground(QColor(state_color))
        self.setItem(row, 2, state_item)
        
        # Instance type
        type_item = QTableWidgetItem(instance.instance_type)
        self.setItem(row, 3, type_item)
        
        # Image
        image_item = QTableWidgetItem(instance.image)
        self.setItem(row, 4, image_item)
        
        # Launch time (format: YYYY-MM-DD HH:MM)
        try:
            if hasattr(instance, 'created_at') and instance.created_at:
                # Parse ISO format datetime
                dt = datetime.fromisoformat(instance.created_at.replace('Z', '+00:00'))
                launch_time = dt.strftime("%Y-%m-%d %H:%M")
            else:
                launch_time = "-"
        except:
            launch_time = "-"
        
        time_item = QTableWidgetItem(launch_time)
        self.setItem(row, 5, time_item)
    
    def clear_instances(self):
        """Clear all instances"""
        self.setRowCount(0)
        self.checkboxes.clear()
        self.instance_data.clear()
    
    def get_selected_instances(self):
        """Get list of selected instance IDs (via checkboxes)"""
        selected = []
        for instance_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected.append(instance_id)
        return selected
    
    def get_selected_running_instances(self):
        """Get list of selected running instance IDs"""
        selected_running = []
        for instance_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                instance = self.instance_data.get(instance_id)
                if instance and instance.status.lower() == "running":
                    selected_running.append(instance_id)
        return selected_running
    
    def get_selected_stopped_instances(self):
        """Get list of selected stopped instance IDs"""
        selected_stopped = []
        for instance_id, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                instance = self.instance_data.get(instance_id)
                if instance and instance.status.lower() == "stopped":
                    selected_stopped.append(instance_id)
        return selected_stopped
    
    def _on_checkbox_changed(self):
        """Handle checkbox state change"""
        selected = self.get_selected_instances()
        running = self.get_selected_running_instances()
        self.selection_changed.emit(selected, running)
    
    def _on_item_clicked(self, item):
        """Handle item click - navigate to instance details"""
        if item.column() == 1:  # Instance ID column
            instance_id = item.data(Qt.ItemDataRole.UserRole)
            if instance_id:
                self.instance_selected.emit(instance_id)
    
    def refresh_instance(self, instance):
        """Refresh a single instance in the table"""
        # Find row by instance ID
        for row in range(self.rowCount()):
            id_item = self.item(row, 1)
            if id_item and id_item.data(Qt.ItemDataRole.UserRole) == instance.id:
                # Update state
                state_text = instance.status.lower()
                state_item = self.item(row, 2)
                if state_item:
                    state_item.setText(state_text)
                    state_color = {
                        "running": Colors.STATE_RUNNING,
                        "stopped": Colors.STATE_STOPPED,
                        "pending": Colors.STATE_PENDING,
                        "terminated": Colors.STATE_TERMINATED,
                    }.get(state_text, Colors.TEXT_PRIMARY)
                    state_item.setForeground(QColor(state_color))
                
                # Update instance data
                self.instance_data[instance.id] = instance
                break
