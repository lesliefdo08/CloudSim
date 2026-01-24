"""
Serverless View - Lambda-like function management interface
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QTextEdit, QDialog,
    QFormLayout, QLineEdit, QMessageBox, QSplitter,
    QGroupBox, QListWidgetItem, QStackedWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from services.serverless_service import ServerlessService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from ui.design_system import Colors
from datetime import datetime
import json


class CreateFunctionDialog(QDialog):
    """Dialog for creating a new function"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Function")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Function name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., my-function")
        layout.addRow("Function Name:", self.name_input)
        
        # Handler name
        self.handler_input = QLineEdit()
        self.handler_input.setText("handler")
        self.handler_input.setPlaceholderText("handler")
        layout.addRow("Handler:", self.handler_input)
        
        # Info
        info = QLabel("Handler is the function name in your code that will be invoked")
        info.setStyleSheet("color: #666; font-size: 11px;")
        info.setWordWrap(True)
        layout.addRow("", info)
        
        # Code editor
        code_label = QLabel("Function Code (Python):")
        layout.addRow(code_label)
        
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Write your Python code here...")
        self.code_editor.setMinimumHeight(300)
        
        # Set monospace font
        font = QFont("Courier New", 10)
        self.code_editor.setFont(font)
        
        # Default template
        template = ServerlessService().get_default_code_template()
        self.code_editor.setPlainText(template)
        
        layout.addRow(self.code_editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.SERVERLESS};
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {Colors.SERVERLESS_HOVER};
            }}
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addRow(button_layout)
    
    def get_values(self):
        """Get input values"""
        return {
            "name": self.name_input.text().strip(),
            "handler": self.handler_input.text().strip() or "handler",
            "code": self.code_editor.toPlainText()
        }


