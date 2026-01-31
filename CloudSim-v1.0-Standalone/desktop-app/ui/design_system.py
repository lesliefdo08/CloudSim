"""
CloudSim Design System - AWS EC2 Console Style
Boring, professional, and realistic AWS-style design
"""

# ============================================
# COLOR PALETTE - AWS Console Style
# ============================================

class Colors:
    """Modern, vibrant cloud console theme with depth and visual appeal"""
    
    # Primary Brand Colors - Vibrant Blue/Purple
    PRIMARY = "#5B7CFF"          # Vibrant blue
    PRIMARY_HOVER = "#4A6BE8"    # Darker blue
    PRIMARY_LIGHT = "#E8EEFF"    # Very light blue
    SECONDARY = "#7C3AED"        # Purple accent
    ACCENT = "#FF6B9D"           # Pink accent
    
    # Backgrounds - Layered depth
    BG_PRIMARY = "#FAFBFF"       # Off-white with blue tint
    BG_SECONDARY = "#F5F7FF"     # Light blue-gray
    BG_TERTIARY = "#FFFFFF"      # Pure white for cards
    BG_HOVER = "#EEF2FF"         # Light purple on hover
    BG_GRADIENT_START = "#667EEA" # Gradient start
    BG_GRADIENT_END = "#764BA2"   # Gradient end
    
    # Borders - Subtle and modern
    BORDER = "#E5E7EB"           # Light gray border
    BORDER_LIGHT = "#F3F4F6"     # Very light border
    BORDER_DARK = "#D1D5DB"      # Darker border
    BORDER_ACCENT = "#C7D2FE"    # Purple-tinted border
    
    # Text Colors - High contrast
    TEXT_PRIMARY = "#1F2937"     # Dark gray (not black)
    TEXT_SECONDARY = "#6B7280"   # Medium gray
    TEXT_TERTIARY = "#9CA3AF"    # Light gray
    TEXT_DISABLED = "#D1D5DB"    # Very light gray
    TEXT_LINK = "#5B7CFF"        # Primary blue
    TEXT_LINK_HOVER = "#4A6BE8"  # Darker blue
    TEXT_ON_PRIMARY = "#FFFFFF"  # White on colored backgrounds
    
    # State colors - Vibrant and clear
    STATE_RUNNING = "#10B981"    # Bright green
    STATE_STOPPED = "#EF4444"    # Bright red
    STATE_PENDING = "#F59E0B"    # Bright orange
    STATE_TERMINATED = "#9CA3AF" # Gray
    
    # Status Colors - Modern palette
    SUCCESS = "#10B981"          # Emerald green
    DANGER = "#EF4444"           # Red
    WARNING = "#F59E0B"          # Amber
    INFO = "#3B82F6"             # Blue
    
    # Table
    TABLE_HEADER = "#fafafa"
    TABLE_ROW_HOVER = "#f9f9f9"
    TABLE_BORDER = "#e7e7e7"
    TABLE_SELECTED = "#f0f7ff"
    
    # Legacy aliases (for compatibility)
    BACKGROUND = "#ffffff"
    SURFACE = "#ffffff"
    SURFACE_HOVER = "#f9f9f9"
    CARD = "#ffffff"
    CARD_HOVER = "#f9f9f9"
    ACCENT = "#ec7211"
    ACCENT_HOVER = "#da6910"
    
    # Service Colors (minimal)
    COMPUTE = "#0073bb"
    STORAGE = "#037f0c"
    DATABASE = "#8b008b"
    SERVERLESS = "#ff9900"
    VOLUMES = "#0073bb"


# ============================================
# TYPOGRAPHY - AWS Style
# ============================================

