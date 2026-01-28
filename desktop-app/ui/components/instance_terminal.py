"""
Instance Terminal - Interactive shell for Docker-backed compute instances
"""

import random
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPlainTextEdit, 
                                QLineEdit, QLabel, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QTextCursor, QColor


class InstanceTerminal(QWidget):
    """Terminal widget for executing commands in compute instances"""
    
    command_executed = Signal(str, str)  # command, output
    
    def __init__(self, instance_id: str, instance_name: str, docker_service, parent=None):
        super().__init__(parent)
        self.instance_id = instance_id
        self.instance_name = instance_name
        self.docker_service = docker_service
        self.container_id = None
        self.command_history = []
        self.history_index = -1
        
        self._setup_ui()
    
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
        
        title = QLabel(f"🖥️ Terminal: {self.instance_name} ({self.instance_id})")
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
        self.command_input.setPlaceholderText("Enter command...")
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
        """)
        self.command_input.returnPressed.connect(self._execute_command)
        input_layout.addWidget(self.command_input)
        
        # Execute button
        exec_btn = QPushButton("Execute")
        exec_btn.setStyleSheet("""
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
        """)
        exec_btn.clicked.connect(self._execute_command)
        input_layout.addWidget(exec_btn)
        
        layout.addWidget(input_container)
        
        self.setLayout(layout)
        
        # Focus command input
        self.command_input.setFocus()
    
    def set_container_id(self, container_id: str):
        """Set the Docker container ID for command execution"""
        self.container_id = container_id
        self._update_prompt()
        self._append_output("Connected to container.", "#4ec9b0")
        self._append_output(f"Type commands and press Enter to execute.\n", "#808080")
    
    def _update_prompt(self):
        """Update terminal prompt"""
        if self.container_id:
            prompt = f"root@{self.instance_id[:8]}:~$"
        else:
            prompt = "$"
        self.prompt_label.setText(prompt)
    
    def _execute_command(self):
        """Execute command in container"""
        command = self.command_input.text().strip()
        
        if not command:
            return
        
        if not self.container_id:
            self._append_output("ERROR: No container connected", "#f48771")
            return
        
        # Add to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command
        prompt = self.prompt_label.text()
        self._append_output(f"{prompt} {command}", "#d4d4d4")
        
        # Clear input
        self.command_input.clear()
        self.command_input.setEnabled(False)
        
        # Simulate network latency then execute
        latency_ms = random.randint(300, 800)
        QTimer.singleShot(latency_ms, lambda: self._do_execute(command))
    
    def _do_execute(self, command: str):
        """Actually execute the command after latency"""
        result = self.docker_service.execute_command(self.container_id, command)
        
        # Display output
        if result['output']:
            self._append_output(result['output'].rstrip(), "#cccccc")
        
        # Display errors
        if result['error']:
            self._append_output(result['error'].rstrip(), "#f48771")
        
        # Show exit code if non-zero
        if result['exit_code'] != 0 and not result['error']:
            self._append_output(f"(exit code: {result['exit_code']})", "#ce9178")
        
        # Add blank line
        self._append_output("", "#cccccc")
        
        # Re-enable input
        self.command_input.setEnabled(True)
        self.command_input.setFocus()
        
        # Emit signal
        self.command_executed.emit(command, result['output'])
    
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
        """Clear terminal output"""
        self.output_display.clear()
        self._append_output("Terminal cleared.", "#4ec9b0")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Command history navigation
        if event.key() == Qt.Key_Up:
            if self.history_index > 0:
                self.history_index -= 1
                self.command_input.setText(self.command_history[self.history_index])
        elif event.key() == Qt.Key_Down:
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_input.setText(self.command_history[self.history_index])
            else:
                self.history_index = len(self.command_history)
                self.command_input.clear()
        else:
            super().keyPressEvent(event)
