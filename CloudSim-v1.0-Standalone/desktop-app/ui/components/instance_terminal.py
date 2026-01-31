"""
Instance Terminal - Interactive shell for Docker-backed compute instances
Provides AWS EC2-like browser terminal experience
"""

import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, 
                                QLineEdit, QLabel, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor, QColor


class InstanceTerminal(QWidget):
    """Terminal widget for executing commands in compute instances"""
    
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
        self._update_prompt()
        
        # Check if terminal should be enabled
        if instance_status.lower() != "running":
            self._disable_terminal(f"Instance is {instance_status.upper()}")
        else:
            # Auto-connect message
            QTimer.singleShot(100, self._show_connected_message)
    
    def _show_connected_message(self):
        """Show connection message with AWS-like welcome"""
        self._append_output("=" * 60, "#4ec9b0")
        self._append_output(f"CloudSim Terminal - Instance {self.instance_id}", "#4ec9b0")
        self._append_output(f"Instance Name: {self.instance_name}", "#808080")
        self._append_output("=" * 60, "#4ec9b0")
        self._append_output("", "#808080")
        self._append_output("Welcome to the CloudSim EC2 instance terminal.", "#cccccc")
        self._append_output("Type commands and press Enter to execute.", "#808080")
        self._append_output("Use ↑/↓ arrows to navigate command history.", "#808080")
        self._append_output("", "#808080")
    
    def _setup_ui(self):
        """Initialize terminal UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setStyleSheet("background-color: #1e1e1e; padding: 8px;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Status indicator
        self.status_label = QLabel("● CONNECTED")
        self.status_label.setStyleSheet("color: #4ec9b0; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addSpacing(10)
        
        title = QLabel(f"🖥️ {self.instance_name} ({self.instance_id})")
        title.setStyleSheet("color: #d4d4d4; font-weight: bold; font-size: 13px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)
        clear_btn.clicked.connect(self._clear_output)
        header_layout.addWidget(clear_btn)
        
        layout.addWidget(header)
        
        # Terminal output display
        self.output_display = QPlainTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0c0c0c;
                color: #cccccc;
                border: none;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        
        # Set monospace font
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.output_display.setFont(font)
        
        layout.addWidget(self.output_display)
        
        # Command input area
        input_container = QWidget()
        input_container.setStyleSheet("background-color: #1e1e1e; padding: 8px;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(10, 5, 10, 5)
        
        # Prompt label
        self.prompt_label = QLabel("$")
        self.prompt_label.setStyleSheet("color: #4ec9b0; font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;")
        input_layout.addWidget(self.prompt_label)
        
        # Command input
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Enter command... (e.g., ls, whoami, pwd)")
        self.command_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QLineEdit:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border: 1px solid #2a2a2a;
            }
        """)
        self.command_input.returnPressed.connect(self._execute_command)
        input_layout.addWidget(self.command_input)
        
        # Execute button
        self.exec_btn = QPushButton("Execute")
        self.exec_btn.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 6px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5a8f;
            }
            QPushButton:disabled {
                background-color: #3a3a3a;
                color: #666666;
            }
        """)
        self.exec_btn.clicked.connect(self._execute_command)
        input_layout.addWidget(self.exec_btn)
        
        layout.addWidget(input_container)
        
        self.setLayout(layout)
        
        # Focus command input
        self.command_input.setFocus()
    
    def _update_prompt(self):
        """Update terminal prompt to match Linux shell style"""
        prompt = f"root@{self.instance_id[:8]}:~$"
        self.prompt_label.setText(prompt)
    
    def _disable_terminal(self, reason: str):
        """Disable terminal with error message"""
        self.command_input.setEnabled(False)
        self.exec_btn.setEnabled(False)
        self.status_label.setText("● DISCONNECTED")
        self.status_label.setStyleSheet("color: #f48771; font-weight: bold; font-size: 11px;")
        
        self._append_output("=" * 60, "#f48771")
        self._append_output("Terminal Unavailable", "#f48771")
        self._append_output("=" * 60, "#f48771")
        self._append_output("", "#808080")
        self._append_output(f"⚠️  {reason}", "#f48771")
        self._append_output("", "#808080")
        self._append_output("Please ensure the instance is RUNNING to use the terminal.", "#808080")
    
    def _execute_command(self):
        """Execute command in container"""
        command = self.command_input.text().strip()
        
        if not command:
            return
        
        if self.is_executing:
            return
        
        # Add to history (avoid duplicates)
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command with prompt
        prompt = self.prompt_label.text()
        self._append_output(f"{prompt} {command}", "#d4d4d4")
        
        # Clear input and disable during execution
        self.command_input.clear()
        self.command_input.setEnabled(False)
        self.exec_btn.setEnabled(False)
        self.is_executing = True
        self.status_label.setText("● EXECUTING...")
        self.status_label.setStyleSheet("color: #ce9178; font-weight: bold; font-size: 11px;")
        
        # Simulate network latency then execute
        latency_ms = random.randint(300, 800)
        QTimer.singleShot(latency_ms, lambda: self._do_execute(command))
    
    def _do_execute(self, command: str):
        """Actually execute the command after latency"""
        try:
            result = self.compute_service.execute_command(self.instance_id, command)
            
            # Check for backend/connection errors
            if result['exit_code'] == 1 and 'Backend not available' in result.get('error', ''):
                self._append_output("", "#cccccc")
                self._append_output("⚠️  Backend Connection Error", "#f48771")
                self._append_output("The backend server is not responding.", "#f48771")
                self._append_output("Please ensure the backend is running on http://127.0.0.1:8000", "#808080")
                self._append_output("", "#cccccc")
            elif result['exit_code'] == 1 and 'not running' in result.get('error', '').lower():
                self._append_output("", "#cccccc")
                self._append_output("⚠️  Container Not Running", "#f48771")
                self._append_output("The instance container is not in running state.", "#f48771")
                self._append_output("Please start the instance before using the terminal.", "#808080")
                self._append_output("", "#cccccc")
            else:
                # Display output
                if result.get('output'):
                    self._append_output(result['output'].rstrip(), "#cccccc")
                
                # Display errors
                if result.get('error'):
                    self._append_output(result['error'].rstrip(), "#f48771")
                
                # Show exit code if non-zero
                if result.get('exit_code', 0) != 0 and not result.get('error'):
                    self._append_output(f"Command exited with code {result['exit_code']}", "#ce9178")
                
                # Add blank line for readability
                self._append_output("", "#cccccc")
        
        except Exception as e:
            self._append_output("", "#cccccc")
            self._append_output(f"⚠️  Unexpected Error: {str(e)}", "#f48771")
            self._append_output("Please check backend connectivity and instance state.", "#808080")
            self._append_output("", "#cccccc")
        
        finally:
            # Re-enable input
            self.command_input.setEnabled(True)
            self.exec_btn.setEnabled(True)
            self.command_input.setFocus()
            self.is_executing = False
            self.status_label.setText("● CONNECTED")
            self.status_label.setStyleSheet("color: #4ec9b0; font-weight: bold; font-size: 11px;")
            
            # Emit signal
            if 'result' in locals():
                self.command_executed.emit(command, result.get('output', ''))
    
    def _append_output(self, text: str, color: str = "#cccccc"):
        """Append text to terminal output"""
        cursor = self.output_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        
        # Set text color
        char_format = cursor.charFormat()
        char_format.setForeground(QColor(color))
        cursor.setCharFormat(char_format)
        
        cursor.insertText(text + "\n")
        
        # Scroll to bottom
        self.output_display.setTextCursor(cursor)
        self.output_display.ensureCursorVisible()
    
    def _clear_output(self):
        """Clear terminal output and show welcome message again"""
        self.output_display.clear()
        self._append_output("Terminal cleared.", "#4ec9b0")
        self._append_output("", "#808080")
        
        # Show prompt hint
        if self.instance_status.lower() == "running":
            self._append_output("Type commands and press Enter to execute.", "#808080")
            self._append_output("Use ↑/↓ arrows to navigate command history.", "#808080")
            self._append_output("", "#808080")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for command history"""
        # Only handle if input is enabled
        if not self.command_input.isEnabled():
            super().keyPressEvent(event)
            return
        
        # Command history navigation
        if event.key() == Qt.Key_Up:
            if self.command_history and self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
                event.accept()
        elif event.key() == Qt.Key_Down:
            if self.command_history:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.command_input.setText(self.command_history[self.history_index])
                else:
                    self.history_index = len(self.command_history)
                    self.command_input.clear()
                event.accept()
        else:
            super().keyPressEvent(event)
