"""
Footer Component - Consistent branding across CloudSim
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class Footer(QWidget):
    """Reusable footer component with branding"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize footer UI"""
        self.setFixedHeight(40)
        self.setStyleSheet("""
            Footer {
                background: #0f172a;
                border-top: 1px solid #334155;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)
        
        # Footer text
        footer_text = QLabel("© 2026 CloudSim | Developed by Leslie Fernando | Educational Use Only")
        footer_text.setStyleSheet("""
            color: #64748b;
            font-size: 11px;
        """)
        footer_text.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(footer_text)
