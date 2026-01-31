"""
Lambda Service View
Functions management interface
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
    QPushButton, QLabel, QMessageBox, QListWidgetItem,
    QDialog, QFormLayout, QLineEdit, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt
from api.client import APIClient


class LambdaView(QWidget):
    """Lambda functions management view"""
    
    def __init__(self, api_client: APIClient):
        super().__init__()
        self.api_client = api_client
        self.setup_ui()
        self.refresh_functions()
        
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Lambda Functions")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #232f3e;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        self.create_function_btn = QPushButton("+ Create Function")
        self.create_function_btn.clicked.connect(self.create_function)
        self.create_function_btn.setStyleSheet(self.button_style("#ff9900"))
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.refresh_functions)
        self.refresh_btn.setStyleSheet(self.button_style("#232f3e"))
        
        header_layout.addWidget(self.create_function_btn)
        header_layout.addWidget(self.refresh_btn)
        layout.addLayout(header_layout)
        
        # Functions list
        self.functions_list = QListWidget()
        self.functions_list.setStyleSheet("""
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
        layout.addWidget(self.functions_list)
        
        # Actions
        actions_layout = QHBoxLayout()
        
        self.invoke_btn = QPushButton("▶ Invoke")
        self.invoke_btn.clicked.connect(self.invoke_function)
        self.invoke_btn.setStyleSheet(self.button_style("#28a745"))
        
        self.delete_btn = QPushButton("Delete Function")
        self.delete_btn.clicked.connect(self.delete_function)
        self.delete_btn.setStyleSheet(self.button_style("#dc3545"))
        
        actions_layout.addStretch()
        actions_layout.addWidget(self.invoke_btn)
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
        
    def refresh_functions(self):
        """Refresh functions list"""
        functions = self.api_client.list_functions()
        if functions is None:
            return
            
        self.functions_list.clear()
        for func in functions:
            name = func.get("function_name", "N/A")
            runtime = func.get("runtime", "N/A")
            handler = func.get("handler", "N/A")
            
            item_text = f"λ {name}\n   Runtime: {runtime}\n   Handler: {handler}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, func)
            self.functions_list.addItem(item)
            
    def create_function(self):
        """Create new Lambda function"""
        dialog = CreateFunctionDialog(self.api_client, self)
        if dialog.exec():
            self.refresh_functions()
            
    def invoke_function(self):
        """Invoke selected function"""
        current = self.functions_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a function to invoke")
            return
            
        func = current.data(Qt.UserRole)
        function_name = func.get("function_name")
        
        # Simple invoke with empty payload
        result = self.api_client.invoke_function(function_name, {})
        if result:
            output = result.get("output", "No output")
            QMessageBox.information(
                self, "Function Invoked",
                f"Function: {function_name}\n\nOutput:\n{output}"
            )
            
    def delete_function(self):
        """Delete selected function"""
        current = self.functions_list.currentItem()
        if not current:
            QMessageBox.warning(self, "No Selection", "Please select a function to delete")
            return
            
        func = current.data(Qt.UserRole)
        function_name = func.get("function_name")
        
        reply = QMessageBox.warning(
            self, "Confirm Deletion",
            f"Are you sure you want to delete function '{function_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.api_client.delete_function(function_name):
                QMessageBox.information(self, "Success", f"Function '{function_name}' deleted")
                self.refresh_functions()


class CreateFunctionDialog(QDialog):
    """Dialog for creating Lambda function"""
    
    def __init__(self, api_client: APIClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.setup_ui()
        
    def setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Create Lambda Function")
        self.setMinimumWidth(500)
        
        layout = QFormLayout(self)
        
        # Function name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my-function")
        layout.addRow("Function Name:", self.name_input)
        
        # Runtime
        self.runtime_combo = QComboBox()
        self.runtime_combo.addItems([
            "python3.9", "python3.10", "python3.11", "python3.12",
            "nodejs18.x", "nodejs20.x"
        ])
        layout.addRow("Runtime:", self.runtime_combo)
        
        # Handler
        self.handler_input = QLineEdit()
        self.handler_input.setText("lambda_function.lambda_handler")
        layout.addRow("Handler:", self.handler_input)
        
        # Code
        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("def lambda_handler(event, context):\n    return {'statusCode': 200, 'body': 'Hello!'}")
        self.code_input.setMinimumHeight(200)
        layout.addRow("Code:", self.code_input)
        
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
        """Create the function"""
        data = {
            "function_name": self.name_input.text(),
            "runtime": self.runtime_combo.currentText(),
            "handler": self.handler_input.text(),
            "code": self.code_input.toPlainText() or "def lambda_handler(event, context): return {'statusCode': 200}"
        }
        
        result = self.api_client.create_function(data)
        if result:
            QMessageBox.information(self, "Success", "Function created successfully!")
            self.accept()
