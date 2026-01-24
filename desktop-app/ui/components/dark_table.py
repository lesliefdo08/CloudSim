"""
Dark Table Component - Modern table with zebra rows and status pills
"""

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QPushButton, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class DarkTable(QTableWidget):
    """Modern dark-themed table widget"""
    
    def __init__(self, columns):
        super().__init__()
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(columns)
        self.setup_style()
        
    def setup_style(self):
        """Apply modern dark styling"""
        self.setStyleSheet("""
            QTableWidget {
                background: #1e293b;
                color: #cbd5e1;
                border: 1px solid #334155;
                border-radius: 8px;
                gridline-color: #334155;
                font-size: 13px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTableWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #334155;
            }
            QTableWidget::item:selected {
                background: rgba(245, 158, 11, 0.15);
                color: #f59e0b;
            }
            QTableWidget::item:hover {
                background: rgba(100, 116, 139, 0.1);
            }
            QHeaderView::section {
                background: #0f172a;
                color: #f8fafc;
                padding: 12px 16px;
                border: none;
                border-bottom: 2px solid #f59e0b;
                font-weight: 600;
                font-size: 13px;
                text-align: left;
            }
        """)
        
        # Alternating row colors (zebra)
        self.setAlternatingRowColors(True)
        
        # Behavior
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        
    def create_status_pill(self, status, status_map=None):
        """Create a colored status pill"""
        if status_map is None:
            status_map = {
                "running": ("#10b981", "#d1fae5"),
                "stopped": ("#64748b", "#e2e8f0"),
                "error": ("#ef4444", "#fee2e2"),
                "pending": ("#f59e0b", "#fef3c7")
            }
        
        colors = status_map.get(status.lower(), ("#64748b", "#e2e8f0"))
        bg_color, text_color = colors
        
        pill = QLabel(status.upper())
        pill.setStyleSheet(f"""
            QLabel {{
                background: {bg_color};
                color: {text_color};
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 600;
            }}
        """)
        pill.setAlignment(Qt.AlignCenter)
        pill.setFixedHeight(24)
        
        return pill
    
    def create_action_buttons(self, actions):
        """Create a widget with action buttons"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        for action_name, callback in actions:
            btn = QPushButton(action_name)
            btn.clicked.connect(callback)
            btn.setStyleSheet("""
                QPushButton {
                    background: #334155;
                    color: #cbd5e1;
                    border: 1px solid #475569;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: #475569;
                    color: #f8fafc;
                    border: 1px solid #f59e0b;
                }
                QPushButton:pressed {
                    background: #1e293b;
                }
            """)
            btn.setFixedHeight(28)
            layout.addWidget(btn)
        
        layout.addStretch()
        return widget
