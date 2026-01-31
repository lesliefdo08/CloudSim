"""
Bulk Action Bar - Floating action toolbar for multi-selection
Enterprise-grade bulk operations with smart action validation
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QCursor
from ui.design_system import Colors, Fonts, Spacing
from ui.components.tooltips import add_tooltip_to_widget


class BulkActionBar(QWidget):
    """
    Floating action bar that appears at bottom when items are selected
    Provides bulk operations with smart validation and tooltips
    """
    
    # Signals for actions
    action_triggered = Signal(str, list)  # action_name, selected_ids
    selection_cleared = Signal()
    
    def __init__(self, resource_type: str = "instance", parent=None):
        super().__init__(parent)
        self.resource_type = resource_type  # "instance" or "volume"
        self.selected_items = []  # List of {id, status, data} dicts
        self.action_buttons = {}
        
        self._init_ui()
        self._setup_animations()
        self.hide()  # Initially hidden
        
    def _init_ui(self):
        """Create floating bar UI"""
        self.setObjectName("bulkActionBar")
        self.setFixedHeight(72)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 16, 32, 16)
        layout.setSpacing(24)
        
        # Left side: Selection info
        self.selection_label = QLabel()
        self.selection_label.setStyleSheet(f"""
            QLabel {{
                font-size: 15px;
                font-weight: {Fonts.SEMIBOLD};
                color: {Colors.TEXT_PRIMARY};
            }}
        """)
        layout.addWidget(self.selection_label)
        
        # Clear selection button
        clear_btn = QPushButton("✕ Clear")
        clear_btn.setCursor(QCursor(Qt.PointingHandCursor))
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {Colors.TEXT_SECONDARY};
                border: 1px solid {Colors.BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: {Fonts.MEDIUM};
            }}
            QPushButton:hover {{
                background: {Colors.SURFACE_HOVER};
                color: {Colors.TEXT_PRIMARY};
                border-color: {Colors.BORDER_LIGHT};
            }}
        """)
        clear_btn.clicked.connect(self._on_clear_selection)
        layout.addWidget(clear_btn)
        
        layout.addStretch()
        
        # Right side: Action buttons
        self._create_action_buttons(layout)
        
        # Styling for floating effect
        self.setStyleSheet(f"""
            #bulkActionBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {Colors.PRIMARY_LIGHT},
                    stop:1 {Colors.SURFACE});
                border: 1px solid {Colors.ACCENT};
                border-radius: 12px;
            }}
        """)
    
    def _create_action_buttons(self, layout):
        """Create action buttons based on resource type"""
        if self.resource_type == "instance":
            actions = [
                ("start", "▶ Start", Colors.SUCCESS, "Start selected instances"),
                ("stop", "⏸ Stop", Colors.WARNING, "Stop selected instances"),
                ("restart", "🔄 Restart", Colors.INFO, "Restart selected instances"),
                ("terminate", "🗑 Terminate", Colors.DANGER, "Permanently delete selected instances"),
            ]
        else:  # volume
            actions = [
                ("attach", "📎 Attach", Colors.INFO, "Attach selected volumes"),
                ("detach", "📤 Detach", Colors.WARNING, "Detach selected volumes"),
                ("snapshot", "📸 Snapshot", Colors.ACCENT, "Create snapshots of selected volumes"),
                ("delete", "🗑 Delete", Colors.DANGER, "Delete selected volumes"),
            ]
        
        for action_id, label, color, tooltip in actions:
            btn = QPushButton(label)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setFixedHeight(40)
            btn.setProperty("action_id", action_id)
            
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 0 20px;
                    font-size: 13px;
                    font-weight: {Fonts.SEMIBOLD};
                }}
                QPushButton:hover {{
                    background: {Colors.ACCENT_HOVER};
                }}
                QPushButton:pressed {{
                    background: {Colors.ACCENT};
                }}
                QPushButton:disabled {{
                    background: {Colors.SURFACE};
                    color: {Colors.TEXT_DISABLED};
                    border: 1px solid {Colors.BORDER};
                }}
            """)
            
            btn.clicked.connect(lambda checked, a=action_id: self._on_action_triggered(a))
            add_tooltip_to_widget(btn, tooltip)
            
            self.action_buttons[action_id] = btn
            layout.addWidget(btn)
    
    def update_selection(self, selected_items: list):
        """
        Update selected items and refresh UI
        selected_items: list of dicts with {id, status, name, data}
        """
        self.selected_items = selected_items
        count = len(selected_items)
        
        if count == 0:
            self._hide_with_animation()
            return
        
        # Update label
        item_type = self.resource_type.title()
        plural = "s" if count > 1 else ""
        self.selection_label.setText(f"{count} {item_type}{plural} selected")
        
        # Validate and update action buttons
        self._validate_actions()
        
        # Show bar if hidden
        if not self.isVisible():
            self._show_with_animation()
    
    def _validate_actions(self):
        """
        Smart validation: disable actions based on selected item states
        Add tooltips explaining why actions are disabled
        """
        if not self.selected_items:
            return
        
        # Get all states
        states = [item.get('status', '').lower() for item in self.selected_items]
        state_counts = {}
        for state in states:
            state_counts[state] = state_counts.get(state, 0) + 1
        
        if self.resource_type == "instance":
            self._validate_instance_actions(states, state_counts)
        else:
            self._validate_volume_actions(states, state_counts)
    
    def _validate_instance_actions(self, states: list, state_counts: dict):
        """Validate instance-specific actions"""
        all_running = all(s == 'running' for s in states)
        all_stopped = all(s == 'stopped' for s in states)
        has_running = 'running' in states
        has_stopped = 'stopped' in states
        has_mixed = len(state_counts) > 1
        
        # Start button
        start_btn = self.action_buttons.get('start')
        if start_btn:
            if all_running:
                start_btn.setEnabled(False)
                add_tooltip_to_widget(start_btn, "❌ All selected instances are already running")
            elif has_running and has_stopped:
                start_btn.setEnabled(True)
                add_tooltip_to_widget(start_btn, 
                    f"⚠ Will start {state_counts.get('stopped', 0)} stopped instance(s)\n"
                    f"({state_counts.get('running', 0)} already running)")
            else:
                start_btn.setEnabled(True)
                add_tooltip_to_widget(start_btn, f"Start {len(states)} selected instance(s)")
        
        # Stop button
        stop_btn = self.action_buttons.get('stop')
        if stop_btn:
            if all_stopped:
                stop_btn.setEnabled(False)
                add_tooltip_to_widget(stop_btn, "❌ All selected instances are already stopped")
            elif has_running and has_stopped:
                stop_btn.setEnabled(True)
                add_tooltip_to_widget(stop_btn,
                    f"⚠ Will stop {state_counts.get('running', 0)} running instance(s)\n"
                    f"({state_counts.get('stopped', 0)} already stopped)")
            else:
                stop_btn.setEnabled(True)
                add_tooltip_to_widget(stop_btn, f"Stop {len(states)} selected instance(s)")
        
        # Restart button
        restart_btn = self.action_buttons.get('restart')
        if restart_btn:
            if all_stopped:
                restart_btn.setEnabled(False)
                add_tooltip_to_widget(restart_btn, "❌ Cannot restart stopped instances\nUse Start instead")
            else:
                restart_btn.setEnabled(True)
                tooltip = f"Restart {state_counts.get('running', 0)} running instance(s)"
                if has_stopped:
                    tooltip += f"\n⚠ {state_counts.get('stopped', 0)} stopped instance(s) will be skipped"
                add_tooltip_to_widget(restart_btn, tooltip)
        
        # Terminate button (always enabled)
        terminate_btn = self.action_buttons.get('terminate')
        if terminate_btn:
            terminate_btn.setEnabled(True)
            add_tooltip_to_widget(terminate_btn, 
                f"⚠ Permanently delete {len(states)} instance(s)\nThis action cannot be undone!")
    
    def _validate_volume_actions(self, states: list, state_counts: dict):
        """Validate volume-specific actions"""
        all_available = all(s == 'available' for s in states)
        all_in_use = all(s == 'in-use' for s in states)
        has_available = 'available' in states
        has_in_use = 'in-use' in states
        
        # Attach button
        attach_btn = self.action_buttons.get('attach')
        if attach_btn:
            if all_in_use:
                attach_btn.setEnabled(False)
                add_tooltip_to_widget(attach_btn, "❌ All selected volumes are already attached")
            elif has_available:
                attach_btn.setEnabled(True)
                tooltip = f"Attach {state_counts.get('available', 0)} available volume(s)"
                if has_in_use:
                    tooltip += f"\n⚠ {state_counts.get('in-use', 0)} already attached"
                add_tooltip_to_widget(attach_btn, tooltip)
            else:
                attach_btn.setEnabled(False)
                add_tooltip_to_widget(attach_btn, "❌ No available volumes selected")
        
        # Detach button
        detach_btn = self.action_buttons.get('detach')
        if detach_btn:
            if all_available:
                detach_btn.setEnabled(False)
                add_tooltip_to_widget(detach_btn, "❌ All selected volumes are already detached")
            elif has_in_use:
                detach_btn.setEnabled(True)
                tooltip = f"Detach {state_counts.get('in-use', 0)} attached volume(s)"
                if has_available:
                    tooltip += f"\n⚠ {state_counts.get('available', 0)} already detached"
                add_tooltip_to_widget(detach_btn, tooltip)
            else:
                detach_btn.setEnabled(False)
                add_tooltip_to_widget(detach_btn, "❌ No attached volumes selected")
        
        # Snapshot button (always enabled)
        snapshot_btn = self.action_buttons.get('snapshot')
        if snapshot_btn:
            snapshot_btn.setEnabled(True)
            add_tooltip_to_widget(snapshot_btn, f"Create snapshots of {len(states)} volume(s)")
        
        # Delete button
        delete_btn = self.action_buttons.get('delete')
        if delete_btn:
            if all_in_use:
                delete_btn.setEnabled(False)
                add_tooltip_to_widget(delete_btn, 
                    "❌ Cannot delete attached volumes\nDetach them first")
            elif has_in_use:
                delete_btn.setEnabled(False)
                add_tooltip_to_widget(delete_btn,
                    f"❌ Cannot delete: {state_counts.get('in-use', 0)} volume(s) still attached\n"
                    "Detach all volumes before deleting")
            else:
                delete_btn.setEnabled(True)
                add_tooltip_to_widget(delete_btn,
                    f"⚠ Delete {len(states)} volume(s)\nThis action cannot be undone!")
    
    def _setup_animations(self):
        """Setup slide-up animation for bar appearance"""
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(250)
        self.fade_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def _show_with_animation(self):
        """Animate bar appearance"""
        self.show()
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
    
    def _hide_with_animation(self):
        """Animate bar disappearance"""
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.start()
        
        # Disconnect after hiding to avoid multiple connections
        QTimer.singleShot(300, lambda: self.fade_animation.finished.disconnect())
    
    def _on_action_triggered(self, action_id: str):
        """Handle action button click"""
        if not self.selected_items:
            return
        
        # Get IDs of items that can actually be acted upon
        valid_ids = self._get_valid_ids_for_action(action_id)
        
        if valid_ids:
            self.action_triggered.emit(action_id, valid_ids)
    
    def _get_valid_ids_for_action(self, action_id: str) -> list:
        """Filter items that can actually receive the action"""
        valid_ids = []
        
        for item in self.selected_items:
            status = item.get('status', '').lower()
            item_id = item.get('id')
            
            # Action validation logic
            if action_id == 'start' and status != 'running':
                valid_ids.append(item_id)
            elif action_id == 'stop' and status != 'stopped':
                valid_ids.append(item_id)
            elif action_id == 'restart' and status == 'running':
                valid_ids.append(item_id)
            elif action_id == 'terminate':  # Always valid
                valid_ids.append(item_id)
            elif action_id == 'attach' and status == 'available':
                valid_ids.append(item_id)
            elif action_id == 'detach' and status == 'in-use':
                valid_ids.append(item_id)
            elif action_id in ['snapshot', 'delete']:  # Always valid (with conditions)
                valid_ids.append(item_id)
        
        return valid_ids
    
    def _on_clear_selection(self):
        """Clear selection and hide bar"""
        self.selected_items = []
        self._hide_with_animation()
        self.selection_cleared.emit()
    
    def clear(self):
        """Programmatically clear selection"""
        self._on_clear_selection()
