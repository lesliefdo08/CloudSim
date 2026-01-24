"""
Realism Utilities - Helper functions for adding realistic UI elements
"""

import random
import string
from PySide6.QtWidgets import QApplication


def generate_realistic_id(prefix: str = "i", length: int = 17) -> str:
    """
    Generate AWS-style realistic resource ID
    
    Args:
        prefix: Resource type prefix (i=instance, vol=volume, db=database, etc.)
        length: Length of random hex string (default 17 for instances)
    
    Returns:
        Formatted ID like: i-0123456789abcdef
    """
    chars = string.hexdigits[:16]  # 0-9 and a-f
    random_part = ''.join(random.choices(chars, k=length))
    return f"{prefix}-{random_part}"


def copy_to_clipboard(text: str, show_notification: bool = True):
    """
    Copy text to clipboard with optional notification
    
    Args:
        text: Text to copy
        show_notification: Whether to show success notification
    """
    clipboard = QApplication.clipboard()
    clipboard.setText(text)
    
    if show_notification:
        from ui.components.notifications import NotificationManager
        # Truncate long IDs for notification
        display_text = text if len(text) <= 30 else f"{text[:27]}..."
        NotificationManager.show_success("Copied", f"Copied to clipboard: {display_text}")


def get_fake_account_id() -> str:
    """Get consistent fake AWS account ID"""
    return "123456789012"


def get_region_latency(region: str) -> tuple:
    """
    Get realistic latency for a region
    
    Returns:
        tuple: (latency_ms, status_emoji, status_color)
    """
    latencies = {
        "us-east-1": (15, "🟢", "#10b981"),
        "us-west-2": (45, "🟢", "#10b981"),
        "eu-west-1": (120, "🟡", "#f59e0b"),
        "ap-southeast-1": (180, "🟠", "#fb923c"),
    }
    return latencies.get(region, (25, "🟢", "#10b981"))
