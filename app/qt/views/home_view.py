"""
Qt Home View for StreamCap.

Dashboard principal con estadísticas en vivo, acciones rápidas,
y cards de características. Sustituye la vista Home de Flet.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF, QSize
from PySide6.QtGui import (
    QColor, QPainter, QBrush, QLinearGradient, QPen, QFont, QDesktopServices
)
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QGraphicsOpacityEffect,
)

from app.qt.themes.theme import theme_manager, STATUS_COLORS
from app.utils.logger import logger


# ── Reusable sub-widgets ──────────────────────────────────────────────────────

class StatCard(QFrame):
    """Small stat card with icon + number + label.

    Uses QPainter for the accent top-border stripe (Elite anti-aliasing §3).
    """

    def __init__(
        self,
        icon: str,
        title: str,
        value: str = "0",
        accent: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._initial_accent_setting = accent
        self._accent = theme_manager.get_color("accent") if accent == "use_theme_accent" else (accent or theme_manager.get_color("accent"))
        self.setMinimumWidth(140)
        self.setFixedHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup(icon, title, value)

        # Subscribe to theme changes so colours stay fresh
        theme_manager.themeChanged.connect(self._refresh_colors)

    def _setup(self, icon: str, title: str, value: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 18, 16, 14)
        layout.setSpacing(4)

        # Icon row
        icon_row = QHBoxLayout()
        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        icon_row.addWidget(self.icon_lbl)
        icon_row.addStretch()
        layout.addLayout(icon_row)

        # Value (big number)
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: 800; color: {self._accent}; background: transparent;"
        )
        layout.addWidget(self.value_lbl)

        # Title label
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(
            f"font-size: 11px; color: {theme_manager.get_color('text_sec')}; background: transparent;"
        )
        layout.addWidget(self.title_lbl)

    def set_value(self, v: str) -> None:
        self.value_lbl.setText(v)

    def paintEvent(self, event) -> None:  # noqa: N802
        """Draw card background + accent top stripe (Elite anti-alias §3)."""
        p = QPainter(self)
        p.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        c = theme_manager.colors
        r = self.rect()

        # Card background
        p.setPen(QPen(QColor(c["border"]), 1))
        p.setBrush(QBrush(QColor(c["surface"])))
        p.drawRoundedRect(r.adjusted(1, 1, -1, -1), 10, 10)

        # Accent stripe (top 3 px)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(self._accent)))
        p.drawRoundedRect(QRectF(2, 1, r.width() - 4, 4), 2, 2)

    def _refresh_colors(self) -> None:
        if self._initial_accent_setting == "use_theme_accent":
            self._accent = theme_manager.get_color("accent")
            
        self.title_lbl.setStyleSheet(
            f"font-size: 11px; color: {theme_manager.get_color('text_sec')}; background: transparent;"
        )
        self.value_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: 800; color: {self._accent}; background: transparent;"
        )
        self.update()


class FeatureCard(QFrame):
    """Larger feature highlight card."""

    def __init__(
        self,
        icon: str,
        title: str,
        description: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setMinimumWidth(160)
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup(icon, title, description)

        # Hover opacity effect (micro-interaction §7)
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(1.0)
        self.setGraphicsEffect(self._effect)
        
        theme_manager.themeChanged.connect(self._refresh_colors)

    def _refresh_colors(self) -> None:
        self.icon_lbl.setStyleSheet(
            f"font-size: 24px; font-weight: 900; "
            f"color: {theme_manager.get_color('accent')}; background: transparent;"
        )

    def _setup(self, icon: str, title: str, description: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        self.icon_lbl = QLabel(icon)
        # Use accent color for the icon — gives it identity without emoji engine
        self.icon_lbl.setStyleSheet(
            f"font-size: 24px; font-weight: 900; "
            f"color: {theme_manager.get_color('accent')}; background: transparent;"
        )
        layout.addWidget(self.icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-weight: 700; font-size: 13px; background: transparent;")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setWordWrap(True)
        desc_lbl.setProperty("class", "muted")
        layout.addWidget(desc_lbl)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._animate_opacity(0.85)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._animate_opacity(1.0)
        super().leaveEvent(event)

    def _animate_opacity(self, target: float) -> None:
        anim = QPropertyAnimation(self._effect, b"opacity", self)
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.setStartValue(self._effect.opacity())
        anim.setEndValue(target)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


class QuickActionButton(QPushButton):
    """Pill-style quick-action button with icon + label."""

    def __init__(
        self,
        icon: str,
        label: str,
        accent: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._initial_accent_setting = accent
        self._accent = theme_manager.get_color("accent") if accent == "use_theme_accent" else (accent or theme_manager.get_color("accent"))
        self.setFixedHeight(42)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setText(f"{icon}  {label}")
        self._refresh_style()
        theme_manager.themeChanged.connect(self._refresh_style)

    def _refresh_style(self):
        if self._initial_accent_setting == "use_theme_accent":
            self._accent = theme_manager.get_color("accent")
            
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._accent};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 0 16px;
                font-weight: 600;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {QColor(self._accent).lighter(115).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(self._accent).darker(115).name()};
            }}
        """)


