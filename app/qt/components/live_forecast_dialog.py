"""
Qt Manual Live Forecast Dialog — StreamCap.
Displays on-demand forecast of upcoming live streams.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QScrollArea, QWidget, QFrame, QSizePolicy
)
from PySide6.QtGui import QColor

from app.core.recording.history_manager import HistoryManager
from app.qt.themes.theme import theme_manager

# Platform colors for badges
_PLATFORM_COLORS = {
    "chaturbate": "#FF9800",
    "chaturbate-privates": "#F44336",
    "tiktok": "#000000",
    "default": "#4CAF50"
}

def _get_platform_color(platform: str | None) -> str:
    if not platform:
        return _PLATFORM_COLORS["default"]
    p_lower = platform.lower()
    return _PLATFORM_COLORS.get(p_lower, _PLATFORM_COLORS["default"])

def _get_forecast_time_info(recording) -> tuple[str, str, str]:
    """Return (state, display_text, color_hint) for the forecast time column."""
    from datetime import datetime
    
    now = datetime.now()
    current_hour = now.hour
    day_str = str(now.weekday())
    intervals = recording.historical_intervals or {}
    active_hours = intervals.get(day_str, [])
    
    if not active_hours:
        return ("none", "", "")
    
    sorted_hours = sorted(active_hours)
    first_h = sorted_hours[0]
    last_h = sorted_hours[-1]
    end_h = (last_h + 1) if last_h < 23 else 0
    range_str = f"{first_h:02d}:00‑{end_h:02d}:00"
    
    is_live = recording.is_live
    
    # Currently in the active window
    if current_hour in active_hours:
        if is_live:
            return ("live_range", f"🔴 {range_str}", "#E53935")
        # Not live but within expected window
        minutes_into = (current_hour - first_h) * 60 + now.minute
        if minutes_into <= 15:
            return ("expected", "⏳ Esperado", "#FF9800")
        else:
            return ("delayed", "⚠ Retrasado", "#FF5252")
    
    # Next hour is in active hours → countdown
    next_hour = (current_hour + 1) % 24
    if next_hour in active_hours:
        minutes_left = 60 - now.minute
        return ("countdown", f"⏱ En ~{minutes_left}min", "#4CAF50")
    
    # Far from active window — show start hour
    return ("upcoming", f"{first_h:02d}:00", "")

class ForecastItemWidget(QFrame):
    """Single streamer forecast item with a clean UI."""
    def __init__(self, recording, likelihood: float, parent=None):
        super().__init__(parent)
        self.recording = recording
        self._likelihood = likelihood
        
        self.setFixedHeight(54)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Style the frame
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 6px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Platform badge
        platform = self.recording.platform or "Unknown"
        p_lower = platform.lower()
        if p_lower == "chaturbate":
            p_text = "CB"
        elif p_lower == "chaturbate-privates":
            p_text = "CBP"
        elif p_lower == "tiktok":
            p_text = "TK"
        else:
            p_text = platform[:2].upper()
            
        platform_color = _get_platform_color(platform)
        platform_badge = QLabel(p_text)
        platform_badge.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: white;
            background-color: {platform_color};
            border-radius: 4px;
            padding: 3px 6px;
            border: none;
        """)
        platform_badge.setFixedWidth(30)
        platform_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(platform_badge)
        
        # Streamer name
        name_lbl = QLabel(self.recording.streamer_name)
        name_lbl.setStyleSheet(f"""
            font-size: 13px; 
            font-weight: 600;
            color: {c['text']}; 
            border: none;
            background: transparent;
        """)
        layout.addWidget(name_lbl, 1)
        
        # Consistency bar (10 segments)
        consistency = self.recording.consistency_score or 0.0
        filled = int(consistency * 10)
        bar_str = "●" * filled + "○" * (10 - filled)
        consistency_lbl = QLabel(bar_str)
        consistency_lbl.setStyleSheet(f"""
            font-size: 11px; 
            color: {c['text_muted']}; 
            border: none;
            background: transparent;
        """)
        consistency_lbl.setFixedWidth(80)
        consistency_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(consistency_lbl)
        
        # Likelihood percentage
        likelihood_pct = int(self._likelihood * 100)
        lik_color = "#4CAF50" if self._likelihood >= 0.6 else "#FF9800" if self._likelihood >= 0.3 else c['text_muted']
        
        lik_lbl = QLabel(f"{likelihood_pct}%")
        lik_lbl.setStyleSheet(f"""
            font-size: 12px; 
            font-weight: bold;
            color: {lik_color}; 
            border: none;
            background: transparent;
        """)
        lik_lbl.setFixedWidth(45)
        lik_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lik_lbl)
        
        # Time / Status
        state, time_text, time_color = _get_forecast_time_info(self.recording)
        time_lbl = QLabel(time_text or "No info")
        color = time_color if time_color else c['text_muted']
        time_lbl.setStyleSheet(f"""
            font-size: 11px; 
            font-weight: {'bold' if state in ('expected', 'delayed', 'countdown', 'live_range') else 'normal'};
            color: {color}; 
            border: none;
            background: transparent;
        """)
        time_lbl.setFixedWidth(100)
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(time_lbl)


class LiveForecastDialog(QDialog):
    def __init__(self, app_context, recordings, parent=None):
        super().__init__(parent)
        
        # Requirement: Proper memory management
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        self.app = app_context
        self.recordings = recordings
        
        self.setWindowTitle("Previsión de Streams")
        self.setMinimumSize(600, 450)
        self.resize(650, 500)
        
        self._setup_ui()

    def _setup_ui(self):
        c = theme_manager.colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['bg']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        
        title_lbl = QLabel("🔮 Previsión de Streams")
        title_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c['text']};")
        header_layout.addWidget(title_lbl)
        
        subtitle_lbl = QLabel("Streams próximos a estar online basados en el historial reciente.")
        subtitle_lbl.setStyleSheet(f"font-size: 12px; color: {c['text_muted']};")
        header_layout.addWidget(subtitle_lbl)
        
        layout.addLayout(header_layout)
        
        # Scroll Area for the list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: {c['surface']};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {c['border']};
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c['text_muted']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 8, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        # Populate
        self._populate_list()
        
        # Footer
        btns = QHBoxLayout()
        btns.addStretch()
        
        close_btn = QPushButton("Cerrar")
        close_btn.setProperty("class", "primary") # Use app theme primary class
        close_btn.setMinimumWidth(100)
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)
        
        layout.addLayout(btns)
        
    def _populate_list(self):
        c = theme_manager.colors
        
        # Gather forecasts
        forecasts = []
        for rec in self.recordings:
            score = HistoryManager.get_likelihood_score(rec)
            # Only consider items with a likelihood >= 50% to be "likely soon"
            # Or if they are currently live
            # Also check if they have valid time info
            state, time_text, time_color = _get_forecast_time_info(rec)
            if rec.is_live or (score >= 0.50 and state in ('expected', 'delayed', 'countdown', 'live_range')):
                forecasts.append((rec, score))
                
        # Sort by score descending, then consistency descending
        forecasts.sort(key=lambda x: (x[1], x[0].consistency_score or 0.0), reverse=True)
        
        if not forecasts:
            empty_lbl = QLabel("No hay streams próximos según el historial.")
            empty_lbl.setStyleSheet(f"font-size: 13px; color: {c['text_muted']}; font-style: italic;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_lbl)
            return

        for rec, score in forecasts:
            item_widget = ForecastItemWidget(rec, score, parent=self.scroll_content)
            self.scroll_layout.addWidget(item_widget)
