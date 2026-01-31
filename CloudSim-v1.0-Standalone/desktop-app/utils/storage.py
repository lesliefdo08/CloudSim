"""
Storage - Simple JSON-based storage for CloudSim data
"""

import json
import os
from pathlib import Path
from typing import Any, List
from utils.data_path import get_data_dir


class Storage:
    """Simple JSON file storage"""
    
    def __init__(self, filename: str):
        """
        Initialize storage with filename
        
        Args:
            filename: Name of the JSON file to store data
        """
        # Get writable data directory (handles PyInstaller)
        self.data_dir = get_data_dir()
        self.filepath = self.data_dir / filename
    
    def load(self) -> List[dict]:
        """
        Load data from storage
        
        Returns:
            List of dictionaries
        """
        if not self.filepath.exists():
            return []
        
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    
    def save(self, data: List[dict]):
        """
        Save data to storage
        
        Args:
            data: List of dictionaries to save
        """
        try:
            with open(self.filepath, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving to {self.filepath}: {e}")
    
    def clear(self):
        """Clear all data from storage"""
        if self.filepath.exists():
            self.filepath.unlink()
