"""
Micro-Interactions System - Button ripples, glows, and visual feedback
Makes CloudSim feel responsive and polished
"""

from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect, Property
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QRadialGradient, QPaintEvent, QMouseEvent
from ui.design_system import Colors


class RippleButton(QPushButton):
    """
    Button with material design ripple effect on click
    Provides satisfying visual feedback for user actions
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.ripple_radius = 0
        self.ripple_opacity = 0.0
        self.ripple_pos = QPoint()
        self.ripple_animation = None
        self.is_rippling = False
        
    def mousePressEvent(self, event: QMouseEvent):
        """Trigger ripple effect on press"""
        super().mousePressEvent(event)
        
        # Start ripple at click position
        self.ripple_pos = event.pos()
        self.ripple_radius = 0
        self.ripple_opacity = 0.4
        self.is_rippling = True
        
        # Animate ripple expansion
        self._animate_ripple()
        
    def _animate_ripple(self):
        """Animate the ripple effect"""
        max_radius = max(self.width(), self.height()) * 1.5
        duration = 600  # ms
        
        # Animate in steps for smooth effect
        steps = 30
        step_duration = duration // steps
        step_radius = max_radius / steps
        step_opacity = 0.4 / steps
        
        def update_ripple(step):
            if step >= steps:
                self.is_rippling = False
                self.update()
                return
            
            self.ripple_radius = step_radius * step
            self.ripple_opacity = 0.4 - (step_opacity * step)
            self.update()
            
            QTimer.singleShot(step_duration, lambda: update_ripple(step + 1))
        
        update_ripple(0)
    
    def paintEvent(self, event: QPaintEvent):
        """Custom paint to draw ripple effect"""
        super().paintEvent(event)
        
        if self.is_rippling and self.ripple_opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Semi-transparent white ripple
            color = QColor(255, 255, 255, int(self.ripple_opacity * 255))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            # Draw expanding circle
            painter.drawEllipse(
                self.ripple_pos,
                int(self.ripple_radius),
                int(self.ripple_radius)
            )


class GlowButton(QPushButton):
    """
    Button with glow effect on press
    Simpler alternative to ripple, uses shadow animation
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.glow_effect = None
        self.is_glowing = False
        
    def mousePressEvent(self, event: QMouseEvent):
        """Trigger glow on press"""
        super().mousePressEvent(event)
        self._start_glow()
        
    def _start_glow(self):
        """Animate glow effect"""
        if self.is_glowing:
            return
        
        self.is_glowing = True
        
        # Create or get glow effect
        if not self.glow_effect:
            self.glow_effect = QGraphicsDropShadowEffect(self)
            self.glow_effect.setColor(QColor(Colors.ACCENT))
            self.glow_effect.setBlurRadius(0)
            self.glow_effect.setOffset(0, 0)
            self.setGraphicsEffect(self.glow_effect)
        
        # Animate glow intensity
        steps = 20
        max_blur = 20
        step_duration = 25  # ms
        
        def update_glow(step):
            if step >= steps:
                self.is_glowing = False
                return
            
            # Pulse in and out
            if step < steps // 2:
                blur = (step / (steps // 2)) * max_blur
            else:
                blur = max_blur - ((step - steps // 2) / (steps // 2)) * max_blur
            
            self.glow_effect.setBlurRadius(blur)
            QTimer.singleShot(step_duration, lambda: update_glow(step + 1))
        
        update_glow(0)


def add_ripple_effect(button: QPushButton):
    """
    Add ripple effect to existing button
    Monkey-patches the mousePressEvent
    """
    original_press = button.mousePressEvent
    
    ripple_data = {
        'pos': QPoint(),
        'radius': 0,
        'opacity': 0.0,
        'active': False
    }
    
    def animate_ripple():
        max_radius = max(button.width(), button.height()) * 1.5
        steps = 30
        duration_per_step = 20
        
        def update(step):
            if step >= steps:
                ripple_data['active'] = False
                button.update()
                return
            
            ripple_data['radius'] = (max_radius / steps) * step
            ripple_data['opacity'] = 0.4 - ((0.4 / steps) * step)
            button.update()
            
            QTimer.singleShot(duration_per_step, lambda: update(step + 1))
        
        update(0)
    
    def new_mouse_press(event: QMouseEvent):
        original_press(event)
        ripple_data['pos'] = event.pos()
        ripple_data['active'] = True
        animate_ripple()
    
    def new_paint(event: QPaintEvent):
        QPushButton.paintEvent(button, event)
        
        if ripple_data['active'] and ripple_data['opacity'] > 0:
            painter = QPainter(button)
            painter.setRenderHint(QPainter.Antialiasing)
            
            color = QColor(255, 255, 255, int(ripple_data['opacity'] * 255))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.NoPen)
            
            painter.drawEllipse(
                ripple_data['pos'],
                int(ripple_data['radius']),
                int(ripple_data['radius'])
            )
    
    button.mousePressEvent = new_mouse_press
    button.paintEvent = new_paint


def add_glow_on_hover(widget):
    """Add subtle glow effect on hover"""
    original_enter = widget.enterEvent if hasattr(widget, 'enterEvent') else None
    original_leave = widget.leaveEvent if hasattr(widget, 'leaveEvent') else None
    
    glow = QGraphicsDropShadowEffect(widget)
    glow.setColor(QColor(Colors.ACCENT))
    glow.setBlurRadius(0)
    glow.setOffset(0, 0)
    widget.setGraphicsEffect(glow)
    
    def enter_event(event):
        if original_enter:
            original_enter(event)
        
        # Animate glow in
        animation = QPropertyAnimation(glow, b"blurRadius")
        animation.setDuration(200)
        animation.setStartValue(0)
        animation.setEndValue(15)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        widget._glow_animation = animation  # Keep reference
    
    def leave_event(event):
        if original_leave:
            original_leave(event)
        
        # Animate glow out
        animation = QPropertyAnimation(glow, b"blurRadius")
        animation.setDuration(200)
        animation.setStartValue(15)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        widget._glow_animation = animation
    
    widget.enterEvent = enter_event
    widget.leaveEvent = leave_event


class LoadingButton(QPushButton):
    """
    Button that shows loading state with animated dots
    Provides visual feedback during async operations
    """
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.is_loading = False
        self.dot_count = 0
        self.loading_timer = None
        
    def start_loading(self, loading_text: str = "Processing"):
        """Start loading animation"""
        if self.is_loading:
            return
        
        self.is_loading = True
        self.original_text = self.text()
        self.setEnabled(False)
        self.dot_count = 0
        
        def update_dots():
            if not self.is_loading:
                return
            
            self.dot_count = (self.dot_count + 1) % 4
            dots = "." * self.dot_count
            self.setText(f"{loading_text}{dots}")
            
            if self.loading_timer:
                self.loading_timer.start(500)
        
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(update_dots)
        self.loading_timer.start(500)
        update_dots()
    
    def stop_loading(self):
        """Stop loading and restore original state"""
        self.is_loading = False
        if self.loading_timer:
            self.loading_timer.stop()
        self.setText(self.original_text)
        self.setEnabled(True)


def create_action_button(text: str, color: str, icon: str = "") -> RippleButton:
    """
    Factory function to create styled action button with ripple effect
    """
    from ui.design_system import Fonts
    
    btn = RippleButton(f"{icon} {text}" if icon else text)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setFixedHeight(40)
    
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0 20px;
            font-size: 13px;
            font-weight: {Fonts.SEMIBOLD};
        }}
        QPushButton:hover {{
            background: {Colors.ACCENT_HOVER};
        }}
        QPushButton:pressed {{
            background: {Colors.ACCENT};
        }}
        QPushButton:disabled {{
            background: {Colors.SURFACE};
            color: {Colors.TEXT_DISABLED};
        }}
    """)
    
    return btn


# Export convenience functions
__all__ = [
    'RippleButton',
    'GlowButton',
    'LoadingButton',
    'add_ripple_effect',
    'add_glow_on_hover',
    'create_action_button'
]
