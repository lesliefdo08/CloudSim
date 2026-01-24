#!/usr/bin/env python3
"""
CloudSim Desktop - Main Entry Point
A student-focused local cloud computing lab platform
(Authentication temporarily disabled - direct dashboard launch)
"""

import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow

# Windows-specific: Set AppUserModelID for taskbar icon
if sys.platform == 'win32':
    try:
        from ctypes import windll
        # Set AppUserModelID so Windows shows our icon in taskbar
        windll.shell32.SetCurrentProcessExplicitAppUserModelID('CloudSim.Desktop.v1.0')
    except:
        pass


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Running in normal Python environment
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)


class CloudSimApp(MainWindow):
    """Main application - launches directly to dashboard"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudSim Console")
        self.setMinimumSize(1400, 900)
        
        # Set window icon (taskbar icon) - works with PyInstaller
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))


def main():
    """Initialize and run the CloudSim Desktop application"""
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("CloudSim Console")
    app.setOrganizationName("CloudSim")
    
    # Set application icon (for taskbar grouping) - works with PyInstaller
    icon_path = get_resource_path("icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create and show the app controller
    window = CloudSimApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
