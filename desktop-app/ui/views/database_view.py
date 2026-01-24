"""
Database View - RDS and DynamoDB-like database management interface
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QHeaderView, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QComboBox,
    QSplitter, QTextEdit, QScrollArea, QStackedWidget
)
from PySide6.QtCore import Qt
from services.database_service import DatabaseService
from ui.utils import show_permission_denied, show_error_dialog, show_success_dialog
from ui.components.resource_detail_page import ResourceDetailPage
from ui.components.footer import Footer
from ui.design_system import Colors
from datetime import datetime
import json


class CreateDatabaseDialog(QDialog):
    """Dialog for creating a new database"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create Database")
        self.setMinimumWidth(400)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Database name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., my-database")
        layout.addRow("Database Name:", self.name_input)
        
        # Database type
        self.type_input = QComboBox()
        self.type_input.addItems(["relational", "nosql"])
        layout.addRow("Type:", self.type_input)
        
        # Info label
        info = QLabel(
            "Relational: SQL-based (like MySQL/PostgreSQL)\n"
            "NoSQL: Key-value store (like DynamoDB)"
        )
        info.setStyleSheet("color: #666; font-size: 11px;")
        info.setWordWrap(True)
        layout.addRow("", info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
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
            "db_type": self.type_input.currentText()
        }


class CreateTableDialog(QDialog):
    """Dialog for creating a new table"""
    
    def __init__(self, db_type: str, parent=None):
        super().__init__(parent)
        self.db_type = db_type
        self.setWindowTitle("Create Table")
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Table name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., users")
        layout.addRow("Table Name:", self.name_input)
        
        if self.db_type == "relational":
            # Schema definition
            schema_label = QLabel("Schema (JSON format):")
            layout.addRow(schema_label)
            
            self.schema_input = QTextEdit()
            self.schema_input.setPlaceholderText(
                '{\n'
                '  "id": "INTEGER PRIMARY KEY",\n'
                '  "name": "TEXT",\n'
                '  "email": "TEXT"\n'
                '}'
            )
            self.schema_input.setMaximumHeight(150)
            layout.addRow(self.schema_input)
            
            info = QLabel("Define columns and their SQL types")
            info.setStyleSheet("color: #666; font-size: 11px;")
            layout.addRow("", info)
        else:
            info = QLabel("NoSQL tables store JSON documents with flexible schema")
            info.setStyleSheet("color: #666; font-size: 11px;")
            info.setWordWrap(True)
            layout.addRow("", info)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(self.accept)
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addRow(button_layout)
    
    def get_values(self):
        """Get input values"""
        values = {"name": self.name_input.text().strip()}
        
        if self.db_type == "relational":
            try:
                schema = json.loads(self.schema_input.toPlainText())
                values["schema"] = schema
            except json.JSONDecodeError:
                values["schema"] = None
        
        return values


