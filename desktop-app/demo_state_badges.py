"""
Interactive State Badge Demo - Shows animations and transitions
"""
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QGroupBox
)
from PySide6.QtCore import Qt, QTimer

sys.path.insert(0, '..')

from ui.components.state_badge import AnimatedStateBadge, StateTransitionManager
from ui.design_system import Colors


class StateBadgeDemo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudSim - Animated State Badges Demo")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(f"background: {Colors.BACKGROUND};")
        
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title = QLabel("🎨 Animated State Badges")
        title.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {Colors.TEXT_PRIMARY};
            margin-bottom: 10px;
        """)
        layout.addWidget(title)
        
        subtitle = QLabel("Subtle micro-animations for enhanced instance state visibility")
        subtitle.setStyleSheet(f"""
            font-size: 14px;
            color: {Colors.TEXT_SECONDARY};
            margin-bottom: 20px;
        """)
        layout.addWidget(subtitle)
        
        # All States Section
        states_group = self._create_states_group()
        layout.addWidget(states_group)
        
        # Interactive Transition Section
        transition_group = self._create_transition_group()
        layout.addWidget(transition_group)
        
        layout.addStretch()
        
    def _create_states_group(self):
        group = QGroupBox("All State Badges")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
                margin-top: 12px;
                background: {Colors.SURFACE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        states = [
            ('running', '🟢 Running - Soft pulse animation (healthy state)'),
            ('pending', '🟡 Pending - Shimmer animation (initializing)'),
            ('starting', '▶️ Starting - Shimmer animation (transition state)'),
            ('stopping', '⏸ Stopping - Pulse animation (transition state)'),
            ('stopped', '🔴 Stopped - Static (no animation)'),
            ('error', '✖ Error - Static (failure state)'),
            ('terminated', '⊗ Terminated - Static (removed)'),
        ]
        
        for state, description in states:
            row = QHBoxLayout()
            
            badge = AnimatedStateBadge(state)
            badge.setFixedWidth(140)
            row.addWidget(badge)
            
            desc = QLabel(description)
            desc.setStyleSheet(f"""
                font-size: 13px;
                color: {Colors.TEXT_SECONDARY};
            """)
            row.addWidget(desc)
            row.addStretch()
            
            group_layout.addLayout(row)
        
        return group
    
    def _create_transition_group(self):
        group = QGroupBox("Interactive State Transitions")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 12px;
                padding: 20px;
                margin-top: 12px;
                background: {Colors.SURFACE};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(20)
        
        # Current badge display
        badge_row = QHBoxLayout()
        badge_label = QLabel("Current State:")
        badge_label.setStyleSheet(f"font-size: 14px; color: {Colors.TEXT_SECONDARY};")
        badge_label.setFixedWidth(120)
        badge_row.addWidget(badge_label)
        
        self.demo_badge = AnimatedStateBadge('stopped')
        self.demo_badge.setFixedWidth(140)
        badge_row.addWidget(self.demo_badge)
        badge_row.addStretch()
        
        group_layout.addLayout(badge_row)
        
        # Control buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        
        # Transition buttons
        transitions = [
            ('Start Instance', 'stopped', 'running', Colors.SUCCESS),
            ('Stop Instance', 'running', 'stopped', Colors.WARNING),
            ('Simulate Pending', 'stopped', 'pending', Colors.INFO),
            ('Force Error', 'running', 'error', Colors.DANGER),
        ]
        
        for label, from_state, to_state, color in transitions:
            btn = QPushButton(label)
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0 20px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background: {Colors.ACCENT_HOVER};
                }}
                QPushButton:pressed {{
                    background: {Colors.ACCENT};
                }}
            """)
            btn.clicked.connect(lambda checked, f=from_state, t=to_state: self._transition_state(f, t))
            button_row.addWidget(btn)
        
        button_row.addStretch()
        group_layout.addLayout(button_row)
        
        # Status text
        self.status_label = QLabel("Click a button to see state transitions with intermediate states")
        self.status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.TEXT_MUTED};
            font-style: italic;
        """)
        group_layout.addWidget(self.status_label)
        
        return group
    
    def _transition_state(self, from_state, to_state):
        current_state = self.demo_badge._state
        
        # Get transition sequence
        sequence = StateTransitionManager.get_transition_sequence(current_state, to_state)
        
        self.status_label.setText(f"Transitioning: {current_state} → {' → '.join(sequence)}")
        self.status_label.setStyleSheet(f"""
            font-size: 12px;
            color: {Colors.ACCENT};
            font-weight: 600;
        """)
        
        # Execute transition sequence
        self._execute_sequence(sequence, 0)
    
    def _execute_sequence(self, sequence, index):
        if index >= len(sequence):
            self.status_label.setStyleSheet(f"""
                font-size: 12px;
                color: {Colors.SUCCESS};
                font-weight: 600;
            """)
            self.status_label.setText(f"✓ Transition complete - Current state: {sequence[-1]}")
            return
        
        state = sequence[index]
        self.demo_badge.set_state(state)
        
        # Schedule next transition
        duration = StateTransitionManager.get_transition_duration(state)
        QTimer.singleShot(duration, lambda: self._execute_sequence(sequence, index + 1))


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = StateBadgeDemo()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
