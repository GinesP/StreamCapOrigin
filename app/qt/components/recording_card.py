"""
Qt Recording Card — StreamCap.

Architecture:
  ┌─────────────────────────────────────────────────────────────────────┐
  │ QFrame (card)                                                       │
  │  ├─ stripe: QFrame (4px coloured left border)                      │
  │  └─ body: QWidget                                                   │
  │      ├─ [GRID LAYOUT - QVBoxLayout]  shown in grid mode            │
  │      │   ├─ top_row (avatar / name / status / badges)              │
  │      │   ├─ dates_lbl                                               │
  │      │   └─ action_bar (always created, shown/hidden on hover)     │
  │      └─ [LIST LAYOUT - QHBoxLayout]  shown in list mode            │
  │          ├─ avatar                                                   │
  │          ├─ info_col (name / status) ── stretch                    │
  │          ├─ badge_row                                               │
  │          └─ btn_row  (always visible)                               │
  └─────────────────────────────────────────────────────────────────────┘

Key design decisions
────────────────────
• Two inner QWidgets (grid_w / list_w) are show/hidden.  No effects on self.
• Shadow is drawn only in paintEvent to avoid QGraphicsEffect conflicts.
• Hover in grid  → show/hide action_bar via setVisible (no opacity effect).
• Hover in list  → card background colour shift via setProperty + repaint.
• _is_hovered initialised in __init__ so leaveEvent never crashes.
"""

from __future__ import annotations

import os

from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen, QPainterPath,
)
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.models.recording.recording_status_model import RecordingStatus, CardStateType
from app.utils.logger import logger


# ── Palette ───────────────────────────────────────────────────────────────────

_STATUS_COLOR: dict[CardStateType, str] = {
    CardStateType.RECORDING: "#4CAF50",
    CardStateType.ERROR:     "#FF9800",
    CardStateType.LIVE:      "#F44336",
    CardStateType.OFFLINE:   "#757575",
    CardStateType.STOPPED:   "#546E7A",
    CardStateType.CHECKING:  "#AB47BC",
}

_CARD_BG        = "#2D2D2D"
_CARD_BG_HOVER  = "#363636"
_CARD_BORDER    = "#383838"


# ── Helpers ───────────────────────────────────────────────────────────────────