class Fonts:
    """AWS Console typography - dense and small"""
    
    # Font Families
    PRIMARY = "'Amazon Ember', 'Helvetica Neue', Arial, sans-serif"
    MONOSPACE = "'Courier New', 'Consolas', monospace"
    
    # Font Sizes (smaller, denser)
    TITLE = "18px"       # Page titles
    HEADING = "16px"     # Section headers
    BODY = "14px"        # Normal text
    SMALL = "12px"       # Table text, labels
    TINY = "11px"        # Helper text
    
    # Legacy aliases
    HERO = "18px"
    SUBTITLE = "16px"
    METRIC_HUGE = "24px"
    METRIC_LARGE = "20px"
    METRIC_LABEL = "12px"
    
    # Font Weights
    REGULAR = "400"
    MEDIUM = "500"
    SEMIBOLD = "600"
    BOLD = "700"
    
    # Legacy aliases
    LIGHT = "400"
    EXTRABOLD = "700"
    HEAVY = "700"


# ============================================
# SPACING - Dense AWS Style
# ============================================

class Spacing:
    """Consistent spacing system - denser than before"""
    
    XXS = "2px"
    XS = "4px"
    SM = "8px"
    MD = "12px"    # Default padding (reduced from 16px)
    LG = "16px"
    XL = "24px"
    XXL = "32px"
    XXXL = "48px"


# ============================================
# ANIMATIONS - Minimal
# ============================================

class Animations:
    """Minimal animations for AWS style"""
    
    FAST = "100ms"
    NORMAL = "150ms"
    SLOW = "200ms"
    
    EASING = "ease"


# ============================================
# COMPONENT STYLES - AWS Console Style
# ============================================

