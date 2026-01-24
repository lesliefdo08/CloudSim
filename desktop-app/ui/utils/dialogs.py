"""
UI Dialog Utilities - Common functions for handling dialogs and notifications
"""

from PySide6.QtWidgets import QMessageBox, QWidget
from typing import Optional
from ui.design_system import Colors


def show_notification_banner(message: str, notification_type: str = "info", duration: int = 3000):
    """
    Show a toast notification banner
    
    Args:
        message: Notification message
        notification_type: Type of notification (success, error, warning, info)
        duration: Duration in milliseconds (0 for persistent)
    """
    from ui.components.notifications import NotificationManager
    
    if notification_type == "success":
        NotificationManager.show_success(message, duration)
    elif notification_type == "error":
        NotificationManager.show_error(message, duration)
    elif notification_type == "warning":
        NotificationManager.show_warning(message, duration)
    else:
        NotificationManager.show_info(message, duration)


def show_permission_denied(parent: Optional[QWidget], error: PermissionError, action_description: str = "this action"):
    """
    Show a user-friendly permission denied notification
    
    Args:
        parent: Parent widget for the dialog
        error: The PermissionError exception
        action_description: Human-readable description of what was attempted
    """
    # Show banner notification
    show_notification_banner(
        f"Access Denied: You don't have permission to {action_description}",
        "error",
        5000
    )
    
    # Also show dialog for detailed info if needed
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle("Access Denied")
    msg.setText(f"You don't have permission to perform {action_description}.")
    msg.setInformativeText(str(error))
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #1e293b;
            color: #e2e8f0;
        }
        QLabel {
            color: #e2e8f0;
        }
        QPushButton {
            background-color: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #2563eb;
        }
    """)
    msg.exec()


def show_error_dialog(parent: Optional[QWidget], title: str, message: str, details: str = ""):
    """
    Show a generic error notification and dialog
    
    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Main error message
        details: Optional detailed error information
    """
    # Show banner notification
    show_notification_banner(message, "error", 5000)
    
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    if details:
        msg.setInformativeText(details)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #1e293b;
            color: #e2e8f0;
        }
        QLabel {
            color: #e2e8f0;
        }
        QPushButton {
            background-color: #ef4444;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
        }
        QPushButton:hover {
            background-color: #dc2626;
        }
    """)
    msg.exec()


def show_success_dialog(parent: Optional[QWidget], title: str, message: str):
    """
    Show a success notification banner
    
    Args:
        parent: Parent widget for the dialog
        title: Dialog title
        message: Success message
    """
    # Show banner notification (no dialog needed for success)
    show_notification_banner(message, "success", 3000)
