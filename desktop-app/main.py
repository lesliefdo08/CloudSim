#!/usr/bin/env python3
"""
CloudSim Desktop - Main Entry Point
A student-focused local cloud computing lab platform
(Authentication temporarily disabled - direct dashboard launch)
"""

import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


class CloudSimApp(MainWindow):
    """Main application - launches directly to dashboard"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CloudSim Console")
        self.setMinimumSize(1400, 900)


def main():
    """Initialize and run the CloudSim Desktop application"""
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("CloudSim Console")
    app.setOrganizationName("CloudSim")
    
    # Create and show the app controller
    window = CloudSimApp()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
