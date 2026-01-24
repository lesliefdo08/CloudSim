"""
CloudSim Design System - Modern SaaS UI Components
Professional, engaging, and accessible design system
"""

# ============================================
# COLOR PALETTE - Modern SaaS
# ============================================

class Colors:
    """Modern light-on-dark theme with vibrant accents"""
    
    # Primary Colors
    PRIMARY = "#0f172a"      # Deep navy background
    PRIMARY_LIGHT = "#1e293b"  # Lighter navy for surfaces
    SECONDARY = "#1e293b"    # Slate surface
    ACCENT = "#6366f1"       # Modern indigo
    ACCENT_HOVER = "#818cf8" # Lighter indigo
    
    # Status Colors
    SUCCESS = "#10b981"      # Emerald
    DANGER = "#ef4444"       # Red
    WARNING = "#f59e0b"      # Amber
    INFO = "#3b82f6"         # Blue
    PURPLE = "#a855f7"       # Purple
    TEAL = "#14b8a6"         # Teal
    
    # Status Backgrounds
    WARNING_BG = "rgba(245, 158, 11, 0.1)"
    DANGER_BG = "rgba(239, 68, 68, 0.1)"
    SUCCESS_BG = "rgba(16, 185, 129, 0.1)"
    INFO_BG = "rgba(59, 130, 246, 0.1)"
    
    # UI Colors
    BACKGROUND = "#0a0f1e"
    SURFACE = "#1e293b"
    SURFACE_HOVER = "#2d3a4f"
    CARD = "#1e293b"
    CARD_HOVER = "#2d3a4f"
    BORDER = "#334155"
    BORDER_LIGHT = "#475569"
    
    # Text Colors
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#cbd5e1"
    TEXT_MUTED = "#94a3b8"
    TEXT_DISABLED = "#64748b"
    
    # Service Colors (refined for consistency)
    COMPUTE = "#3b82f6"      # Blue - EC2 instances
    STORAGE = "#10b981"      # Green - S3 buckets
    DATABASE = "#a855f7"     # Purple - RDS databases
    SERVERLESS = "#f59e0b"   # Orange - Lambda functions
    VOLUMES = "#06b6d4"      # Cyan - EBS volumes
    
    # Service Color Variants (hover states, backgrounds)
    COMPUTE_HOVER = "#60a5fa"
    STORAGE_HOVER = "#34d399"
    DATABASE_HOVER = "#c084fc"
    SERVERLESS_HOVER = "#fbbf24"
    
    COMPUTE_BG = "rgba(59, 130, 246, 0.1)"
    STORAGE_BG = "rgba(16, 185, 129, 0.1)"
    DATABASE_BG = "rgba(168, 85, 247, 0.1)"
    SERVERLESS_BG = "rgba(245, 158, 11, 0.1)"
    
    # Shadows
    SHADOW_SM = "rgba(0, 0, 0, 0.1)"
    SHADOW_MD = "rgba(0, 0, 0, 0.2)"
    SHADOW_LG = "rgba(0, 0, 0, 0.3)"
    
    # Depth shadows for metric sections (elevated appearance)
    METRIC_SHADOW = "0 4px 12px rgba(0, 0, 0, 0.25), 0 2px 4px rgba(0, 0, 0, 0.15)"
    SECTION_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.2)"
    
    # Opacity levels
    SECONDARY_OPACITY = "0.6"  # For IDs, timestamps, regions (60%)
    TERTIARY_OPACITY = "0.4"   # For very low-priority info


# ============================================
# TYPOGRAPHY - Modern
# ============================================

