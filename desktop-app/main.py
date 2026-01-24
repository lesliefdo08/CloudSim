#!/usr/bin/env python3
"""
CloudSim Desktop - Main Entry Point
A student-focused local cloud computing lab platform
(Authentication temporarily disabled - direct dashboard launch)
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from ui.main_window import MainWindow


class CloudSimApp(MainWindow):
    """Main application - launches directly to dashboard"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudSim Console")
        self.setMinimumSize(1400, 900)
        
        # Set window icon (taskbar icon)
        icon_path = Path("icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))


def main():
    """Initialize and run the CloudSim Desktop application"""
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("CloudSim Console")
    app.setOrganizationName("CloudSim")
    
    # Set application icon (for taskbar grouping)
    icon_path = Path("icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Create and show the app controller
    window = CloudSimApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
