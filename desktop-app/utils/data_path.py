"""
Data Path - Get writable data directory for CloudSim
"""

import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    """
    Get the data directory path that's writable
    
    When running as PyInstaller executable, creates data folder next to the .exe
    When running from source, uses ./data
    
    Returns:
        Path to writable data directory
    """
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # Use the directory where the executable is located
        exe_dir = Path(sys.executable).parent
        data_dir = exe_dir / "data"
    else:
        # Running from source code
        data_dir = Path("data")
    
    # Create directory if it doesn't exist (with proper error handling)
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        # If we can't write here, use user's AppData folder
        app_data = Path(os.getenv('APPDATA', os.path.expanduser('~'))) / "CloudSim" / "data"
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    
    return data_dir