class Fonts:
    """Typography system with modern font stack"""
    
    # Font Families
    PRIMARY = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    MONOSPACE = "'JetBrains Mono', 'Consolas', 'Courier New', monospace"
    
    # Font Sizes
    HERO = "36px"
    TITLE = "28px"
    SUBTITLE = "20px"
    HEADING = "16px"
    BODY = "14px"
    SMALL = "13px"
    TINY = "11px"
    
    # Metric-specific sizes (30-40% larger for visual dominance)
    METRIC_HUGE = "48px"      # Primary metrics (counts, costs)
    METRIC_LARGE = "40px"     # Secondary metrics
    METRIC_LABEL = "12px"     # Metric labels
    
    # Font Weights
    LIGHT = "300"
    REGULAR = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"
    EXTRABOLD = "800"
    HEAVY = "900"             # For critical metrics


# ============================================
# SPACING - 8px baseline
# ============================================

class Spacing:
    """Consistent spacing system based on 8px grid"""
    
    XXS = "2px"
    XS = "4px"
    SM = "8px"
    MD = "16px"
    LG = "24px"
    XL = "32px"
    XXL = "48px"
    XXXL = "64px"


# ============================================
# ANIMATIONS
# ============================================

class Animations:
    """Animation and transition durations"""
    
    FAST = "150ms"
    NORMAL = "250ms"
    SLOW = "350ms"
    
    EASING = "cubic-bezier(0.4, 0.0, 0.2, 1)"


# ============================================
# COMPONENT STYLES - Modern SaaS
# ============================================

