"""
Qt Home View for StreamCap.

Dashboard principal con estadísticas en vivo, acciones rápidas,
cards de características e Intelligence Monitor con gráficas dinámicas.
Sustituye la vista Home de Flet.
"""

from __future__ import annotations

import collections
from typing import Sequence

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRectF, QSize
from PySide6.QtGui import (
    QColor, QPainter, QBrush, QLinearGradient, QPen, QFont, QDesktopServices,
    QFontMetrics,
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


# ── Intelligence Monitor widgets ──────────────────────────────────────────────

# Colour constants for queue lanes (consistent with QUEUE_COLORS in theme)
_FAST_COLOR   = "#4CAF50"   # green
_MEDIUM_COLOR = "#FF9800"   # orange
_SLOW_COLOR   = "#F44336"   # red
_BUSY_ALPHA   = 0.45        # dimmed version for "busy" bars


class QueueBarChart(QWidget):
    """Grouped bar chart showing Dispatched + Busy counts for F / M / S queues.

    Each cycle updates three groups (Fast, Medium, Slow) with two bars each:
    - Solid bar  → dispatched
    - Dimmer bar → busy (already checking)
    """

    _BAR_WIDTH  = 18
    _GROUP_GAP  = 14
    _BAR_GAP    = 4
    _BOTTOM_PAD = 28   # room for x-axis labels
    _TOP_PAD    = 12

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Current values (animated targets)
        self._disp = [0, 0, 0]   # F M S dispatched
        self._busy = [0, 0, 0]   # F M S busy
        self._waiting = 0

        # Rendered values (smoothly interpolated)
        self._rdisp = [0.0, 0.0, 0.0]
        self._rbusy = [0.0, 0.0, 0.0]

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(30)   # ~33 fps
        self._anim_timer.timeout.connect(self._step_animation)

        theme_manager.themeChanged.connect(self.update)

    def set_data(self, disp: Sequence[int], busy: Sequence[int], waiting: int) -> None:
        self._disp    = list(disp)
        self._busy    = list(busy)
        self._waiting = waiting
        if not self._anim_timer.isActive():
            self._anim_timer.start()

    def _step_animation(self) -> None:
        speed   = 0.22   # lerp factor per frame
        settled = True
        for i in range(3):
            for src, rendered in [("_disp", "_rdisp"), ("_busy", "_rbusy")]:
                target  = float(getattr(self, src)[i])
                current = getattr(self, rendered)[i]
                diff    = target - current
                if abs(diff) < 0.01:
                    getattr(self, rendered)[i] = target
                else:
                    getattr(self, rendered)[i] = current + diff * speed
                    settled = False
        if settled:
            self._anim_timer.stop()
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c      = theme_manager.colors
        w      = self.width()
        h      = self.height()
        bottom = h - self._BOTTOM_PAD
        chart_h = bottom - self._TOP_PAD

        # Background
        p.fillRect(self.rect(), QColor(c["surface"]))

        # Determine scale: max rendered value → full chart height
        max_val = max(
            max(self._rdisp + self._rbusy, default=0),
            1   # avoid /0
        )

        colors = [_FAST_COLOR, _MEDIUM_COLOR, _SLOW_COLOR]
        labels = ["Fast", "Med", "Slow"]
        group_w = self._BAR_WIDTH * 2 + self._BAR_GAP

        total_w = len(labels) * group_w + (len(labels) - 1) * self._GROUP_GAP
        x_start = (w - total_w) // 2

        font = QFont("Segoe UI", 9)
        p.setFont(font)
        fm = QFontMetrics(font)

        for i, (col, lbl) in enumerate(zip(colors, labels)):
            gx = x_start + i * (group_w + self._GROUP_GAP)

            # ── Dispatched bar (solid)
            dh = int(self._rdisp[i] / max_val * chart_h)
            dy = bottom - dh
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(col)))
            p.drawRoundedRect(gx, dy, self._BAR_WIDTH, dh, 3, 3)

            # Dispatched value label above bar
            if self._rdisp[i] >= 0.5:
                p.setPen(QPen(QColor(col)))
                disp_val = str(int(round(self._rdisp[i])))
                tw = fm.horizontalAdvance(disp_val)
                p.drawText(gx + (self._BAR_WIDTH - tw) // 2, dy - 3, disp_val)

            # ── Busy bar (dimmed)
            bx  = gx + self._BAR_WIDTH + self._BAR_GAP
            bh  = int(self._rbusy[i] / max_val * chart_h)
            bdy = bottom - bh
            busy_col = QColor(col)
            busy_col.setAlphaF(_BUSY_ALPHA)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(busy_col))
            p.drawRoundedRect(bx, bdy, self._BAR_WIDTH, bh, 3, 3)

            # Busy value label above bar
            if self._rbusy[i] >= 0.5:
                p.setPen(QPen(busy_col))
                busy_val = str(int(round(self._rbusy[i])))
                tw = fm.horizontalAdvance(busy_val)
                p.drawText(bx + (self._BAR_WIDTH - tw) // 2, bdy - 3, busy_val)

            # ── X-axis label
            p.setPen(QPen(QColor(c["text_muted"])))
            lw = fm.horizontalAdvance(lbl)
            p.drawText(gx + (group_w - lw) // 2, bottom + 16, lbl)

        # Baseline
        p.setPen(QPen(QColor(c["border"]), 1))
        p.drawLine(x_start - 4, bottom, x_start + total_w + 4, bottom)

        # "Waiting" label (bottom-right)
        if self._waiting > 0:
            p.setPen(QPen(QColor(c["text_sec"])))
            wait_txt = f"{self._waiting} waiting"
            p.setFont(QFont("Segoe UI", 8))
            p.drawText(w - fm.horizontalAdvance(wait_txt) - 8, h - 4, wait_txt)


class SparklineChart(QWidget):
    """Rolling area sparkline showing total dispatched per cycle over last N cycles."""

    HISTORY = 40

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(60)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._data: collections.deque[int] = collections.deque(maxlen=self.HISTORY)
        theme_manager.themeChanged.connect(self.update)

    def add_point(self, value: int) -> None:
        self._data.append(value)
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        if len(self._data) < 2:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c   = theme_manager.colors
        w   = self.width()
        h   = self.height()
        pad = 6

        p.fillRect(self.rect(), QColor(c["surface"]))

        data   = list(self._data)
        n      = len(data)
        max_v  = max(data) or 1
        step   = (w - pad * 2) / max(n - 1, 1)
        accent = theme_manager.get_color("accent")

        # Build polygon for the filled area
        from PySide6.QtGui import QPolygonF
        from PySide6.QtCore import QPointF

        pts = []
        for i, v in enumerate(data):
            x = pad + i * step
            y = (h - pad) - (v / max_v) * (h - pad * 2)
            pts.append(QPointF(x, y))

        # Filled gradient area
        grad = QLinearGradient(0, 0, 0, h)
        col_top = QColor(accent)
        col_top.setAlphaF(0.35)
        col_bot = QColor(accent)
        col_bot.setAlphaF(0.0)
        grad.setColorAt(0, col_top)
        grad.setColorAt(1, col_bot)

        fill_pts = [QPointF(pts[0].x(), h - pad)] + pts + [QPointF(pts[-1].x(), h - pad)]
        poly = QPolygonF(fill_pts)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPolygon(poly)

        # Line
        pen = QPen(QColor(accent), 2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        line_poly = QPolygonF(pts)
        p.drawPolyline(line_poly)

        # Last-value dot
        last_pt = pts[-1]
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(accent)))
        p.drawEllipse(last_pt, 4, 4)

        # Baseline
        p.setPen(QPen(QColor(c["border"]), 1))
        p.drawLine(pad, h - pad, w - pad, h - pad)


class IntelligenceMonitor(QFrame):
    """Dashboard panel for the Intelligence queue-management system.

    Displays:
    - Grouped bar chart: Dispatched vs Busy per queue tier (F/M/S)
    - Sparkline: rolling dispatched total over the last 40 cycles
    - Numeric summary row
    """

    def __init__(self, app_context, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app_context
        self.setProperty("class", "card")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._setup_ui()
        self._retranslate_ui()
        theme_manager.themeChanged.connect(self._on_theme_changed)

        # Subscribe to intelligence events from the record manager
        self.app.event_bus.subscribe("intelligence_cycle", self._on_intelligence_cycle)
        self.app.event_bus.subscribe("language_changed", self._on_language_changed)

    def _on_language_changed(self, new_language) -> None:
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        l_intel = self.app.language_manager.language.get("home_view", {})
        self._title_lbl.setText(l_intel.get("intelligence_monitor", "🧠 Intelligence Monitor"))
        for lbl, key in self._legend_items:
            lbl.setText(l_intel.get(key, key.capitalize()))
        self._busy_lbl.setText(l_intel.get("busy", "Busy"))
        self._bar_lbl.setText(l_intel.get("queue_activity", "Queue Activity"))
        self._spark_lbl.setText(l_intel.get("dispatched_per_cycle", "Dispatched / Cycle"))

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # ── Header row ─────────────────────────────────────────────
        hdr = QHBoxLayout()
        self._title_lbl = QLabel() # Empty initially
        self._title_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; "
            f"color: {theme_manager.get_color('text')}; background: transparent;"
        )
        hdr.addWidget(self._title_lbl)
        hdr.addStretch()

        # Legend labels stored
        self._legend_items = []
        for color, label_key in [(_FAST_COLOR, "fast"), (_MEDIUM_COLOR, "med"), (_SLOW_COLOR, "slow")]:
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {color}; font-size: 10px; background: transparent;")
            lbl = QLabel()
            lbl.setStyleSheet(
                f"color: {theme_manager.get_color('text_muted')}; font-size: 10px; background: transparent;"
            )
            hdr.addWidget(dot)
            hdr.addWidget(lbl)
            self._legend_items.append((lbl, label_key))

        # Legend: dimmed = busy
        dim_dot = QLabel("●")
        dim_dot.setStyleSheet(f"color: rgba(200,200,200,0.4); font-size: 10px; background: transparent;")
        self._busy_lbl = QLabel()
        self._busy_lbl.setStyleSheet(
            f"color: {theme_manager.get_color('text_muted')}; font-size: 10px; background: transparent;"
        )
        hdr.addWidget(dim_dot)
        hdr.addWidget(self._busy_lbl)

        root.addLayout(hdr)

        # ── Charts row ─────────────────────────────────────────────
        charts_row = QHBoxLayout()
        charts_row.setSpacing(12)

        # Bar chart
        bar_col = QVBoxLayout()
        self._bar_lbl = QLabel()
        self._bar_lbl.setStyleSheet(
            f"font-size: 10px; color: {theme_manager.get_color('text_muted')}; background: transparent;"
        )
        bar_col.addWidget(self._bar_lbl)
        self._bar_chart = QueueBarChart()
        bar_col.addWidget(self._bar_chart)
        charts_row.addLayout(bar_col, 1)

        # Vertical separator
        sep = QFrame()
        sep.setProperty("class", "divider-v")
        sep.setFixedWidth(1)
        charts_row.addWidget(sep)

        # Sparkline
        spark_col = QVBoxLayout()
        self._spark_lbl = QLabel()
        self._spark_lbl.setStyleSheet(
            f"font-size: 10px; color: {theme_manager.get_color('text_muted')}; background: transparent;"
        )
        spark_col.addWidget(self._spark_lbl)
        self._sparkline = SparklineChart()
        spark_col.addWidget(self._sparkline)
        charts_row.addLayout(spark_col, 2)

        root.addLayout(charts_row)

        # ── Numeric counters row ────────────────────────────────────
        num_row = QHBoxLayout()
        num_row.setSpacing(0)

        self._counters: dict[str, QLabel] = {}
        counter_defs = [
            ("disp_fast",   "↑F",   _FAST_COLOR),
            ("disp_medium", "↑M",   _MEDIUM_COLOR),
            ("disp_slow",   "↑S",   _SLOW_COLOR),
            ("busy_fast",   "~F",   _FAST_COLOR    + "88"),
            ("busy_medium", "~M",   _MEDIUM_COLOR  + "88"),
            ("busy_slow",   "~S",   _SLOW_COLOR    + "88"),
            ("waiting",     "⏸ wait", theme_manager.get_color("text_sec")),
        ]
        for key, label, color in counter_defs:
            cell = QWidget()
            cell_lay = QVBoxLayout(cell)
            cell_lay.setContentsMargins(8, 4, 8, 4)
            cell_lay.setSpacing(2)

            val_lbl = QLabel("0")
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_lbl.setStyleSheet(
                f"font-size: 16px; font-weight: 700; color: {color}; background: transparent;"
            )

            key_lbl = QLabel(label)
            key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            key_lbl.setStyleSheet(
                f"font-size: 9px; color: {theme_manager.get_color('text_muted')}; background: transparent;"
            )

            cell_lay.addWidget(val_lbl)
            cell_lay.addWidget(key_lbl)
            num_row.addWidget(cell, 1)

            self._counters[key] = val_lbl

            if key != counter_defs[-1][0]:
                vsep = QFrame()
                vsep.setProperty("class", "divider-v")
                vsep.setFixedWidth(1)
                num_row.addWidget(vsep)

        root.addLayout(num_row)

    def _on_intelligence_cycle(self, topic, data: dict) -> None:
        """Receive intelligence cycle data and update all charts."""
        disp = [data["disp_fast"], data["disp_medium"], data["disp_slow"]]
        busy = [data["busy_fast"], data["busy_medium"], data["busy_slow"]]

        self._bar_chart.set_data(disp, busy, data["waiting"])
        self._sparkline.add_point(data["total_disp"])

        # Update counters
        for key in ("disp_fast", "disp_medium", "disp_slow",
                    "busy_fast", "busy_medium", "busy_slow", "waiting"):
            if key in self._counters:
                self._counters[key].setText(str(data.get(key, 0)))

    def _on_theme_changed(self) -> None:
        self._title_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 700; "
            f"color: {theme_manager.get_color('text')}; background: transparent;"
        )
        for lbl in (self._bar_lbl, self._spark_lbl):
            lbl.setStyleSheet(
                f"font-size: 10px; color: {theme_manager.get_color('text_muted')}; background: transparent;"
            )
        self._bar_chart.update()
        self._sparkline.update()


