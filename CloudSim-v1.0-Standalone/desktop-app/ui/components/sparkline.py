"""
Sparkline Chart Component - Mini line charts for trend visualization
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath
from typing import List


class SparklineChart(QWidget):
    """
    Lightweight sparkline chart for showing trends in small spaces
    
    Features:
    - Smooth line rendering with gradient fill
    - Auto-scaling to data range
    - Minimal footprint (40-60px height)
    - Color-coded trends (positive=green, negative=red)
    """
    
    def __init__(self, data: List[float] = None, color: str = None, parent=None):
        """
        Initialize sparkline chart
        
        Args:
            data: List of numeric values to plot
            color: Line color (hex). If None, auto-determined by trend
            parent: Parent widget
        """
        super().__init__(parent)
        self.data = data or []
        self.color = color
        self.setMinimumHeight(40)
        self.setMaximumHeight(60)
        
    def set_data(self, data: List[float], color: str = None):
        """
        Update chart data
        
        Args:
            data: New data points
            color: Optional color override
        """
        self.data = data
        if color:
            self.color = color
        self.update()
    
    def _determine_trend_color(self) -> str:
        """Determine color based on overall trend"""
        if not self.data or len(self.data) < 2:
            return "#64748b"  # Neutral gray
        
        first_half_avg = sum(self.data[:len(self.data)//2]) / (len(self.data)//2)
        second_half_avg = sum(self.data[len(self.data)//2:]) / (len(self.data) - len(self.data)//2)
        
        if second_half_avg > first_half_avg:
            return "#10b981"  # Green (growing)
        elif second_half_avg < first_half_avg:
            return "#ef4444"  # Red (declining)
        else:
            return "#64748b"  # Neutral (stable)
    
    def paintEvent(self, event):
        """Custom paint event for sparkline rendering"""
        if not self.data or len(self.data) < 2:
            return
        
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Get drawing area
            width = self.width()
            height = self.height()
            
            if width <= 0 or height <= 0:
                return
            
            padding = 4
            draw_width = width - (2 * padding)
            draw_height = height - (2 * padding)
            
            if draw_width <= 0 or draw_height <= 0:
                return
            
            # Determine color
            line_color = self.color if self.color else self._determine_trend_color()
            
            # Calculate scaling factors
            min_val = min(self.data)
            max_val = max(self.data)
            value_range = max_val - min_val if max_val != min_val else 1
            
            # Create path for line
            path = QPainterPath()
            points = []
            
            for i, value in enumerate(self.data):
                # Calculate x position (evenly spaced)
                x = padding + (i / (len(self.data) - 1)) * draw_width
                
                # Calculate y position (inverted because Qt y-axis goes down)
                normalized = (value - min_val) / value_range
                y = padding + draw_height - (normalized * draw_height)
                
                points.append(QPointF(x, y))
            
            # Draw line
            if points:
                path.moveTo(points[0])
                for point in points[1:]:
                    path.lineTo(point)
                
                # Draw the line
                pen = QPen(QColor(line_color))
                pen.setWidth(2)
                pen.setCapStyle(Qt.RoundCap)
                pen.setJoinStyle(Qt.RoundJoin)
                painter.setPen(pen)
                painter.drawPath(path)
                
                # Optional: Draw fill area with gradient
                fill_path = QPainterPath(path)
                fill_path.lineTo(points[-1].x(), height)
                fill_path.lineTo(points[0].x(), height)
                fill_path.closeSubpath()
                
                fill_color = QColor(line_color)
                fill_color.setAlpha(30)  # 12% opacity
                painter.fillPath(fill_path, fill_color)
                
                # Draw dots at data points
                dot_color = QColor(line_color)
                painter.setPen(Qt.NoPen)
                painter.setBrush(dot_color)
                for point in points:
                    painter.drawEllipse(point, 2, 2)
        finally:
            painter.end()


class InsightCard(QWidget):
    """
    Actionable insight card with icon, message, and optional CTA
    
    Features:
    - Color-coded severity (warning, info, success)
    - Icon + multi-line message
    - Optional action button
    - Hover effects
    """
    
    def __init__(self, icon: str, title: str, message: str, 
                 severity: str = "info", parent=None):
        """
        Initialize insight card
        
        Args:
            icon: Emoji or icon character
            title: Bold heading
            message: Descriptive text
            severity: "info", "warning", "success", "error"
            parent: Parent widget
        """
        super().__init__(parent)
        self.icon = icon
        self.title = title
        self.message = message
        self.severity = severity
        self.init_ui()
    
    def init_ui(self):
        """Build insight card UI"""
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel
        from ui.design_system import Colors
        
        # Determine colors based on severity
        severity_colors = {
            "info": ("#3b82f6", "#1e3a8a"),
            "warning": ("#f59e0b", "#78350f"),
            "success": ("#10b981", "#064e3b"),
            "error": ("#ef4444", "#7f1d1d")
        }
        
        accent_color, bg_accent = severity_colors.get(self.severity, severity_colors["info"])
        
        self.setStyleSheet(f"""
            InsightCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CARD}, stop:1 {bg_accent}15);
                border: 1px solid {accent_color}40;
                border-left: 3px solid {accent_color};
                border-radius: 8px;
                padding: 12px 16px;
            }}
            InsightCard:hover {{
                border: 1px solid {accent_color}80;
                border-left: 3px solid {accent_color};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.CARD}, stop:1 {bg_accent}25);
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            font-size: 24px;
            color: {accent_color};
        """)
        icon_label.setAlignment(Qt.AlignTop)
        layout.addWidget(icon_label)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: #f8fafc;
        """)
        title_label.setWordWrap(True)
        content_layout.addWidget(title_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setStyleSheet("""
            font-size: 12px;
            color: #94a3b8;
            line-height: 1.4;
        """)
        message_label.setWordWrap(True)
        content_layout.addWidget(message_label)
        
        layout.addLayout(content_layout, 1)


class GhostTimelineEntry(QWidget):
    """
    Ghost/skeleton timeline entry for empty state
    
    Shows subtle placeholder when no activity exists
    """
    
    def __init__(self, message: str = "Awaiting activity…", parent=None):
        """
        Initialize ghost entry
        
        Args:
            message: Placeholder text
            parent: Parent widget
        """
        super().__init__(parent)
        self.message = message
        self.init_ui()
    
    def init_ui(self):
        """Build ghost timeline UI"""
        from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QGraphicsOpacityEffect
        from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Timeline dot (pulsing)
        dot = QLabel("○")
        dot.setStyleSheet("""
            font-size: 14px;
            color: #334155;
        """)
        dot.setAlignment(Qt.AlignTop)
        layout.addWidget(dot)
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(4)
        
        # Timestamp placeholder
        time_label = QLabel("--:--:--")
        time_label.setStyleSheet("""
            font-size: 11px;
            color: #334155;
            font-family: 'Consolas', monospace;
        """)
        content_layout.addWidget(time_label)
        
        # Message
        message_label = QLabel(self.message)
        message_label.setStyleSheet("""
            font-size: 13px;
            color: #475569;
            font-style: italic;
        """)
        content_layout.addWidget(message_label)
        
        layout.addLayout(content_layout, 1)
        
        # Subtle fade animation
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(2000)
        self.fade_animation.setStartValue(0.3)
        self.fade_animation.setEndValue(0.6)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.setLoopCount(-1)  # Loop forever
        self.fade_animation.start()
