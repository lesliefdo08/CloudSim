#!/usr/bin/env python3
"""
CloudSim Desktop - Premium Modern Cloud Console
Stunning, beautiful, professional
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window_premium import PremiumMainWindow

# Windows-specific: Set AppUserModelID for taskbar icon
if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID('CloudSim.Desktop.Premium.v1.0')
    except:
        pass


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


class CloudSimApp(PremiumMainWindow):
    """Premium modern cloud console application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudSim Premium - Cloud Simulation Platform")
        self.setMinimumSize(1400, 900)
        
        # Set window icon
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))


def main():
    """Initialize and run the premium CloudSim application"""
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("CloudSim Premium")
    app.setOrganizationName("CloudSim")
    
    # Set application icon (for taskbar grouping)
    icon_path = get_resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show the premium app
    window = CloudSimApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