class Styles:
    """Boring, professional AWS-style components"""
    
    @staticmethod
    def primary_button():
        """Modern gradient primary button"""
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.PRIMARY}, stop:1 {Colors.PRIMARY_HOVER});
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.PRIMARY_HOVER}, stop:1 {Colors.PRIMARY});
            }}
            QPushButton:pressed {{
                background: {Colors.PRIMARY_HOVER};
                padding-top: 12px;
                padding-bottom: 8px;
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def secondary_button():
        """Modern secondary button with subtle shadow"""
        return f"""
            QPushButton {{
                background: white;
                color: {Colors.TEXT_PRIMARY};
                border: 2px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: {Colors.BG_HOVER};
                border-color: {Colors.PRIMARY};
                color: {Colors.PRIMARY};
            }}
            QPushButton:pressed {{
                background: {Colors.PRIMARY_LIGHT};
                padding-top: 12px;
                padding-bottom: 8px
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: {Colors.BG_TERTIARY};
            }}
            QPushButton:pressed {{
                background: {Colors.BG_SECONDARY};
            }}
            QPushButton:disabled {{
                color: {Colors.TEXT_DISABLED};
                border-color: {Colors.BORDER};
            }}
        """
    
    @staticmethod
    def success_button():
        """Green success button (minimal use)"""
        return f"""
            QPushButton {{
                background: {Colors.SUCCESS};
                color: white;
                border: none;
                border-radius: 2px;
                padding: 6px 12px;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: #026609;
            }}
            QPushButton:pressed {{
                background: #014d07;
            }}
        """
    
    @staticmethod
    def danger_button():
        """Red danger button"""
        return f"""
            QPushButton {{
                background: {Colors.DANGER};
                color: white;
                border: none;
                border-radius: 2px;
                padding: 6px 12px;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QPushButton:hover {{
                background: #b02a0f;
            }}
            QPushButton:pressed {{
                background: #8f220c;
            }}
            QPushButton:disabled {{
                background: {Colors.BORDER};
                color: {Colors.TEXT_DISABLED};
            }}
        """
    
    @staticmethod
    def card():
        """Simple white card with border"""
        return f"""
            QFrame {{
                background: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 20px;
            }}
        """
    
    @staticmethod
    def table():
        """Modern table with rounded corners and shadows"""
        return f"""
            QTableWidget {{")
                background: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
                gridline-color: {Colors.BORDER_LIGHT};
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.SMALL};
                font-family: {Fonts.PRIMARY};
            }}
            QTableWidget::item {{
                padding: 12px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {Colors.PRIMARY_LIGHT};
                color: {Colors.PRIMARY};
            }}
            QTableWidget::item:hover {{
                background: {Colors.BG_HOVER};
            }}
            QHeaderView::section {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.BG_GRADIENT_START}, stop:1 {Colors.BG_GRADIENT_END});
                color: white;
                padding: 12px;
                border: none;
                font-weight: {Fonts.SEMIBOLD};
                font-family: {Fonts.PRIMARY};
            }}
            QTableWidget::item:hover {{
                background: {Colors.TABLE_ROW_HOVER};
            }}
            QHeaderView::section {{
                background: {Colors.TABLE_HEADER};
                color: {Colors.TEXT_PRIMARY};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {Colors.BORDER};
                font-weight: {Fonts.SEMIBOLD};
                font-size: {Fonts.SMALL};
            }}
        """
    
    @staticmethod
    def input():
        """AWS-style input fields"""
        return f"""
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background: white;
                border: 1px solid {Colors.BORDER_DARK};
                border-radius: 2px;
                padding: 6px 8px;
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                font-family: {Fonts.PRIMARY};
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {Colors.INFO};
            }}
            QLineEdit:hover, QTextEdit:hover, QSpinBox:hover, QComboBox:hover {{
                border-color: {Colors.TEXT_SECONDARY};
            }}
            QLineEdit:disabled, QTextEdit:disabled, QSpinBox:disabled, QComboBox:disabled {{
                background: {Colors.BG_TERTIARY};
                color: {Colors.TEXT_DISABLED};
            }}
            QComboBox::drop-down {{
                border: none;
                border-left: 1px solid {Colors.BORDER};
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: white;
                border: 1px solid {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
                selection-background-color: {Colors.TABLE_SELECTED};
            }}
        """
    
    @staticmethod
    def dialog():
        """Simple dialog styling"""
        return f"""
            QDialog {{
                background: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 2px;
            }}
            QLabel {{
                color: {Colors.TEXT_PRIMARY};
                font-size: {Fonts.BODY};
                font-family: {Fonts.PRIMARY};
            }}
        """
    
    @staticmethod
    def status_badge(status: str):
        """Minimal status text (no badges)"""
        status_colors = {
            "running": Colors.STATE_RUNNING,
            "active": Colors.STATE_RUNNING,
            "available": Colors.STATE_RUNNING,
            "stopped": Colors.STATE_STOPPED,
            "pending": Colors.STATE_PENDING,
            "in-use": Colors.INFO,
            "error": Colors.DANGER,
            "terminated": Colors.STATE_TERMINATED,
        }
        
        color = status_colors.get(status.lower(), Colors.TEXT_PRIMARY)
        
        return f"""
            QLabel {{
                color: {color};
                background: transparent;
                border: none;
                font-size: {Fonts.SMALL};
                font-weight: {Fonts.REGULAR};
            }}
        """
    
    @staticmethod
    def empty_state():
        """Simple empty state"""
        return f"""
            QWidget {{
                background: white;
            }}
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
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
    """Create a simple status text label (no fancy badges)"""
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import Qt
    
    label = QLabel(status.lower(), parent)
    label.setStyleSheet(Styles.status_badge(status))
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    return label


def create_empty_state(title: str, message: str, icon: str = "", parent=None):
    """Create a simple empty state widget"""
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
    from PySide6.QtCore import Qt
    
    widget = QWidget(parent)
    layout = QVBoxLayout(widget)
    layout.setSpacing(int(Spacing.MD.replace("px", "")))
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    # Title
    title_label = QLabel(title)
    title_label.setStyleSheet(f"""
        font-size: {Fonts.HEADING};
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
        color: {Colors.TEXT_SECONDARY};
        background: transparent;
    """)
    msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    msg_label.setWordWrap(True)
    layout.addWidget(msg_label)
    
    widget.setStyleSheet(Styles.empty_state())
    return widget
