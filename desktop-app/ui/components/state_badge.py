"""
State Badge Component - Animated status indicators with color & micro-animations
Provides visual feedback for instance states with subtle, performant animations
"""

from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QPen, QLinearGradient, QRadialGradient
from ui.design_system import Colors


class AnimatedStateBadge(QLabel):
    """
    Animated badge for instance states with micro-animations:
    - 🟢 Running → soft pulse
    - 🟡 Pending → shimmer
    - 🔴 Stopped → static
    """
    
    def __init__(self, state: str = "stopped", parent=None):
        super().__init__(parent)
        self._state = state.lower()
        self._animation_phase = 0.0
        self._shimmer_offset = 0.0
        
        self.setFixedHeight(24)
        self.setMinimumWidth(90)
        self.setMaximumWidth(120)
        self.setAlignment(Qt.AlignCenter)
        
        self._setup_animations()
        self._update_badge()
    
    def _setup_animations(self):
        """Setup state-specific micro-animations"""
        # Pulse animation for Running state (soft, subtle)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.setInterval(50)  # 20 FPS for smoothness
        self.pulse_timer.timeout.connect(self._animate_pulse)
        
        # Shimmer animation for Pending state
        self.shimmer_timer = QTimer(self)
        self.shimmer_timer.setInterval(40)  # 25 FPS
        self.shimmer_timer.timeout.connect(self._animate_shimmer)
    
    def set_state(self, state: str):
        """Update badge state with smooth transition"""
        new_state = state.lower()
        if new_state != self._state:
            self._state = new_state
            self._stop_animations()
            self._update_badge()
    
    def _update_badge(self):
        """Update badge appearance and start appropriate animation"""
        state_config = {
            'running': {
                'text': '● RUNNING',
                'color': Colors.SUCCESS,
                'bg': 'rgba(16, 185, 129, 0.15)',
                'border': Colors.SUCCESS,
                'animate': True,
                'animation_type': 'pulse'
            },
            'pending': {
                'text': '◐ PENDING',
                'color': Colors.WARNING,
                'bg': 'rgba(245, 158, 11, 0.15)',
                'border': Colors.WARNING,
                'animate': True,
                'animation_type': 'shimmer'
            },
            'starting': {
                'text': '▶ STARTING',
                'color': Colors.INFO,
                'bg': 'rgba(59, 130, 246, 0.15)',
                'border': Colors.INFO,
                'animate': True,
                'animation_type': 'shimmer'
            },
            'stopping': {
                'text': '⏸ STOPPING',
                'color': Colors.WARNING,
                'bg': 'rgba(245, 158, 11, 0.15)',
                'border': Colors.WARNING,
                'animate': True,
                'animation_type': 'pulse'
            },
            'stopped': {
                'text': '■ STOPPED',
                'color': Colors.TEXT_MUTED,
                'bg': 'rgba(100, 116, 139, 0.1)',
                'border': Colors.TEXT_MUTED,
                'animate': False,
                'animation_type': None
            },
            'error': {
                'text': '✖ ERROR',
                'color': Colors.DANGER,
                'bg': 'rgba(239, 68, 68, 0.15)',
                'border': Colors.DANGER,
                'animate': False,
                'animation_type': None
            },
            'terminated': {
                'text': '⊗ TERMINATED',
                'color': Colors.TEXT_DISABLED,
                'bg': 'rgba(100, 116, 139, 0.08)',
                'border': Colors.TEXT_DISABLED,
                'animate': False,
                'animation_type': None
            }
        }
        
        config = state_config.get(self._state, state_config['stopped'])
        self.setText(config['text'])
        
        # Apply base styling
        self.setStyleSheet(f"""
            QLabel {{
                background: {config['bg']};
                color: {config['color']};
                border: 1px solid {config['border']};
                border-radius: 12px;
                padding: 4px 12px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
        """)
        
        # Start appropriate animation
        if config['animate']:
            if config['animation_type'] == 'pulse':
                self.pulse_timer.start()
            elif config['animation_type'] == 'shimmer':
                self.shimmer_timer.start()
    
    def _animate_pulse(self):
        """Soft pulse animation for Running state - very subtle"""
        import math
        self._animation_phase += 0.08  # Slow, gentle pulse
        
        # Sine wave for smooth pulsing (0.85 to 1.0 opacity)
        opacity = 0.85 + (math.sin(self._animation_phase) * 0.075)
        
        # Apply subtle glow effect through opacity
        if not hasattr(self, '_opacity_effect'):
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)
        
        self._opacity_effect.setOpacity(opacity)
    
    def _animate_shimmer(self):
        """Shimmer animation for Pending/Starting states"""
        self._shimmer_offset += 3.0  # Shimmer speed
        if self._shimmer_offset > 100:
            self._shimmer_offset = -50
        
        # Create shimmer effect with gradient overlay
        # Using opacity modulation for subtle shimmer
        import math
        shimmer_intensity = (math.sin(self._shimmer_offset * 0.1) + 1) / 2  # 0 to 1
        opacity = 0.75 + (shimmer_intensity * 0.25)  # 0.75 to 1.0
        
        if not hasattr(self, '_opacity_effect'):
            self._opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self._opacity_effect)
        
        self._opacity_effect.setOpacity(opacity)
    
    def _stop_animations(self):
        """Stop all running animations"""
        self.pulse_timer.stop()
        self.shimmer_timer.stop()
        self._animation_phase = 0.0
        self._shimmer_offset = 0.0
        
        # Reset opacity
        if hasattr(self, '_opacity_effect'):
            self._opacity_effect.setOpacity(1.0)
    
    def showEvent(self, event):
        """Start animations when badge becomes visible"""
        super().showEvent(event)
        self._update_badge()
    
    def hideEvent(self, event):
        """Stop animations when badge is hidden"""
        super().hideEvent(event)
        self._stop_animations()


class StateTransitionManager:
    """
    Manages smooth state transitions with visual feedback
    Handles: Stopped → Starting → Running
    """
    
    @staticmethod
    def get_transition_sequence(from_state: str, to_state: str) -> list:
        """Get intermediate states for smooth transition"""
        from_state = from_state.lower()
        to_state = to_state.lower()
        
        transitions = {
            ('stopped', 'running'): ['starting', 'running'],
            ('running', 'stopped'): ['stopping', 'stopped'],
            ('stopped', 'pending'): ['pending'],
            ('pending', 'running'): ['starting', 'running'],
        }
        
        key = (from_state, to_state)
        return transitions.get(key, [to_state])
    
    @staticmethod
    def get_transition_duration(state: str) -> int:
        """Get duration (ms) for each transition state"""
        durations = {
            'starting': 1500,  # Show 'Starting' for 1.5s
            'stopping': 1000,  # Show 'Stopping' for 1s
            'pending': 2000,   # Show 'Pending' for 2s
        }
        return durations.get(state.lower(), 500)


def create_state_badge(state: str, parent=None) -> AnimatedStateBadge:
    """Factory function to create animated state badge"""
    return AnimatedStateBadge(state, parent)