# ── Main View ─────────────────────────────────────────────────────────────────

class QtHomeView(QWidget):
    """
    Home dashboard for StreamCap Qt.

    Layout:
        ┌─────────────────────────────────┐
        │  Header (Welcome + subtitle)    │
        │  Stat Cards row (4 cards)       │
        │  Quick Actions row              │
        │  Feature Cards grid (2×3)       │
        │  Recent Activity / tip section  │
        └─────────────────────────────────┘
    """

    def __init__(self, app_context) -> None:
        super().__init__()
        self.app = app_context
        self.language = self.app.language_manager.language
        self._l = self.language.get("home_page", {})
        self._stat_cards: dict[str, StatCard] = {}

        self._setup_ui()
        self._refresh_stats()

        # Live-update stats every 10 seconds
        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(10_000)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start()

        # Subscribe to recording changes for immediate stat updates
        self.app.event_bus.subscribe("update", self._on_recording_event)
        self.app.event_bus.subscribe("add",    self._on_recording_event)
        self.app.event_bus.subscribe("delete", self._on_recording_event)

        # Theme changes
        theme_manager.themeChanged.connect(self._on_theme_changed)

    # ── UI Construction ───────────────────────────────────────────

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll wrapper so content is accessible on small windows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent; border: none;")
        outer.addWidget(scroll)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        self._main_layout = QVBoxLayout(content)
        self._main_layout.setContentsMargins(30, 30, 30, 30)
        self._main_layout.setSpacing(28)

        scroll.setWidget(content)

        self._build_header()
        self._build_stat_cards()
        self._build_quick_actions()
        self._build_feature_cards()
        self._build_tip_section()

        self._main_layout.addStretch()

    def _build_header(self) -> None:
        c = theme_manager.colors

        wrapper = QWidget()
        wrapper.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c['surface']},
                    stop:1 {c['bg']}
                );
                border-radius: 12px;
            }}
        """)
        h_layout = QVBoxLayout(wrapper)
        h_layout.setContentsMargins(24, 20, 24, 20)
        h_layout.setSpacing(6)

        title = QLabel("StreamCap")
        self._header_title_lbl = title
        title.setStyleSheet(
            f"font-size: 34px; font-weight: 800; color: {c['accent']}; background: transparent;"
        )
        h_layout.addWidget(title)

        subtitle = QLabel(
            self._l.get("tagline", "Multi-platform live-stream recording dashboard")
        )
        subtitle.setStyleSheet(
            f"font-size: 14px; color: {c['text_sec']}; background: transparent;"
        )
        h_layout.addWidget(subtitle)

        self._main_layout.addWidget(wrapper)
        self._header_wrapper = wrapper

    def _build_stat_cards(self) -> None:
        c = theme_manager.colors

        section_lbl = QLabel(self._l.get("stats", "Overview"))
        section_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
            f"color: {c['text_muted']}; text-transform: uppercase;"
        )
        self._main_layout.addWidget(section_lbl)
        self._section_overview_lbl = section_lbl

        row = QHBoxLayout()
        row.setSpacing(12)

        defs = [
            ("total",     "▣",  self._l.get("total_rooms", "Total Streams"),  "use_theme_accent"),
            ("recording", "◉",  self._l.get("active_recordings", "Recording"),      STATUS_COLORS["recording"]),
            ("live",      "◎",  self.language.get("recording_manager", {}).get("is_live", "Live"),           STATUS_COLORS["living"]),
            ("offline",   "○",  self.language.get("recording_card", {}).get("offline", "Offline"),        STATUS_COLORS["offline"]),
        ]

        for key, icon, label, accent in defs:
            card = StatCard(icon, label, "0", accent=accent)
            row.addWidget(card)
            self._stat_cards[key] = card

        self._main_layout.addLayout(row)

    def _build_quick_actions(self) -> None:
        c = theme_manager.colors

        section_lbl = QLabel(self.language.get("recordings_page", {}).get("operations", "Quick Actions"))
        section_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
            f"color: {c['text_muted']}; text-transform: uppercase;"
        )
        self._main_layout.addWidget(section_lbl)
        self._section_actions_lbl = section_lbl

        row = QHBoxLayout()
        row.setSpacing(10)

        self.btn_add_stream = QuickActionButton(
            "+", self.language.get("recordings_page", {}).get("add_record", "Add Stream"),
            accent="use_theme_accent",
        )
        self.btn_add_stream.clicked.connect(self._on_add_stream)
        row.addWidget(self.btn_add_stream)

        self.btn_go_recordings = QuickActionButton(
            "▶", self.language.get("sidebar", {}).get("recordings", "View Recordings"),
            accent="#4A4A6A",
        )
        self.btn_go_recordings.clicked.connect(self._on_go_recordings)
        row.addWidget(self.btn_go_recordings)

        self.btn_settings = QuickActionButton(
            "✦", self.language.get("sidebar", {}).get("settings", "Settings"),
            accent="#4A4A6A",
        )
        self.btn_settings.clicked.connect(self._on_open_settings)
        row.addWidget(self.btn_settings)

        self._main_layout.addLayout(row)

    def _build_feature_cards(self) -> None:
        c = theme_manager.colors

        section_lbl = QLabel(self._l.get("main_features", "Features"))
        section_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
            f"color: {c['text_muted']}; text-transform: uppercase;"
        )
        self._main_layout.addWidget(section_lbl)
        self._section_features_lbl = section_lbl

        grid = QGridLayout()
        grid.setSpacing(12)

        about_l = self.language.get("about_page", {})
        param_l = self.language.get("settings_page", {})
        
        features = [
            ("◈",  about_l.get("support_platforms", "30+ Platforms"),
             self._l.get("feature_desc_1", "Record streams from Twitch, YouTube, TikTok, Bilibili, and more.")),
            ("◉",  self._l.get("feature_title_1", "Auto-Recording"),
             "Start recording automatically when your favourite streamer goes live."),
            ("✦",  param_l.get("recording_quality", "Custom Quality"),
             about_l.get("customize_recording", "Choose OD, UHD, HD, SD or LD per stream.")),
            ("◆",  self._l.get("feature_title_2", "Push Notifications"),
             self._l.get("feature_desc_2", "Receive instant alerts on stream start and end.")),
            ("↺",  about_l.get("automatic_transcoding", "Auto-Transcode"),
             param_l.get("convert_mp4", "Convert recordings to MP4 automatically after capture.")),
            ("◑",  self.language.get("sidebar", {}).get("light_theme", "Light") + " / " + self.language.get("sidebar", {}).get("dark_theme", "Dark Mode"),
             "Switch themes instantly without restarting the app."),
        ]

        for i, (icon, title, desc) in enumerate(features):
            card = FeatureCard(icon, title, desc)
            grid.addWidget(card, i // 3, i % 3)

        self._main_layout.addLayout(grid)

    def _build_tip_section(self) -> None:
        c = theme_manager.colors

        tip = QFrame()
        tip.setObjectName("tipFrame")
        tip.setStyleSheet(f"""
            QFrame#tipFrame {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-left: 3px solid {c['accent']};
                border-radius: 8px;
            }}
        """)
        self._tip_frame = tip

        tip_layout = QHBoxLayout(tip)
        tip_layout.setContentsMargins(16, 12, 16, 12)
        tip_layout.setSpacing(12)

        bulb = QLabel("◆")
        bulb.setStyleSheet(
            f"font-size: 16px; font-weight: 900; "
            f"color: {c['accent']}; background: transparent;"
        )
        bulb.setFixedWidth(24)
        tip_layout.addWidget(bulb)

        tip_text = QLabel(
            f"<b>{self.language.get('recordings_page', {}).get('refresh_success_tip', 'Pro tip').split(':')[0]}:</b> "
            "Use the Recordings view filter bar to quickly find streams "
            f"by status ({self.language.get('recording_manager', {}).get('is_live', 'Live')}, "
            f"{self.language.get('recording_card', {}).get('recording', 'Recording')}, "
            f"{self.language.get('recording_card', {}).get('offline', 'Offline')})."
        )
        tip_text.setWordWrap(True)
        tip_text.setStyleSheet(f"color: {c['text_sec']}; font-size: 13px; background: transparent;")
        tip_layout.addWidget(tip_text, 1)

        self._tip_bulb_lbl = bulb
        self._tip_text_lbl = tip_text
        self._main_layout.addWidget(tip)

    # ── Data Refresh ──────────────────────────────────────────────

    def _refresh_stats(self) -> None:
        """Recalculate and display the stat cards from live data."""
        try:
            recordings = self.app.record_manager.recordings
            total = len(recordings)
            rec_count = sum(1 for r in recordings if r.is_recording)
            live_count = sum(1 for r in recordings if r.is_live and not r.is_recording)
            offline_count = total - rec_count - live_count

            self._stat_cards["total"].set_value(str(total))
            self._stat_cards["recording"].set_value(str(rec_count))
            self._stat_cards["live"].set_value(str(live_count))
            self._stat_cards["offline"].set_value(str(max(0, offline_count)))
        except (KeyboardInterrupt, SystemError):
            # Ignore interrupts during refresh, main loop will handle exit
            pass
        except Exception as e:
            logger.error(f"HomeView: Error refreshing stats: {e}")

    def _on_recording_event(self, topic, data) -> None:
        """React to any recording bus event by refreshing stats."""
        QTimer.singleShot(100, self._refresh_stats)

    # ── Navigation helpers ────────────────────────────────────────

    def _on_add_stream(self) -> None:
        from app.qt.components.add_stream_dialog import QtAddStreamDialog
        dialog = QtAddStreamDialog(self.app, self)
        dialog.exec()

    def _on_go_recordings(self) -> None:
        if mw := getattr(self.app, "main_window", None):
            mw.show_page("recordings")

    def _on_open_settings(self) -> None:
        if mw := getattr(self.app, "main_window", None):
            mw.show_page("settings")

    # ── Theme subscription (§2 Unpolish/Polish) ───────────────────

    def _on_theme_changed(self) -> None:
        """Refresh colours that are set inline (not via QSS tokens)."""
        c = theme_manager.colors

        # Header wrapper gradient
        self._header_wrapper.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {c['surface']},
                    stop:1 {c['bg']}
                );
                border-radius: 12px;
            }}
        """)

        # Section labels
        section_style = (
            f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
            f"color: {c['text_muted']}; text-transform: uppercase;"
        )
        for lbl in (
            self._section_overview_lbl,
            self._section_actions_lbl,
            self._section_features_lbl,
        ):
            lbl.setStyleSheet(section_style)
            
        self._header_title_lbl.setStyleSheet(
            f"font-size: 34px; font-weight: 800; color: {c['accent']}; background: transparent;"
        )

        # Tip frame
        self._tip_frame.setStyleSheet(f"""
            QFrame#tipFrame {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-left: 3px solid {c['accent']};
                border-radius: 8px;
            }}
        """)
        self._tip_text_lbl.setStyleSheet(
            f"color: {c['text_sec']}; font-size: 13px; background: transparent;"
        )
        self._tip_bulb_lbl.setStyleSheet(
            f"font-size: 16px; font-weight: 900; "
            f"color: {c['accent']}; background: transparent;"
        )
