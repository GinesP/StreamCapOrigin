"""
Qt Recording Card component for StreamCap.

A premium-looking card that displays information about a stream recording,
with status indicators, badges, and interactive controls on hover.
"""

import asyncio
import os
from datetime import datetime

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, Signal, QRect, Property
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QBrush, QColor, QPen, QImage
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QSizePolicy,
    QSpacerItem
)

from app.utils.logger import logger
from app.models.recording.recording_status_model import RecordingStatus, CardStateType


class AvatarWidget(QLabel):
    """Circular avatar image widget."""
    def __init__(self, size=44, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.size = size
        self.pixmap_img = None
        self._placeholder_text = "?"
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Rounded to size/2
        self.setStyleSheet(f"background-color: #4a4a6a; border-radius: {size//2}px; color: white; border: 1px solid #5a5a7a;")
        self.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self.setText(self._placeholder_text)

    def set_avatar(self, pixmap: QPixmap):
        self.pixmap_img = pixmap
        self.setText("")
        self.update()

    def set_placeholder(self, char: str):
        self.pixmap_img = None
        self._placeholder_text = char
        self.setText(char)
        self.update()

    def paintEvent(self, event):
        if not self.pixmap_img:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create circle path
        path = QPainter.Path()
        path.addEllipse(0, 0, self.size, self.size)
        painter.setClipPath(path)
        
        # Scale and draw pixmap
        scaled = self.pixmap_img.scaled(
            self.size, self.size, 
            Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
            Qt.TransformationMode.SmoothTransformation
        )
        # Center the scaled image
        x = (self.size - scaled.width()) // 2
        y = (self.size - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)


class BadgeWidget(QFrame):
    """Small badge with text and background color."""
    def __init__(self, text, bgcolor, tooltip="", parent=None):
        super().__init__(parent)
        self.setToolTip(tooltip)
        self.setFixedHeight(26)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        
        self.label = QLabel(text)
        self.label.setStyleSheet(f"color: white; font-size: 11px; font-weight: bold; background: transparent;")
        layout.addWidget(self.label)
        
        self.setStyleSheet(f"background-color: {bgcolor}; border-radius: 6px; border: none;")


class QtRecordingCard(QFrame):
    """
    Highly interactive recording card.
    
    Features:
    - Status color indicator (left border)
    - Async avatar loading
    - Badges (Queue, Likelihood, Priority)
    - Hover effects for action buttons
    """
    
    # Define colors matching the original app design
    STATUS_COLORS = {
        CardStateType.RECORDING: "#2ECC71", # Green
        CardStateType.ERROR: "#F39C12",     # Orange
        CardStateType.LIVE: "#E74C3C",      # Red
        CardStateType.OFFLINE: "#95A5A6",   # Grey
        CardStateType.STOPPED: "#34495E",   # Dark Blue/Grey
        CardStateType.CHECKING: "#9B59B6",  # Purple
    }

    def __init__(self, recording, app_context, parent=None):
        super().__init__(parent)
        self.recording = recording
        self.app = app_context
        self._setup_ui()
        self.update_content()
        self._set_initial_state()

    def set_view_mode(self, mode):
        """Toggle between grid and list layouts."""
        self._view_mode = mode
        if mode == "list":
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            self.setFixedHeight(80) # Slimmer in list mode
            self.opacity_effect.setOpacity(1.0) # Always visible
            self.dates_label.hide() # Save space horizontally
        else:
            self.setFixedSize(320, 160)
            self.opacity_effect.setOpacity(0.0)
            self.dates_label.show()

    def _set_initial_state(self):
        # Setup shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        self._view_mode = "grid"

    def _setup_ui(self):
        self.setObjectName(f"card_{self.recording.rec_id}")
        self.setProperty("class", "card")
        self.setFixedSize(320, 160)
        
        # Main Layout (Horizontal) to include the status bar on the left
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # 1. Status Bar (Color Indicator)
        self.status_bar = QFrame()
        self.status_bar.setFixedWidth(4)
        self.status_bar.setObjectName("statusLine")
        outer_layout.addWidget(self.status_bar)
        
        # 2. Card Content Area
        content_widget = QWidget()
        outer_layout.addWidget(content_widget)
        
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(15, 12, 12, 12)
        layout.setSpacing(8)
        
        # --- Top Row: Avatar + Info + Badges ---
        top_row = QHBoxLayout()
        top_row.setSpacing(12)
        
        self.avatar = AvatarWidget(44)
        top_row.addWidget(self.avatar)
        
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-weight: 700; font-size: 14px;")
        self.title_label.setWordWrap(False)
        info_col.addWidget(self.title_label)
        
        status_row = QHBoxLayout()
        status_row.setSpacing(8)
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 11px; font-weight: 500;")
        status_row.addWidget(self.status_label)
        
        self.duration_label = QLabel()
        self.duration_label.setProperty("class", "muted")
        status_row.addWidget(self.duration_label)
        status_row.addStretch()
        info_col.addLayout(status_row)
        
        top_row.addLayout(info_col)
        
        # Badges (Top Right)
        self.badge_layout = QHBoxLayout()
        self.badge_layout.setSpacing(4)
        top_row.addLayout(self.badge_layout)
        
        layout.addLayout(top_row)
        
        # --- Middle Area: Dates ---
        self.dates_label = QLabel()
        self.dates_label.setProperty("class", "muted")
        self.dates_label.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.dates_label)
        
        layout.addStretch()
        
        # --- Bottom Area: Actions (Fade in on hover) ---
        self.action_toolbar = QWidget()
        self.action_toolbar.setStyleSheet("background: transparent;")
        actions_layout = QHBoxLayout(self.action_toolbar)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(2)
        
        # Create action buttons
        self.btns = {}
        action_defs = [
            ("folder", "📁", "Open Folder"),
            ("play", "▶️", "Start/Stop"),
            ("info", "ℹ️", "Info"),
            ("preview", "🎞️", "Preview"),
            ("edit", "⚙️", "Edit"),
            ("delete", "🗑️", "Delete")
        ]
        
        for name, icon, tip in action_defs:
            btn = QPushButton(icon)
            btn.setProperty("class", "icon")
            btn.setFixedSize(30, 30)
            btn.setToolTip(tip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Placeholder click
            btn.clicked.connect(lambda checked=False, n=name: self._on_action_triggered(n))
            actions_layout.addWidget(btn)
            self.btns[name] = btn
            
        actions_layout.addStretch()
        layout.addWidget(self.action_toolbar)
        
        # Initial state: action toolbar semi-transparent
        self.action_toolbar.setWindowOpacity(0.0)
        # Use a simpler way to hide if opacity doesn't work on child widgets
        # We can use QGraphicsOpacityEffect for the toolbar
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        self.opacity_effect = QGraphicsOpacityEffect(self.action_toolbar)
        self.opacity_effect.setOpacity(0.0)
        self.action_toolbar.setGraphicsEffect(self.opacity_effect)

    def update_content(self):
        """Update all visual elements from recording data."""
        rec = self.recording
        
        # Title
        title = rec.streamer_name
        if rec.status_info == RecordingStatus.RECORDING and getattr(rec, "live_title", None):
            title = f"{rec.streamer_name} - {rec.live_title}"
        self.title_label.setText(title)
        
        # Status & Color
        from app.ui.components.state.recording_card_state import RecordingCardState
        state = RecordingCardState.get_card_state(rec)
        color = self.STATUS_COLORS.get(state, "#34495E")
        
        self.status_bar.setStyleSheet(f"background-color: {color}; border-top-left-radius: 10px; border-bottom-left-radius: 10px;")
        
        status_text = rec.status_info if rec.status_info else "Idle"
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600;")
        
        # Duration
        duration = self.app.record_manager.get_duration(rec)
        if (rec.is_recording or rec.is_live) and duration != "00:00:00":
            self.duration_label.setText(f"• {duration}")
            self.duration_label.show()
        else:
            self.duration_label.hide()
            
        # Dates
        added_at = getattr(rec, "added_at", "")
        if added_at:
            # We would use the _format_date helper from App Manager usually
            # Using simple text for now
            self.dates_label.setText(f"Added: {added_at}")
        
        # Badges
        self._update_badges(rec)
        
        # Avatar placeholder
        if rec.streamer_name:
            self.avatar.set_placeholder(rec.streamer_name[0].upper())
        
        # Async load of avatar
        # self.app.event_bus.run_task(self._load_avatar, rec.avatar_url)

    def _update_badges(self, rec):
        # Clear old badges
        while self.badge_layout.count():
            item = self.badge_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Queue Badge
        interval = rec.loop_time_seconds
        if interval <= 60:
            q_text, q_color = "F", "#66bb6a"
        elif interval <= 180:
            q_text, q_color = "M", "#ffa726"
        else:
            q_text, q_color = "S", "#ef5350"
        
        self.badge_layout.addWidget(BadgeWidget(q_text, q_color, "Queue Speed"))
        
        # Likelihood Badge (reusing HistoryManager logic if available)
        try:
            from app.core.recording.history_manager import HistoryManager
            score = HistoryManager.get_likelihood_score(rec)
            if score > 0:
                l_text = "High" if score >= 0.8 else "Normal"
                l_color = "#66bb6a" if score >= 0.8 else "#4fc3f7"
                self.badge_layout.addWidget(BadgeWidget(l_text, l_color, "Likelihood"))
        except:
            pass

    def enterEvent(self, event):
        """Start hover animation (fade in actions) only in grid mode."""
        self._is_hovered = True
        if self._view_mode == "grid":
            self._animate_actions(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Start hover animation (fade out actions) only in grid mode."""
        self._is_hovered = False
        if self._view_mode == "grid":
            self._animate_actions(0.0)
        super().leaveEvent(event)

    def _animate_actions(self, target_opacity):
        if not hasattr(self, "anim") or self.anim.state() != QPropertyAnimation.State.Running:
            self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.anim.setDuration(200)
            self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(target_opacity)
        self.anim.start()

    def _on_action_triggered(self, name):
        """Handle control clicks by emitting events or calling app methods."""
        logger.info(f"Card {self.recording.rec_id}: Button {name} clicked")
        rec = self.recording
        
        if name == "folder":
            path = self.app.settings.get_video_save_path()
            if os.path.exists(path):
                import subprocess
                if os.name == "nt":
                    os.startfile(path)
                else:
                    subprocess.run(["open", path] if sys.platform == "darwin" else ["xdg-open", path])
        
        elif name == "play":
            # Toggle recording logic (simplified from RecordingCardManager)
            if rec.is_recording:
                self.app.event_bus.run_task(self.app.record_manager.stop_recording, rec, manually_stopped=True)
            else:
                self.app.event_bus.run_task(self.app.record_manager.start_monitor_recording, rec)
        
        elif name == "delete":
            # Just remove from monitoring for now
            self.app.event_bus.run_task(self.app.record_manager.remove_recording, rec)
            self.app.event_bus.publish("delete", rec) # Notify view to remove card
            
        elif name == "info":
            # Show info dialog (placeholder)
            logger.info(f"Info clicked for {rec.streamer_name}")
            
        elif name == "edit":
            # Edit config (placeholder)
            logger.info(f"Edit clicked for {rec.streamer_name}")
