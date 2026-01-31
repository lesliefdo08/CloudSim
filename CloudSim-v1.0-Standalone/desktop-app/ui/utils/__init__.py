"""
UI Utilities Package
"""

# Import realism utilities
from .realism import (
    generate_realistic_id,
    copy_to_clipboard,
    get_fake_account_id,
    get_region_latency
)

# Import dialog utilities
from .dialogs import (
    show_permission_denied,
    show_error_dialog,
    show_success_dialog,
    show_notification_banner
)

__all__ = [
    'generate_realistic_id',
    'copy_to_clipboard',
    'get_fake_account_id',
    'get_region_latency',
    'show_permission_denied',
    'show_error_dialog',
    'show_success_dialog',
    'show_notification_banner'
]