class ServerlessView(QWidget):
    """View for managing serverless functions"""
    
    def __init__(self):
        super().__init__()
        self.serverless_service = ServerlessService()
        self.current_function = None
        self.init_ui()
        self.refresh_functions()
        
    def init_ui(self):
        """Initialize the serverless view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between list and detail views
        self.stacked_widget = QStackedWidget()
        
        # List view (functions with code editor)
        self.list_widget = QWidget()
        self.init_list_view()
        self.stacked_widget.addWidget(self.list_widget)
        
        layout.addWidget(self.stacked_widget)
        layout.addWidget(Footer())
        
    def init_list_view(self):
        """Initialize the list view with functions"""
        layout = QVBoxLayout(self.list_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Lambda Functions")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        
        header_layout.addStretch()
        
        # Action buttons with modern styling
        from ui.design_system import Styles
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_functions)
        refresh_btn.setStyleSheet(Styles.secondary_button())
        header_layout.addWidget(refresh_btn)
        
        create_btn = QPushButton("Create Function")
        create_btn.clicked.connect(self.create_function)
        create_btn.setStyleSheet(Styles.success_button())
        header_layout.addWidget(create_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Main content with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Function list
        function_widget = self._create_function_list_panel()
        splitter.addWidget(function_widget)
        
        # Right: Code editor and execution panel
        editor_widget = self._create_editor_panel()
        splitter.addWidget(editor_widget)
        
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
    
    def _create_function_list_panel(self):
        """Create function list panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Functions")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)
        
        self.function_list = QListWidget()
        self.function_list.itemClicked.connect(self.show_function_details)
        self.function_list.setStyleSheet("""
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
                cursor: pointer;
            }
            QListWidget::item:selected {
                background-color: #6366f1;
                color: white;
            }
            QListWidget::item:hover {
                background-color: rgba(99, 102, 241, 0.2);
            }
        """)
        layout.addWidget(self.function_list)
        
        return widget
    
    def _create_editor_panel(self):
        """Create code editor and execution panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Function details header
        header = QHBoxLayout()
        self.function_label = QLabel("Select a function")
        self.function_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self.function_label)
        
        header.addStretch()
        
        # Function action buttons
        self.update_btn = QPushButton("Update Code")
        self.update_btn.clicked.connect(self.update_function)
        self.update_btn.setEnabled(False)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        header.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_function)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        header.addWidget(self.delete_btn)
        
        layout.addLayout(header)
        
        # Code editor
        code_group = QGroupBox("Function Code")
        code_layout = QVBoxLayout(code_group)
        
        self.code_editor = QTextEdit()
        self.code_editor.setPlaceholderText("Select a function to view/edit code...")
        font = QFont("Courier New", 10)
        self.code_editor.setFont(font)
        code_layout.addWidget(self.code_editor)
        
        layout.addWidget(code_group)
        
        # Test section
        test_group = QGroupBox("Test Function")
        test_layout = QVBoxLayout(test_group)
        
        # Event input
        event_label = QLabel("Event Data (JSON):")
        test_layout.addWidget(event_label)
        
        self.event_input = QTextEdit()
        self.event_input.setPlaceholderText('{\n  "name": "CloudSim"\n}')
        self.event_input.setMaximumHeight(100)
        font = QFont("Courier New", 9)
        self.event_input.setFont(font)
        test_layout.addWidget(self.event_input)
        
        # Invoke button
        invoke_btn_layout = QHBoxLayout()
        invoke_btn_layout.addStretch()
        
        self.invoke_btn = QPushButton("Invoke Function")
        self.invoke_btn.clicked.connect(self.invoke_function)
        self.invoke_btn.setEnabled(False)
        self.invoke_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        invoke_btn_layout.addWidget(self.invoke_btn)
        
        test_layout.addLayout(invoke_btn_layout)
        
        # Output display
        output_label = QLabel("Output:")
        test_layout.addWidget(output_label)
        
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setPlaceholderText("Function output will appear here...")
        self.output_display.setMaximumHeight(150)
        font = QFont("Courier New", 9)
        self.output_display.setFont(font)
        test_layout.addWidget(self.output_display)
        
        layout.addWidget(test_group)
        
        return widget
    
    def refresh_functions(self):
        """Refresh function list"""
        functions = self.serverless_service.list_functions()
        
        # Update stats
        total = len(functions)
        total_invocations = sum(f.invocation_count for f in functions)
        self.stats_label.setText(f"Functions: {total} | Total Invocations: {total_invocations}")
        
        # Clear list
        self.function_list.clear()
        
        if not functions:
            item = QListWidgetItem("No Lambda functions")
            item.setForeground(Qt.gray)
            self.function_list.addItem(item)
            return
        
        # Populate list
        for func in functions:
            item_text = f"{func.name} ({func.invocation_count} invocations)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, func.name)
            self.function_list.addItem(item)
    
    def on_function_selected(self, item: QListWidgetItem):
        """Handle function selection"""
        func_name = item.data(Qt.UserRole)
        
        if not func_name:
            return
        
        func = self.serverless_service.get_function(func_name)
        if not func:
            return
        
        self.current_function = func
        self.function_label.setText(f"Function: {func.name}")
        
        # Load code
        self.code_editor.setPlainText(func.code)
        
        # Enable buttons
        self.update_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.invoke_btn.setEnabled(True)
        
        # Clear output
        self.output_display.clear()
    
    def create_function(self):
        """Create a new function"""
        dialog = CreateFunctionDialog(self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"]:
                QMessageBox.warning(self, "Error", "Function name cannot be empty")
                return
            
            if not values["code"]:
                QMessageBox.warning(self, "Error", "Function code cannot be empty")
                return
            
            try:
                self.serverless_service.create_function(
                    values["name"],
                    values["code"],
                    values["handler"]
                )
                self.refresh_functions()
                show_success_dialog(self, "Success", f"Function '{values['name']}' created!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def update_function(self):
        """Update current function code"""
        if not self.current_function:
            return
        
        new_code = self.code_editor.toPlainText()
        
        if not new_code.strip():
            QMessageBox.warning(self, "Error", "Function code cannot be empty")
            return
        
        try:
            self.serverless_service.update_function(self.current_function.name, new_code)
            self.refresh_functions()
            show_success_dialog(self, "Success", "Function code updated!")
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except ValueError as e:
            show_error_dialog(self, "Error", str(e))
    
    def delete_function(self):
        """Delete current function"""
        if not self.current_function:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete function '{self.current_function.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.serverless_service.delete_function(self.current_function.name)
                self.current_function = None
                self.code_editor.clear()
                self.output_display.clear()
                self.update_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.invoke_btn.setEnabled(False)
                self.function_label.setText("Select a function")
                self.refresh_functions()
                show_success_dialog(self, "Success", "Function deleted!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def invoke_function(self):
        """Invoke current function"""
        if not self.current_function:
            return
        
        # Parse event input
        event_text = self.event_input.toPlainText().strip()
        
        if not event_text:
            event = {}
        else:
            try:
                event = json.loads(event_text)
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "Error", f"Invalid JSON: {e}")
                return
        
        # Invoke function
        try:
            result = self.serverless_service.invoke_function(self.current_function.name, event)
            
            # Display result
            output_lines = []
            
            if result.success:
                output_lines.append("✓ Execution successful")
                output_lines.append(f"Duration: {result.duration_ms:.2f} ms")
                output_lines.append("")
                
                if result.logs:
                    output_lines.append("=== Logs ===")
                    output_lines.append(result.logs)
                    output_lines.append("")
                
                output_lines.append("=== Output ===")
                output_lines.append(result.output or "null")
                
            else:
                output_lines.append("✗ Execution failed")
                output_lines.append(f"Duration: {result.duration_ms:.2f} ms")
                output_lines.append("")
                
                if result.logs:
                    output_lines.append("=== Logs ===")
                    output_lines.append(result.logs)
                    output_lines.append("")
                
                output_lines.append("=== Error ===")
                output_lines.append(result.error or "Unknown error")
            
            self.output_display.setPlainText("\n".join(output_lines))
            
            # Refresh to update invocation count
            self.refresh_functions()
            
        except PermissionError as e:
            show_permission_denied(self, str(e))
        except ValueError as e:
            show_error_dialog(self, "Error", str(e))
    
    def show_function_details(self, item):
        """Show function detail page"""
        function_name = item.text()
        functions = self.serverless_service.list_functions()
        function = next((f for f in functions if f.name == function_name), None)
        
        if not function:
            return
        
        # Prepare resource data for detail page
        resource_data = {
            "overview": {
                "basic": {
                    "Function Name": function.name,
                    "Handler": function.handler,
                    "Region": function.region,
                    "Runtime": "Python 3.9"
                },
                "status": {
                    "Status": "Active",
                    "Invocations": str(function.invocation_count),
                    "Created": function.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(function, 'created_at') else "N/A"
                }
            },
            "configuration": {
                "Runtime": {
                    "Handler": function.handler,
                    "Runtime": "Python 3.9",
                    "Timeout": "30s"
                },
                "Performance": {
                    "Memory": "128 MB",
                    "Invocations": str(function.invocation_count)
                }
            },
            "monitoring": {
                "Invocations": str(function.invocation_count),
                "Average Duration": "N/A",
                "Error Count": "0",
                "Success Rate": "100%"
            },
            "permissions": {
                "owner": function.owner,
                "created_at": function.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(function, 'created_at') else "N/A",
                "arn": function.arn()
            },
            "tags": function.tags
        }
        
        # Create and show detail page
        detail_page = ResourceDetailPage(
            resource_type="Lambda Function",
            resource_name=function.name,
            resource_data=resource_data,
            parent=self
        )
        
        # Connect back button
        detail_page.back_clicked.connect(self.show_list_view)
        
        # Add to stacked widget and show
        self.stacked_widget.addWidget(detail_page)
        self.stacked_widget.setCurrentWidget(detail_page)
    
    def show_list_view(self):
        """Show the list view"""
        # Switch back to list view
        self.stacked_widget.setCurrentIndex(0)
        
        # Remove detail pages (keep only list view at index 0)
        while self.stacked_widget.count() > 1:
            widget = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(widget)
            widget.deleteLater()
        
        # Refresh the list
        self.refresh_functions()
