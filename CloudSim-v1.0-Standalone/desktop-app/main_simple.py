"""
CloudSim Desktop Application - Cloud Simulation Platform
Professional cloud infrastructure simulator with realistic interface
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont

# Premium main window with API integration
from ui.main_window_api import APIMainWindow


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        base_path = Path(__file__).parent
    return base_path / relative_path


def main():
    """Launch the CloudSim desktop application"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("CloudSim - Cloud Simulator")
    app.setOrganizationName("CloudSim")
    
    # Set application style
    app.setStyle("Fusion")
    
    # Set default font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Set window icon if available
    icon_path = get_resource_path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    else:
        # Try PNG as fallback
        icon_path = get_resource_path("logo.png")
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show main window
    window = APIMainWindow()
    window.show()
    
    print("=" * 70)
    print("CloudSim Desktop - Cloud Simulation Platform")
    print("=" * 70)
    print("Backend: http://localhost:8000")
    print("Status: Connecting to backend server...")
    print("=" * 70)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