class Styles:
    """Modern, engaging component styles"""
    
    @staticmethod
    def primary_button():
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT}, stop:1 {Colors.ACCENT_HOVER});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.ACCENT_HOVER}, stop:1 #a5b4fc);
                padding: 12px 26px;
            }}
            QPushButton:pressed {{
                background: #4f46e5;
                padding: 12px 24px;
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def secondary_button():
        return f"""
            QPushButton {{
                background: {Colors.SURFACE};
                color: {Colors.TEXT_PRIMARY};
                border: 1.5px solid {Colors.BORDER_LIGHT};
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.MEDIUM};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: {Colors.SURFACE_HOVER};
                border-color: {Colors.ACCENT};
                color: {Colors.ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background: #374151;
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def success_button():
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.SUCCESS}, stop:1 #34d399);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #34d399, stop:1 #6ee7b7);
            }}
            QPushButton:pressed {{
                background: #059669;
            }}
        """
    
    @staticmethod
    def danger_button():
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.DANGER}, stop:1 #f87171);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: {Fonts.BODY};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f87171, stop:1 #fca5a5);
            }}
            QPushButton:pressed {{
                background: #dc2626;
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def card():
        """Modern card with subtle shadow and hover effect"""
        return f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                padding: {Spacing.LG};
            }}
            QFrame:hover {{
                border-color: {Colors.ACCENT};
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.CARD_HOVER}, stop:1 #1f2937);
            }}
        """
    
    @staticmethod
    def table():
        """Modern table with hover states and status badges"""
        return f"""
            QTableWidget {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                color: {Colors.TEXT_PRIMARY};
                gridline-color: transparent;
                font-size: {Fonts.BODY};
                font-family: {Fonts.PRIMARY};
                selection-background-color: transparent;
            }}
            QTableWidget::item {{
                padding: 14px 12px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
            }}
            QTableWidget::item:selected {{
                background: transparent;
                color: {Colors.TEXT_PRIMARY};
            }}
            QTableWidget::item:hover {{
                background: {Colors.SURFACE_HOVER};
            }}
            QHeaderView::section {{
                background: {Colors.PRIMARY};
                color: {Colors.TEXT_SECONDARY};
                padding: 16px 12px;
                border: none;
                border-bottom: 2px solid {Colors.ACCENT};
                font-weight: {Fonts.SEMIBOLD};
                font-size: {Fonts.SMALL};
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            QTableWidget::item:last {{
                border-bottom: none;
            }}
        """
    
    @staticmethod
    def input():
        """Modern input fields with focus states"""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background: {Colors.PRIMARY};
                border: 1.5px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 12px 16px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                font-family: {Fonts.PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.ACCENT};
                background: #1a2332;
            }}
            QLineEdit:hover, QTextEdit:hover, QSpinBox:hover, QComboBox:hover {{
                border-color: {Colors.BORDER_LIGHT};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
                border-color: {Colors.BORDER};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {Colors.BORDER};
                border: none;
                border-radius: 4px;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background: {Colors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                border-left: 1px solid {Colors.BORDER};
                border-radius: 0px 6px 6px 0px;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: 2px solid {Colors.TEXT_SECONDARY};
                border-top: none;
                border-right: none;
                width: 8px;
                height: 8px;
                transform: rotate(-45deg);
            }}
            QComboBox QAbstractItemView {{
                background: {Colors.SURFACE};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 4px;
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.ACCENT};
            }}
        """
    
    @staticmethod
    def dialog():
        """Modern dialog styling"""
        return f"""
            QDialog {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.SURFACE}, stop:1 #1a2535);
                border: 1px solid {Colors.BORDER_LIGHT};
                border-radius: 16px;
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                font-family: {Fonts.PRIMARY};
            }}
        """
    
    @staticmethod
    def status_badge(status: str):
        """Status badges with colors"""
        status_colors = {
            "running": Colors.SUCCESS,
            "active": Colors.SUCCESS,
            "available": Colors.SUCCESS,
            "stopped": Colors.TEXT_MUTED,
            "pending": Colors.WARNING,
            "in-use": Colors.INFO,
            "error": Colors.DANGER,
            "terminated": Colors.DANGER,
        }
        
        color = status_colors.get(status.lower(), Colors.TEXT_MUTED)
        
        return f"""
            QLabel {{
                background: {color}22;
                color: {color};
                border: 1px solid {color}44;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
            }}
        """
    
    @staticmethod
    def empty_state():
        """Empty state container"""
        return f"""
            QWidget {{
                background: transparent;
            }}
            QLabel {{
                color: {Colors.TEXT_MUTED};
                font-size: {Fonts.BODY};
                font-family: {Fonts.PRIMARY};
            }}
        """


# ============================================
# BRANDING
# ============================================

class Branding:
    """Branding constants"""
    
    APP_NAME = "CloudSim"
    TAGLINE = "A Local Cloud Simulation Platform for Learning & Practice"
    VERSION = "v1.0"
    COPYRIGHT = "© 2026 CloudSim"
    DEVELOPER = "Developed by Leslie Fernando"
    LICENSE = "Educational Use Only"
    
    @staticmethod
    def footer():
        return f"{Branding.COPYRIGHT} | {Branding.DEVELOPER} | {Branding.LICENSE}"


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_status_badge(status: str, parent=None):
    """Create a styled status badge label"""
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import Qt
    
    label = QLabel(status.upper(), parent)
    label.setStyleSheet(Styles.status_badge(status))
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return label


def create_empty_state(title: str, message: str, icon: str = "📭", parent=None):
    """Create an empty state widget with icon and message"""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PySide6.QtCore import Qt
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    layout.setSpacing(int(Spacing.MD.replace("px", "")))
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Icon
    icon_label = QLabel(icon)
    icon_label.setStyleSheet(f"font-size: 64px; background: transparent;")
    icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(icon_label)
    
    # Title
    title_label = QLabel(title)
    title_label.setStyleSheet(f"""
        font-size: {Fonts.SUBTITLE};
        font-weight: {Fonts.SEMIBOLD};
        color: {Colors.TEXT_PRIMARY};
        background: transparent;
    """)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title_label)
    
    # Message
    msg_label = QLabel(message)
    msg_label.setStyleSheet(f"""
        font-size: {Fonts.BODY};
        color: {Colors.TEXT_MUTED};
        background: transparent;
    """)
    msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    msg_label.setWordWrap(True)
    layout.addWidget(msg_label)
    
    widget.setStyleSheet(Styles.empty_state())
    return widget