# ── Main View ─────────────────────────────────────────────────────────────────

class QtHomeView(QWidget):
    """
    Home dashboard for StreamCap Qt.

    Layout:
        ┌─────────────────────────────────┐
        │  Header (Welcome + subtitle)    │
        │  Stat Cards row (4 cards)       │
        │  Intelligence Monitor           │
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

        self.app.event_bus.subscribe("language_changed", self._on_language_changed)
        
        self._setup_ui()
        self._retranslate_ui()
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

    def _on_language_changed(self, new_language) -> None:
        self.language = new_language
        self._l = self.language.get("home_page", {})
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        c = theme_manager.colors
        self._header_title_lbl.setText("StreamCap")
        self._header_subtitle_lbl.setText(self._l.get("tagline", "Multi-platform live-stream recording dashboard"))
        self._section_overview_lbl.setText(self._l.get("stats", "Overview"))
        
        # Stat cards
        defs = [
            ("total",     self._l.get("total_rooms", "Total Streams")),
            ("recording", self._l.get("active_recordings", "Recording")),
            ("live",      self.language.get("recording_manager", {}).get("is_live", "Live")),
            ("offline",   self.language.get("recording_card", {}).get("offline", "Offline")),
        ]
        for key, label in defs:
            if key in self._stat_cards:
                self._stat_cards[key].title_lbl.setText(label)

        self._section_intelligence_lbl.setText("INTELLIGENCE")
        self._section_actions_lbl.setText(self.language.get("recordings_page", {}).get("operations", "Quick Actions"))
        
        # Quick Actions
        self.btn_add_stream.setText(f"+  {self.language.get('recordings_page', {}).get('add_record', 'Add Stream')}")
        # Assuming forecast text should also be translated, but it's hardcoded "Previsión" above
        self.btn_live_forecast.setText(f"🔮  {'Previsión'}")
        self.btn_go_recordings.setText(f"▶  {self.language.get('sidebar', {}).get('recordings', 'View Recordings')}")
        self.btn_settings.setText(f"✦  {self.language.get('sidebar', {}).get('settings', 'Settings')}")

        self._section_features_lbl.setText(self._l.get("main_features", "Features"))
        
        # Tip
        self._tip_text_lbl.setText(
            f"<b>{self.language.get('recordings_page', {}).get('refresh_success_tip', 'Pro tip').split(':')[0]}:</b> "
            "Use the Recordings view filter bar to quickly find streams "
            f"by status ({self.language.get('recording_manager', {}).get('is_live', 'Live')}, "
            f"{self.language.get('recording_card', {}).get('recording', 'Recording')}, "
            f"{self.language.get('recording_card', {}).get('offline', 'Offline')})."
        )
        
        # Monitor retranslation
        l_intel = self.app.language_manager.language.get("home_view", {})
        self._intel_monitor._title_lbl.setText(l_intel.get("intelligence_monitor", "🧠 Intelligence Monitor"))
        for lbl, key in self._intel_monitor._legend_items:
            lbl.setText(l_intel.get(key, key.capitalize()))
        self._intel_monitor._busy_lbl.setText(l_intel.get("busy", "Busy"))
        self._intel_monitor._bar_lbl.setText(l_intel.get("queue_activity", "Queue Activity"))
        self._intel_monitor._spark_lbl.setText(l_intel.get("dispatched_per_cycle", "Dispatched / Cycle"))

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
        self._header_subtitle_lbl = subtitle
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
        self._section_intelligence_lbl = QLabel()
        self._section_intelligence_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 700; letter-spacing: 1px; "
            f"color: {c['text_muted']}; text-transform: uppercase;"
        )
        self._main_layout.addWidget(self._section_intelligence_lbl)


        self._intel_monitor = IntelligenceMonitor(self.app)
        self._main_layout.addWidget(self._intel_monitor)

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

        # Quick Actions
        self.btn_add_stream = QuickActionButton(
            "+", self.language.get("recordings_page", {}).get("add_record", "Add Stream"),
            accent="use_theme_accent",
        )
        self.btn_add_stream.clicked.connect(self._on_add_stream)
        row.addWidget(self.btn_add_stream)

        self.btn_live_forecast = QuickActionButton(
            "🔮", "Previsión",
            accent="#4A4A6A",
        )
        self.btn_live_forecast.clicked.connect(self._on_live_forecast)
        row.addWidget(self.btn_live_forecast)

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

    def _on_live_forecast(self) -> None:
        from app.qt.components.live_forecast_dialog import LiveForecastDialog
        recordings = self.app.record_manager.recordings
        dialog = LiveForecastDialog(self.app, recordings, self)
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
            self._section_intelligence_lbl,
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
