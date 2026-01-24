"""
Test script for AnimatedStateBadge component
"""
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

# Add parent directory to path
sys.path.insert(0, '..')

from ui.components.state_badge import AnimatedStateBadge
from ui.design_system import Colors


def main():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("State Badge Test")
    window.setMinimumSize(600, 400)
    window.setStyleSheet(f"background: {Colors.BACKGROUND};")
    
    layout = QVBoxLayout(window)
    layout.setSpacing(20)
    layout.setContentsMargins(40, 40, 40, 40)
    
    # Title
    title = QLabel("Animated State Badges Test")
    title.setStyleSheet(f"""
        font-size: 24px;
        font-weight: 700;
        color: {Colors.TEXT_PRIMARY};
        margin-bottom: 20px;
    """)
    layout.addWidget(title)
    
    # Test all states
    states = ['running', 'pending', 'starting', 'stopping', 'stopped', 'error', 'terminated']
    
    for state in states:
        row = QHBoxLayout()
        
        label = QLabel(f"{state.title()}:")
        label.setFixedWidth(120)
        label.setStyleSheet(f"""
            font-size: 14px;
            color: {Colors.TEXT_SECONDARY};
        """)
        row.addWidget(label)
        
        badge = AnimatedStateBadge(state)
        row.addWidget(badge)
        
        row.addStretch()
        layout.addLayout(row)
    
    layout.addStretch()
    
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