class InsertRecordDialog(QDialog):
    """Dialog for inserting a record"""
    
    def __init__(self, db_type: str, schema=None, parent=None):
        super().__init__(parent)
        self.db_type = db_type
        self.schema = schema or {}
        self.setWindowTitle("Insert Record")
        self.setMinimumWidth(500)
        self.init_ui()
        
    def init_ui(self):
        """Initialize dialog UI"""
        layout = QFormLayout(self)
        
        # Record data
        data_label = QLabel("Record Data (JSON format):")
        layout.addRow(data_label)
        
        self.data_input = QTextEdit()
        
        if self.db_type == "relational" and self.schema:
            # Show schema as placeholder
            example = {col: f"<{dtype}>" for col, dtype in self.schema.items() 
                      if "PRIMARY KEY" not in dtype.upper() and "AUTOINCREMENT" not in dtype.upper()}
            self.data_input.setPlaceholderText(json.dumps(example, indent=2))
        else:
            self.data_input.setPlaceholderText(
                '{\n'
                '  "id": "user123",\n'
                '  "name": "John Doe",\n'
                '  "email": "john@example.com"\n'
                '}'
            )
        
        self.data_input.setMaximumHeight(200)
        layout.addRow(self.data_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        insert_btn = QPushButton("Insert")
        insert_btn.clicked.connect(self.accept)
        insert_btn.setStyleSheet("""
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
        button_layout.addWidget(insert_btn)
        
        layout.addRow(button_layout)
    
    def get_record(self):
        """Get record data"""
        try:
            return json.loads(self.data_input.toPlainText())
        except json.JSONDecodeError:
            return None


class DatabaseView(QWidget):
    """View for managing database tables"""
    
    def __init__(self):
        super().__init__()
        self.db_service = DatabaseService()
        self.current_database = None
        self.current_table = None
        self.init_ui()
        self.refresh_databases()
        
    def init_ui(self):
        """Initialize the database view UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget to switch between list and detail views
        self.stacked_widget = QStackedWidget()
        
        # List view (databases, tables, records)
        self.list_widget = QWidget()
        self.init_list_view()
        self.stacked_widget.addWidget(self.list_widget)
        
        layout.addWidget(self.stacked_widget)
        layout.addWidget(Footer())
        
    def init_list_view(self):
        """Initialize the list view with databases table"""
        layout = QVBoxLayout(self.list_widget)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("Databases")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(title)
        
        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        
        header_layout.addStretch()
        
        # Action buttons
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        header_layout.addWidget(refresh_btn)
        
        create_db_btn = QPushButton("Create Database")
        create_db_btn.clicked.connect(self.create_database)
        create_db_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        header_layout.addWidget(create_db_btn)
        
        layout.addLayout(header_layout)
        layout.addSpacing(20)
        
        # Create triple splitter: Databases | Tables | Records
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Databases
        db_widget = self._create_database_panel()
        splitter.addWidget(db_widget)
        
        # Middle: Tables
        table_widget = self._create_table_panel()
        splitter.addWidget(table_widget)
        
        # Right: Records
        record_widget = self._create_record_panel()
        splitter.addWidget(record_widget)
        
        splitter.setSizes([300, 300, 400])
        
        layout.addWidget(splitter)
    
    def _create_database_panel(self):
        """Create database list panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        label = QLabel("Databases")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)
        
        self.db_table = QTableWidget()
        self.db_table.setColumnCount(3)
        self.db_table.setHorizontalHeaderLabels(["Name", "Type", "Actions"])
        self.db_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.db_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.db_table.setSelectionMode(QTableWidget.SingleSelection)
        self.db_table.setShowGrid(False)
        self.db_table.verticalHeader().setVisible(False)
        self.db_table.itemSelectionChanged.connect(self.on_database_selected)
        self.db_table.cellClicked.connect(self.show_database_details)
        from ui.design_system import Styles
        self.db_table.setStyleSheet(Styles.table() + """
            QTableWidget::item {
                cursor: pointer;
            }
            QTableWidget::item:hover {
                background: rgba(99, 102, 241, 0.1);
            }
        """)
        layout.addWidget(self.db_table)
        
        return widget
    
    def _create_table_panel(self):
        """Create table list panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        self.table_label = QLabel("Select a database")
        self.table_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self.table_label)
        
        header.addStretch()
        
        self.create_table_btn = QPushButton("Create Table")
        self.create_table_btn.clicked.connect(self.create_table)
        self.create_table_btn.setEnabled(False)
        self.create_table_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 6px 12px;
                font-size: 11px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        header.addWidget(self.create_table_btn)
        
        layout.addLayout(header)
        
        from ui.design_system import Styles
        self.table_table = QTableWidget()
        self.table_table.setColumnCount(3)
        self.table_table.setHorizontalHeaderLabels(["Table Name", "Records", "Actions"])
        self.table_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_table.setSelectionMode(QTableWidget.NoSelection)
        self.table_table.setShowGrid(False)
        self.table_table.verticalHeader().setVisible(False)
        self.table_table.itemSelectionChanged.connect(self.on_table_selected)
        self.table_table.setStyleSheet(Styles.table())
        layout.addWidget(self.table_table)
        
        return widget
    
    def _create_record_panel(self):
        """Create record display panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        self.record_label = QLabel("Select a table")
        self.record_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self.record_label)
        
        header.addStretch()
        
        self.insert_btn = QPushButton("Insert Record")
        self.insert_btn.clicked.connect(self.insert_record)
        self.insert_btn.setEnabled(False)
        self.insert_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 6px 12px;
                font-size: 11px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        header.addWidget(self.insert_btn)
        
        layout.addLayout(header)
        
        from ui.design_system import Styles
        self.record_table = QTableWidget()
        self.record_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.record_table.setSelectionMode(QTableWidget.NoSelection)
        self.record_table.setShowGrid(False)
        self.record_table.verticalHeader().setVisible(False)
        self.record_table.setStyleSheet(Styles.table())
        layout.addWidget(self.record_table)
        
        return widget
    
    def refresh_all(self):
        """Refresh all panels"""
        self.refresh_databases()
        if self.current_database:
            self.refresh_tables()
            if self.current_table:
                self.refresh_records()
    
    def refresh_databases(self):
        """Refresh database list"""
        databases = self.db_service.list_databases()
        
        # Update stats
        relational = sum(1 for db in databases if db.db_type == "relational")
        nosql = sum(1 for db in databases if db.db_type == "nosql")
        self.stats_label.setText(f"Total: {len(databases)} | Relational: {relational} | NoSQL: {nosql}")
        
        # Clear table
        self.db_table.setRowCount(0)
        
        if not databases:
            self.db_table.setRowCount(1)
            placeholder = QLabel("No databases. Select 'Create Database' to begin.")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("color: #888; padding: 20px;")
            self.db_table.setCellWidget(0, 0, placeholder)
            self.db_table.setSpan(0, 0, 1, 3)
            return
        
        # Populate table
        for row, db in enumerate(databases):
            self.db_table.insertRow(row)
            
            self.db_table.setItem(row, 0, QTableWidgetItem(db.name))
            
            type_item = QTableWidgetItem(db.db_type.upper())
            if db.db_type == "relational":
                type_item.setForeground(Qt.blue)
            else:
                type_item.setForeground(Qt.darkMagenta)
            self.db_table.setItem(row, 1, type_item)
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, name=db.name: self.delete_database(name))
            delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 6px 12px; border: none; border-radius: 8px;")
            action_layout.addWidget(delete_btn)
            
            self.db_table.setCellWidget(row, 2, action_widget)
    
    def on_database_selected(self):
        """Handle database selection"""
        selected_rows = self.db_table.selectedIndexes()
        if not selected_rows:
            self.current_database = None
            self.table_label.setText("Select a database")
            self.create_table_btn.setEnabled(False)
            self.table_table.setRowCount(0)
            self.record_table.setRowCount(0)
            return
        
        row = selected_rows[0].row()
        db_name_item = self.db_table.item(row, 0)
        
        if db_name_item:
            self.current_database = db_name_item.text()
            self.table_label.setText(f"Tables in '{self.current_database}'")
            self.create_table_btn.setEnabled(True)
            self.refresh_tables()
    
    def refresh_tables(self):
        """Refresh table list"""
        if not self.current_database:
            return
        
        try:
            tables = self.db_service.list_tables(self.current_database)
            
            self.table_table.setRowCount(0)
            
            if not tables:
                self.table_table.setRowCount(1)
                placeholder = QLabel("No tables. Click 'Create Table'.")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("color: #888; padding: 20px;")
                self.table_table.setCellWidget(0, 0, placeholder)
                self.table_table.setSpan(0, 0, 1, 3)
                return
            
            for row, table in enumerate(tables):
                self.table_table.insertRow(row)
                
                self.table_table.setItem(row, 0, QTableWidgetItem(table.name))
                self.table_table.setItem(row, 1, QTableWidgetItem(str(table.record_count)))
                
                # Actions
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(4, 4, 4, 4)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, name=table.name: self.delete_table(name))
                delete_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 6px 12px; border: none; border-radius: 8px;")
                action_layout.addWidget(delete_btn)
                
                self.table_table.setCellWidget(row, 2, action_widget)
                
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def on_table_selected(self):
        """Handle table selection"""
        selected_rows = self.table_table.selectedIndexes()
        if not selected_rows:
            self.current_table = None
            self.record_label.setText("Select a table")
            self.insert_btn.setEnabled(False)
            self.record_table.setRowCount(0)
            return
        
        row = selected_rows[0].row()
        table_name_item = self.table_table.item(row, 0)
        
        if table_name_item:
            self.current_table = table_name_item.text()
            self.record_label.setText(f"Records in '{self.current_table}'")
            self.insert_btn.setEnabled(True)
            self.refresh_records()
    
    def refresh_records(self):
        """Refresh record list"""
        if not self.current_database or not self.current_table:
            return
        
        try:
            records = self.db_service.list_records(self.current_database, self.current_table)
            
            self.record_table.setRowCount(0)
            self.record_table.setColumnCount(0)
            
            if not records:
                self.record_table.setRowCount(1)
                self.record_table.setColumnCount(1)
                placeholder = QLabel("No records. Click 'Insert Record'.")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("color: #888; padding: 20px;")
                self.record_table.setCellWidget(0, 0, placeholder)
                return
            
            # Get all unique keys
            all_keys = set()
            for record in records:
                all_keys.update(record.keys())
            
            columns = sorted(list(all_keys))
            self.record_table.setColumnCount(len(columns))
            self.record_table.setHorizontalHeaderLabels(columns)
            
            # Populate records
            for row, record in enumerate(records):
                self.record_table.insertRow(row)
                for col, key in enumerate(columns):
                    value = record.get(key, "")
                    self.record_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.record_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))
    
    def create_database(self):
        """Create a new database"""
        dialog = CreateDatabaseDialog(self)
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"]:
                show_error_dialog(self, "Error", "Database name cannot be empty")
                return
            
            try:
                self.db_service.create_database(values["name"], values["db_type"])
                self.refresh_databases()
                show_success_dialog(self, "Success", f"Database '{values['name']}' created!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def delete_database(self, db_name: str):
        """Delete a database"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete database '{db_name}' and all its tables?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db_service.delete_database(db_name)
                if self.current_database == db_name:
                    self.current_database = None
                    self.current_table = None
                self.refresh_all()
                show_success_dialog(self, "Success", "Database deleted!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def create_table(self):
        """Create a new table"""
        if not self.current_database:
            return
        
        db = self.db_service.get_database(self.current_database)
        dialog = CreateTableDialog(db.db_type, self)
        
        if dialog.exec() == QDialog.Accepted:
            values = dialog.get_values()
            
            if not values["name"]:
                QMessageBox.warning(self, "Error", "Table name cannot be empty")
                return
            
            try:
                self.db_service.create_table(
                    self.current_database,
                    values["name"],
                    values.get("schema")
                )
                self.refresh_tables()
                show_success_dialog(self, "Success", f"Table '{values['name']}' created!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def delete_table(self, table_name: str):
        """Delete a table"""
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete table '{table_name}' and all its records?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db_service.delete_table(self.current_database, table_name)
                if self.current_table == table_name:
                    self.current_table = None
                self.refresh_tables()
                show_success_dialog(self, "Success", "Table deleted!")
            except PermissionError as e:
                show_permission_denied(self, str(e))
            except ValueError as e:
                show_error_dialog(self, "Error", str(e))
    
    def insert_record(self):
        """Insert a record into current table"""
        if not self.current_database or not self.current_table:
            return
        
        db = self.db_service.get_database(self.current_database)
        tables = self.db_service.list_tables(self.current_database)
        current_table_obj = next((t for t in tables if t.name == self.current_table), None)
        
        schema = current_table_obj.schema if current_table_obj else None
        dialog = InsertRecordDialog(db.db_type, schema, self)
        
        if dialog.exec() == QDialog.Accepted:
            record = dialog.get_record()
            
            if not record:
                QMessageBox.warning(self, "Error", "Invalid JSON format")
                return
            
            try:
                self.db_service.insert_record(self.current_database, self.current_table, record)
                self.refresh_records()
                self.refresh_tables()  # Update record count
                QMessageBox.information(self, "Success", "Record inserted!")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))
    
    def show_database_details(self, row, column):
        """Show database detail page"""
        # Skip if clicking the actions column
        if column == 2:
            return
            
        db_name = self.db_table.item(row, 0).text()
        databases = self.db_service.list_databases()
        database = next((d for d in databases if d.name == db_name), None)
        
        if not database:
            return
        
        # Get tables in database
        tables = self.db_service.list_tables(db_name)
        total_records = sum(t.record_count for t in tables)
        
        # Prepare resource data for detail page
        resource_data = {
            "overview": {
                "basic": {
                    "Database Name": database.name,
                    "Type": database.db_type.upper(),
                    "Region": database.region,
                    "Table Count": str(len(tables)),
                    "Total Records": str(total_records)
                },
                "status": {
                    "Status": "Available",
                    "Created": database.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(database, 'created_at') else "N/A"
                }
            },
            "configuration": {
                "Engine": {
                    "Database Type": database.db_type.upper(),
                    "Engine Version": "Latest"
                },
                "Capacity": {
                    "Tables": str(len(tables)),
                    "Records": str(total_records)
                }
            },
            "monitoring": {
                "Total Tables": str(len(tables)),
                "Total Records": str(total_records),
                "Average Records per Table": str(total_records // len(tables)) if len(tables) > 0 else "0"
            },
            "permissions": {
                "owner": database.owner,
                "created_at": database.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(database, 'created_at') else "N/A",
                "arn": database.arn()
            },
            "tags": database.tags
        }
        
        # Create and show detail page
        detail_page = ResourceDetailPage(
            resource_type=f"{database.db_type.upper()} Database",
            resource_name=database.name,
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
        self.refresh_all()

