"""
Compute View - Premium Modern EC2 Console
Beautiful instance management with stunning visuals
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from ui.design_system_premium import Colors, Fonts, Spacing, Styles
from ui.components.instance_table import InstanceTable
from ui.components.compute_dialogs import CreateInstanceDialog
from ui.components.instance_detail_view import InstanceDetailView
from services.compute_service import ComputeService


class ComputeViewTable(QWidget):
    """Premium EC2 Console instance list with beautiful table"""
    
    def __init__(self, compute_service=None):
        super().__init__()
        self.compute_service = compute_service or ComputeService()
        self.current_region = "us-east-1"
        self.current_view = "list"  # "list" or "detail"
        self.current_instance_id = None
        self._setup_ui()
        self._load_instances()
    
    def _setup_ui(self):
        """Setup AWS-style UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header with breadcrumb and region selector
        header = self._create_header()
        self.main_layout.addWidget(header)
        
        # Toolbar with action buttons
        toolbar = self._create_toolbar()
        self.main_layout.addWidget(toolbar)
        
        # Main content area (will switch between list and detail)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        # Table
        self.table = InstanceTable()
        self.table.selection_changed.connect(self._on_selection_changed)
        self.table.instance_selected.connect(self._show_instance_detail)
        self.content_layout.addWidget(self.table)
        
        self.main_layout.addWidget(self.content_widget)
    
    def _create_header(self):
        """Create AWS-style header with breadcrumb"""
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background: {Colors.BG_PRIMARY};
                border-bottom: 1px solid {Colors.BORDER};
            }}
        """)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Breadcrumb
        self.breadcrumb = QLabel("EC2 > Instances")
        self.breadcrumb.setStyleSheet(f"""
            font-size: {Fonts.TITLE};
            font-weight: {Fonts.SEMIBOLD};
            color: {Colors.TEXT_PRIMARY};
            background: transparent;
        """)
        layout.addWidget(self.breadcrumb)
        
        layout.addStretch()
        
        # Region selector
        region_label = QLabel("Region:")
        region_label.setStyleSheet(f"""
            font-size: {Fonts.BODY};
            color: {Colors.TEXT_PRIMARY};
            background: transparent;
        """)
        layout.addWidget(region_label)
        
        self.region_combo = QComboBox()
        self.region_combo.addItems(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"])
        self.region_combo.setCurrentText(self.current_region)
        self.region_combo.setStyleSheet(Styles.input())
        self.region_combo.currentTextChanged.connect(self._on_region_changed)
        layout.addWidget(self.region_combo)
        
        return header
    
    def _create_toolbar(self):
        """Create AWS-style toolbar with action buttons"""
        toolbar = QWidget()
        toolbar.setStyleSheet(f"""
            QWidget {{
                background: {Colors.BG_TERTIARY};
                border-bottom: 1px solid {Colors.BORDER};
                padding: 8px 16px;
            }}
        """)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)
        
        # Launch instance (always enabled)
        self.launch_btn = QPushButton("Launch instance")
        self.launch_btn.setStyleSheet(Styles.primary_button())
        self.launch_btn.clicked.connect(self._launch_instance)
        layout.addWidget(self.launch_btn)
        
        # Start (enabled when stopped instances selected)
        self.start_btn = QPushButton("Start")
        self.start_btn.setStyleSheet(Styles.secondary_button())
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._start_instances)
        layout.addWidget(self.start_btn)
        
        # Stop (enabled when running instances selected)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(Styles.secondary_button())
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_instances)
        layout.addWidget(self.stop_btn)
        
        # Reboot (enabled when running instances selected)
        self.reboot_btn = QPushButton("Reboot")
        self.reboot_btn.setStyleSheet(Styles.secondary_button())
        self.reboot_btn.setEnabled(False)
        self.reboot_btn.clicked.connect(self._reboot_instances)
        layout.addWidget(self.reboot_btn)
        
        # Terminate (enabled when any instances selected)
        self.terminate_btn = QPushButton("Terminate")
        self.terminate_btn.setStyleSheet(Styles.danger_button())
        self.terminate_btn.setEnabled(False)
        self.terminate_btn.clicked.connect(self._terminate_instances)
        layout.addWidget(self.terminate_btn)
        
        layout.addStretch()
        
        return toolbar
    
    def _load_instances(self):
        """Load instances from backend"""
        self.table.clear_instances()
        instances = self.compute_service.list_instances()
        
        # Filter by region
        filtered = [inst for inst in instances if inst.region == self.current_region]
        
        for instance in filtered:
            self.table.add_instance(instance)
    
    def _on_selection_changed(self, selected_ids, running_ids):
        """Handle table selection change - update toolbar button states"""
        has_selection = len(selected_ids) > 0
        has_running = len(running_ids) > 0
        has_stopped = len(self.table.get_selected_stopped_instances()) > 0
        
        self.start_btn.setEnabled(has_stopped)
        self.stop_btn.setEnabled(has_running)
        self.reboot_btn.setEnabled(has_running)
        self.terminate_btn.setEnabled(has_selection)
    
    def _on_region_changed(self, region):
        """Handle region change"""
        self.current_region = region
        self._load_instances()
    
    def _launch_instance(self):
        """Show launch instance dialog"""
        dialog = CreateInstanceDialog(region=self.current_region, parent=self)
        if dialog.exec():
            config = dialog.get_instance_config()
            config["region"] = self.current_region
            
            try:
                instance = self.compute_service.create_instance(**config)
                self._load_instances()
                QMessageBox.information(
                    self,
                    "Instance Launched",
                    f"Instance {instance.id} has been launched successfully."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Launch Failed",
                    f"Failed to launch instance: {str(e)}"
                )
    
    def _start_instances(self):
        """Start selected stopped instances"""
        selected = self.table.get_selected_stopped_instances()
        if not selected:
            return
        
        for instance_id in selected:
            try:
                self.compute_service.start_instance(instance_id)
            except Exception as e:
                QMessageBox.warning(self, "Start Failed", f"Failed to start {instance_id}: {str(e)}")
        
        self._load_instances()
    
    def _stop_instances(self):
        """Stop selected running instances"""
        selected = self.table.get_selected_running_instances()
        if not selected:
            return
        
        reply = QMessageBox.question(
            self,
            "Stop Instances",
            f"Are you sure you want to stop {len(selected)} instance(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for instance_id in selected:
                try:
                    self.compute_service.stop_instance(instance_id)
                except Exception as e:
                    QMessageBox.warning(self, "Stop Failed", f"Failed to stop {instance_id}: {str(e)}")
            
            self._load_instances()
    
    def _reboot_instances(self):
        """Reboot selected running instances"""
        selected = self.table.get_selected_running_instances()
        if not selected:
            return
        
        for instance_id in selected:
            try:
                self.compute_service.reboot_instance(instance_id)
            except Exception as e:
                QMessageBox.warning(self, "Reboot Failed", f"Failed to reboot {instance_id}: {str(e)}")
        
        self._load_instances()
    
    def _terminate_instances(self):
        """Terminate selected instances"""
        selected = self.table.get_selected_instances()
        if not selected:
            return
        
        reply = QMessageBox.warning(
            self,
            "Terminate Instances",
            f"Are you sure you want to permanently terminate {len(selected)} instance(s)?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for instance_id in selected:
                try:
                    self.compute_service.terminate_instance(instance_id)
                except Exception as e:
                    QMessageBox.critical(self, "Terminate Failed", f"Failed to terminate {instance_id}: {str(e)}")
            
            self._load_instances()
    
    def _show_instance_detail(self, instance_id):
        """Show instance detail view"""
        instance = self.compute_service.get_instance(instance_id)
        if not instance:
            return
        
        # Clear content area
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create detail view
        detail_view = InstanceDetailView(instance, self.compute_service, parent=self)
        detail_view.back_clicked.connect(self._show_instance_list)
        self.content_layout.addWidget(detail_view)
        
        # Update breadcrumb
        self.breadcrumb.setText(f"EC2 > Instances > {instance_id}")
        
        # Hide toolbar
        self.findChild(QWidget).setVisible(False)  # Hide toolbar
    
    def _show_instance_list(self):
        """Return to instance list view"""
        # Clear content area
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Recreate table
        self.table = InstanceTable()
        self.table.selection_changed.connect(self._on_selection_changed)
        self.table.instance_selected.connect(self._show_instance_detail)
        self.content_layout.addWidget(self.table)
        
        # Reload instances
        self._load_instances()
        
        # Update breadcrumb
        self.breadcrumb.setText("EC2 > Instances")
