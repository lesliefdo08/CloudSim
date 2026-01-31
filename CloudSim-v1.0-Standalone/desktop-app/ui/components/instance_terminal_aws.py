"""
Instance Terminal - AWS Session Manager Style (Boring and Professional)
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, 
                                QLineEdit, QLabel, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextCursor
from ui.design_system import Colors, Fonts


class InstanceTerminal(QWidget):
    """AWS Session Manager style terminal widget"""
    
    command_executed = Signal(str, str)  # command, output
    
    def __init__(self, instance_id: str, instance_name: str, compute_service, instance_status: str = "running", parent=None):
        super().__init__(parent)
        self.instance_id = instance_id
        self.instance_name = instance_name
        self.compute_service = compute_service
        self.instance_status = instance_status
        self.command_history = []
        self.history_index = -1
        self.is_executing = False
        
        self._setup_ui()
        
        # Check if instance is running
        if instance_status.lower() != "running":
            self._disable_terminal()
        else:
            self._show_session_start()
    
    def _setup_ui(self):
        """Initialize AWS-style terminal UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Simple header
        header = QWidget()
        header.setStyleSheet(f"""
            background: {Colors.BG_PRIMARY};
            border-bottom: 1px solid {Colors.BORDER};
            padding: 8px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        title = QLabel(f"Session Manager > {self.instance_id}")
        title.setStyleSheet(f"""
            color: {Colors.TEXT_PRIMARY};
            font-size: {Fonts.BODY};
            font-weight: {Fonts.SEMIBOLD};
            background: transparent;
        """)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Terminate button
        terminate_btn = QPushButton("Terminate")
        terminate_btn.setStyleSheet(f"""
            QPushButton {{
                background: white;
                color: {Colors.TEXT_PRIMARY};
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 2px;
                padding: 4px 12px;
                font-size: {Fonts.SMALL};
            }}
            QPushButton:hover {{
                background: {Colors.BG_TERTIARY};
            }}
        """)
        terminate_btn.clicked.connect(self.close)
        header_layout.addWidget(terminate_btn)
        
        layout.addWidget(header)
        
        # Terminal output (black background, white text)
        self.output_display = QPlainTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: black;
                color: white;
                border: none;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 13px;
                padding: 12px;
            }
        """)
        
        font = QFont("Courier New", 10)
        self.output_display.setFont(font)
        layout.addWidget(self.output_display)
        
        # Command input
        input_container = QWidget()
        input_container.setStyleSheet(f"""
            background: black;
            border-top: 1px solid #333;
            padding: 8px;
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 8, 12, 8)
        
        # Prompt
        self.prompt_label = QLabel("sh-5.1#")
        self.prompt_label.setStyleSheet("color: white; font-family: 'Courier New'; font-size: 13px; background: transparent;")
        input_layout.addWidget(self.prompt_label)
        
        # Input field
        self.command_input = QLineEdit()
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: black;
                color: white;
                border: none;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 13px;
            }
        """)
        self.command_input.returnPressed.connect(self._execute_command)
        self.command_input.setFocus()
        input_layout.addWidget(self.command_input)
        
        layout.addWidget(input_container)
        
        # Handle up/down arrow for history
        self.command_input.keyPressEvent = self._handle_key_press
    
    def _show_session_start(self):
        """Show session start message (AWS style)"""
        self._append_plain(f"Session started for user: admin")
        self._append_plain(f"Session ID: {self.instance_id}-{hex(id(self))[2:10]}")
        self._append_plain("")
    
    def _disable_terminal(self):
        """Disable terminal when instance is not running"""
        self.command_input.setEnabled(False)
        self._append_plain(f"Cannot start session: Instance is {self.instance_status.upper()}")
        self._append_plain("Instance must be running to start a terminal session.")
    
    def _execute_command(self):
        """Execute command"""
        command = self.command_input.text().strip()
        if not command or self.is_executing:
            return
        
        # Add to history (no duplicates)
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Show command in output
        self._append_plain(f"{self.prompt_label.text()} {command}")
        
        # Clear input
        self.command_input.clear()
        
        # Execute
        self.is_executing = True
        self.command_input.setEnabled(False)
        
        try:
            result = self.compute_service.execute_command(self.instance_id, command)
            output = result.get("output", "").strip()
            
            if output:
                self._append_plain(output)
            
            self.command_executed.emit(command, output)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self._append_plain(error_msg)
        
        finally:
            self.is_executing = False
            self.command_input.setEnabled(True)
            self.command_input.setFocus()
            self._append_plain("")
    
    def _append_plain(self, text):
        """Append plain text to output"""
        self.output_display.appendPlainText(text)
        
        # Auto-scroll to bottom
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_display.setTextCursor(cursor)
    
    def _handle_key_press(self, event):
        """Handle arrow keys for command history"""
        if event.key() == Qt.Key.Key_Up:
            # Previous command
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key.Key_Down:
            # Next command
            if self.command_history and self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            elif self.history_index >= len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            # Default behavior
            QLineEdit.keyPressEvent(self.command_input, event)
    
    def clear_output(self):
        """Clear terminal output"""
        self.output_display.clear()