class _Avatar(QLabel):
    """40 px circular avatar widget with letter placeholder."""

    def __init__(self, size: int = 40, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sz  = size
        self._bg  = "#4A4A6A"
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Segoe UI", max(8, size // 3), QFont.Weight.Bold))
        self._refresh_style()

    def _refresh_style(self) -> None:
        r = self._sz // 2
        self.setStyleSheet(
            f"border-radius:{r}px; background:{self._bg};"
            f" color:#E1E1E1; border:none;"
        )

    def set_letter(self, char: str, bg: str = "#4A4A6A") -> None:
        self._bg = bg
        self._refresh_style()
        self.setText(char.upper())


class _Badge(QFrame):
    """Small coloured pill badge: text on a solid colour."""

    def __init__(
        self, text: str, color: str, tip: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setToolTip(tip)
        self.setFixedHeight(20)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(7, 0, 7, 0)
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "color:#fff; font-size:10px; font-weight:700; background:transparent;"
        )
        lay.addWidget(lbl)
        self.setStyleSheet(
            f"background:{color}; border-radius:5px; border:none;"
        )


def _mk_btn(icon: str, tip: str, parent: QWidget) -> QPushButton:
    """Create a small icon action button."""
    b = QPushButton(icon, parent)
    b.setToolTip(tip)
    b.setFixedSize(38, 24)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet("""
        QPushButton {
            background: #3A3A3A;
            color: #BBBBBB;
            border: 1px solid #555555;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 700;
            font-family: "Consolas", "Courier New", monospace;
            padding: 0;
            margin: 0;
        }
        QPushButton:hover {
            background: #FF6428;
            color: #FFFFFF;
            border-color: #FF8050;
        }
        QPushButton:pressed {
            background: #CC4F20;
        }
    """)
    return b


# ── Card ──────────────────────────────────────────────────────────────────────

_ACTIONS = [
    ("folder",  "Dir",  "Open Folder"),
    ("play",    "Run",  "Start / Stop"),
    ("preview", "Play", "Preview"),
    ("edit",    "Edit", "Edit"),
    ("info",    "Info", "Info"),
    ("delete",  "Del",  "Delete"),
]


class QtRecordingCard(QFrame):
    """
    Dual-mode recording card (list / grid).

    Call ``set_view_mode("list")`` or ``set_view_mode("grid")`` to switch.
    The card starts in list mode.
    """

    def __init__(
        self,
        recording,
        app_context,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.recording   = recording
        self.app         = app_context
        self._hovered    = False
        self._mode       = "list"
        self._status_color = _CARD_BG

        self._build()
        self.update_content()

    # ─────────────────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.setObjectName(f"rec_card_{self.recording.rec_id}")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Colored stripe
        self._stripe = QFrame()
        self._stripe.setFixedWidth(4)
        root.addWidget(self._stripe)

        # Body container
        self._body = QWidget()
        self._body.setStyleSheet("background: transparent;")
        root.addWidget(self._body, 1)

        body_root = QVBoxLayout(self._body)
        body_root.setContentsMargins(0, 0, 0, 0)
        body_root.setSpacing(0)

        self._grid_w = self._build_grid()
        self._list_w = self._build_list()

        body_root.addWidget(self._grid_w)
        body_root.addWidget(self._list_w)

        # Initial: list mode
        self._grid_w.hide()
        self._list_w.show()

    # ── Grid body ─────────────────────────────────────────────────────────────

    def _build_grid(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(14, 12, 12, 10)
        lay.setSpacing(5)

        # Top row
        top = QHBoxLayout()
        top.setSpacing(10)
        self._g_av = _Avatar(40, w)
        top.addWidget(self._g_av)

        info = QVBoxLayout()
        info.setSpacing(2)
        self._g_name   = QLabel(parent=w)
        self._g_name.setStyleSheet(
            "font-weight:700; font-size:13px; background:transparent; color:#E1E1E1;"
        )
        self._g_name.setWordWrap(False)
        info.addWidget(self._g_name)

        status_row = QHBoxLayout()
        self._g_status = QLabel(parent=w)
        self._g_status.setStyleSheet(
            "font-size:11px; font-weight:600; background:transparent;"
        )
        self._g_dur = QLabel(parent=w)
        self._g_dur.setStyleSheet(
            "font-size:10px; color:#777; background:transparent;"
        )
        status_row.addWidget(self._g_status)
        status_row.addWidget(self._g_dur)
        status_row.addStretch()
        info.addLayout(status_row)
        top.addLayout(info, 1)

        self._g_badge_row = QHBoxLayout()
        self._g_badge_row.setSpacing(4)
        top.addLayout(self._g_badge_row)
        lay.addLayout(top)

        # Dates
        self._g_dates = QLabel(parent=w)
        self._g_dates.setStyleSheet(
            "font-size:10px; color:#666; background:transparent;"
        )
        lay.addWidget(self._g_dates)
        lay.addStretch()

        # Action bar — hidden initially, shown on hover
        self._g_actions = QWidget(w)
        self._g_actions.setStyleSheet("background:transparent;")
        ab = QHBoxLayout(self._g_actions)
        ab.setContentsMargins(0, 0, 0, 0)
        ab.setSpacing(3)

        self._g_btns: dict[str, QPushButton] = {}
        for name, icon, tip in _ACTIONS:
            btn = _mk_btn(icon, tip, self._g_actions)
            btn.clicked.connect(lambda _, n=name: self._on_action(n))
            ab.addWidget(btn)
            self._g_btns[name] = btn
        ab.addStretch()

        self._g_actions.hide()   # hidden until hover
        lay.addWidget(self._g_actions)
        return w

    # ── List body ─────────────────────────────────────────────────────────────

    def _build_list(self) -> QWidget:
        w = QWidget()
        w.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 0, 10, 0)
        lay.setSpacing(10)
        lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._l_av = _Avatar(36, w)
        lay.addWidget(self._l_av)

        # Info
        info = QVBoxLayout()
        info.setSpacing(1)
        self._l_name = QLabel(parent=w)
        self._l_name.setStyleSheet(
            "font-weight:700; font-size:13px; background:transparent; color:#E1E1E1;"
        )
        info.addWidget(self._l_name)

        status_row = QHBoxLayout()
        self._l_status = QLabel(parent=w)
        self._l_status.setStyleSheet(
            "font-size:11px; font-weight:600; background:transparent;"
        )
        self._l_dur = QLabel(parent=w)
        self._l_dur.setStyleSheet(
            "font-size:10px; color:#777; background:transparent;"
        )
        status_row.addWidget(self._l_status)
        status_row.addWidget(self._l_dur)
        status_row.addStretch()
        info.addLayout(status_row)
        lay.addLayout(info, 1)

        # Badges
        self._l_badge_row = QHBoxLayout()
        self._l_badge_row.setSpacing(4)
        self._l_badge_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(self._l_badge_row)

        # Action buttons — always visible in list mode
        btn_w = QWidget(w)
        btn_w.setStyleSheet("background:transparent;")
        btn_lay = QHBoxLayout(btn_w)
        btn_lay.setContentsMargins(4, 0, 4, 0)
        btn_lay.setSpacing(3)

        self._l_btns: dict[str, QPushButton] = {}
        for name, icon, tip in _ACTIONS:
            btn = _mk_btn(icon, tip, btn_w)
            btn.clicked.connect(lambda _, n=name: self._on_action(n))
            btn_lay.addWidget(btn)
            self._l_btns[name] = btn

        lay.addWidget(btn_w)
        return w

    # ─────────────────────────────────────────────────────────────────────────
    # Mode
    # ─────────────────────────────────────────────────────────────────────────

    def set_view_mode(self, mode: str) -> None:
        """Switch between 'list' (default) and 'grid'."""
        self._mode = mode
        if mode == "list":
            self._grid_w.hide()
            self._list_w.show()
            self.setFixedHeight(72)
            self.setMinimumWidth(0)
            self.setMaximumWidth(16_777_215)
            self._update_stripe_style()
        else:
            self._list_w.hide()
            self._grid_w.show()
            self._g_actions.hide()
            self.setFixedSize(320, 165)
            self._update_stripe_style()

    # ─────────────────────────────────────────────────────────────────────────
    # Content
    # ─────────────────────────────────────────────────────────────────────────

    def update_content(self) -> None:
        rec = self.recording

        from app.core.recording.recording_state_logic import RecordingStateLogic
        state = RecordingStateLogic.get_card_state(rec)
        color = _STATUS_COLOR.get(state, "#546E7A")
        self._status_color = color

        # Title
        name = rec.streamer_name or "Unknown"
        if rec.status_info == RecordingStatus.RECORDING and getattr(rec, "live_title", None):
            name = f"{rec.streamer_name} — {rec.live_title}"

        # Duration
        dur = self.app.record_manager.get_duration(rec)
        dur_t = f"  {dur}" if (rec.is_recording or rec.is_live) and dur != "00:00:00" else ""

        # Avatar letter
        letter = rec.streamer_name[0].upper() if rec.streamer_name else "?"

        # Grid
        self._g_av.set_letter(letter, color)
        self._g_name.setText(name)
        self._g_status.setText(rec.status_info or "Idle")
        self._g_status.setStyleSheet(
            f"color:{color}; font-size:11px; font-weight:600; background:transparent;"
        )
        self._g_dur.setText(dur_t)
        added = getattr(rec, "added_at", "")
        self._g_dates.setText(f"Added: {added}" if added else "")

        # List
        self._l_av.set_letter(letter, color)
        self._l_name.setText(name)
        self._l_status.setText(rec.status_info or "Idle")
        self._l_status.setStyleSheet(
            f"color:{color}; font-size:11px; font-weight:600; background:transparent;"
        )
        self._l_dur.setText(dur_t)

        # Badges
        self._fill_badges(rec, self._g_badge_row)
        self._fill_badges(rec, self._l_badge_row)

        # Stripe
        self._update_stripe_style()

    def _update_stripe_style(self) -> None:
        radius = "6px" if self._mode == "grid" else "2px"
        self._stripe.setStyleSheet(
            f"background:{self._status_color}; border:none;"
            f" border-top-left-radius:{radius}; border-bottom-left-radius:{radius};"
        )

    @staticmethod
    def _fill_badges(rec, layout: QHBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if w := item.widget():
                w.setParent(None)  # safe deletion in layout context
                w.deleteLater()

        interval = getattr(rec, "loop_time_seconds", 60)
        q_t, q_c = (
            ("F", "#4CAF50") if interval <= 60 else
            ("M", "#FF9800") if interval <= 180 else
            ("S", "#F44336")
        )
        layout.addWidget(_Badge(q_t, q_c, "Queue speed"))

        try:
            from app.core.recording.history_manager import HistoryManager
            score = HistoryManager.get_likelihood_score(rec)
            if score > 0:
                l_t = "High" if score >= 0.8 else "Normal"
                l_c = "#4CAF50" if score >= 0.8 else "#42A5F5"
                layout.addWidget(_Badge(l_t, l_c, f"Likelihood {score:.0%}"))
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Painting  (card background + shadow drawn here to avoid effect conflicts)
    # ─────────────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:                    # noqa: N802
        p = QPainter(self)
        p.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.TextAntialiasing
        )
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        radius = 10.0

        # Card fill
        bg = _CARD_BG_HOVER if self._hovered else _CARD_BG
        p.setPen(QPen(QColor(_CARD_BORDER), 1))
        p.setBrush(QBrush(QColor(bg)))
        p.drawRoundedRect(r, radius, radius)

    # ─────────────────────────────────────────────────────────────────────────
    # Hover
    # ─────────────────────────────────────────────────────────────────────────

    def enterEvent(self, event) -> None:                    # noqa: N802
        self._hovered = True
        self.update()                       # repaint for bg change
        if self._mode == "grid":
            self._g_actions.show()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:                    # noqa: N802
        self._hovered = False
        self.update()
        if self._mode == "grid":
            self._g_actions.hide()
        super().leaveEvent(event)

    # ─────────────────────────────────────────────────────────────────────────
    # Actions
    # ─────────────────────────────────────────────────────────────────────────

    def _on_action(self, name: str) -> None:
        rec = self.recording
        logger.debug(f"Card {rec.rec_id}: '{name}'")

        if name == "folder":
            path = getattr(rec, "recording_dir", None) or self.app.settings.get_video_save_path()
            from app.utils import utils
            utils.open_folder(path)

        elif name == "play":
            if rec.is_recording:
                self.app.event_bus.run_task(
                    self.app.record_manager.stop_recording, rec, manually_stopped=True
                )
            else:
                self.app.event_bus.run_task(
                    self.app.record_manager.start_monitor_recording, rec
                )

        elif name == "preview":
            path = getattr(rec, "recording_dir", None)
            if path and os.path.exists(path):
                from app.utils import utils
                prefix = utils.clean_name(rec.streamer_name)
                videos = []
                for root, _, files in os.walk(path):
                    for f in files:
                        if utils.is_valid_video_file(f) and prefix in f:
                            videos.append(os.path.join(root, f))
                if videos:
                    videos.sort(key=os.path.getmtime, reverse=True)
                    player = self.app.main_window.get_video_player()
                    self.app.event_bus.run_task(
                        player.preview_video, videos[0], room_url=rec.url
                    )

        elif name == "delete":
            from PySide6.QtWidgets import QMessageBox
            box = QMessageBox(self)
            box.setWindowTitle("Confirm Delete")
            box.setText(f"Are you sure you want to delete '{rec.streamer_name}'?")
            box.setInformativeText("This will stop any active recordings for this stream.")
            box.setIcon(QMessageBox.Icon.Warning)
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            box.setDefaultButton(QMessageBox.StandardButton.No)
            
            if box.exec() == QMessageBox.StandardButton.Yes:
                self.app.event_bus.run_task(
                    self.app.record_manager.remove_recording, rec
                )
                self.app.event_bus.publish("delete", rec)
                if hasattr(self.app.main_window, "show_toast"):
                    self.app.main_window.show_toast(f"Deleted: {rec.streamer_name}", "info")

        elif name == "edit":
            self._open_edit_dialog()

        elif name == "info":
            self._open_info_dialog()

    def _open_edit_dialog(self) -> None:
        try:
            from app.qt.components.add_stream_dialog import QtAddStreamDialog
            dialog = QtAddStreamDialog(self.app, self, recording=self.recording)
            dialog.exec()
        except Exception as exc:
            logger.warning(f"Edit dialog error: {exc}")

    def _open_info_dialog(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        rec = self.recording
        lines = [
            f"<b>Streamer:</b> {rec.streamer_name}",
            f"<b>URL:</b> {rec.url}",
            f"<b>Platform:</b> {getattr(rec, 'platform', 'N/A')}",
            f"<b>Status:</b> {rec.status_info}",
            f"<b>Quality:</b> {getattr(rec, 'record_quality', 'N/A')}",
            f"<b>Directory:</b> {getattr(rec, 'recording_dir', 'N/A')}",
        ]
        box = QMessageBox(self)
        box.setWindowTitle(f"Info — {rec.streamer_name}")
        box.setText("<br>".join(lines))
        box.setIcon(QMessageBox.Icon.Information)
        box.exec()
