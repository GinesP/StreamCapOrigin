"""
Qt ThemeManager for StreamCap — Elite Level 10.

Implements the reactive Data-Driven JSON theme architecture:
- ThemeManager watches theme.json via QFileSystemWatcher (hot-reload)
- Emits themeChanged signal so every subscriber can unpolish/polish itself
- Dual palettes: Neutral Dark (default) and Neutral Light (professional)
- Accent color: #FF6428 (brand orange)
"""

from __future__ import annotations

import json
import os

from PySide6.QtCore import QFileSystemWatcher, QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QWidget


# ── Design Token Palettes ────────────────────────────────────────────────────
# Based on Pyside6_Native_Design_Guide.md  §5 & §8

NEUTRAL_DARK: dict[str, str] = {
    # Backgrounds
    "bg":          "#252525",
    "sidebar":     "#1A1A1A",
    "surface":     "#2D2D2D",
    "surface2":    "#333333",  # Hover state
    # Brand
    "accent":      "#FF6428",
    "accent_l":    "#FF8050",  # lighter 20 %
    "accent_d":    "#CC4F20",  # darker  20 %
    # Text
    "text":        "#E1E1E1",
    "text_sec":    "#A0A0A0",
    "text_muted":  "#666666",
    # Lines
    "border":      "#383838",
    "border_h":    "#484848",  # Highlighted border
    "divider":     "#2A2A2A",
    # Inputs
    "input_bg":    "#1E1E1E",
    "input_border":"#383838",
    "input_focus": "#FF6428",
    # Sidebar items
    "sb_hover":    "#2A2A2A",
    "sb_selected": "#332218",  # Tinted with accent
    # Scrollbar
    "scroll":      "#3A3A3A",
    "scroll_h":    "#505050",
    # Feedback
    "success":     "#4CAF50",
    "warning":     "#FF9800",
    "error":       "#F44336",
    "info":        "#2196F3",
    # Cards
    "card":        "#2D2D2D",
    "card_hover":  "#333333",
    # Tooltip
    "tooltip_bg":  "#1A1A1A",
    "tooltip_text":"#E1E1E1",
}

NEUTRAL_LIGHT: dict[str, str] = {
    # Backgrounds
    "bg":          "#F5F5F7",
    "sidebar":     "#EBEBED",
    "surface":     "#FFFFFF",
    "surface2":    "#F0F0F2",
    # Brand
    "accent":      "#FF6428",
    "accent_l":    "#FF8050",
    "accent_d":    "#CC4F20",
    # Text
    "text":        "#1D1D1F",
    "text_sec":    "#555565",
    "text_muted":  "#9E9EB0",
    # Lines
    "border":      "#DCDCE5",
    "border_h":    "#BDBDCA",
    "divider":     "#E8E8EF",
    # Inputs
    "input_bg":    "#FAFAFE",
    "input_border":"#DCDCE5",
    "input_focus": "#FF6428",
    # Sidebar items
    "sb_hover":    "#E0E0EC",
    "sb_selected": "#FFE8DE",
    # Scrollbar
    "scroll":      "#C0C0D0",
    "scroll_h":    "#A0A0B5",
    # Feedback
    "success":     "#388E3C",
    "warning":     "#E65100",
    "error":       "#C62828",
    "info":        "#1565C0",
    # Cards
    "card":        "#FFFFFF",
    "card_hover":  "#F8F8FF",
    # Tooltip
    "tooltip_bg":  "#2D2D2D",
    "tooltip_text":"#E1E1E1",
}

# Status / queue badge colors (shared)
STATUS_COLORS: dict[str, str] = {
    "recording": "#F44336",
    "living":    "#4CAF50",
    "offline":   "#9E9E9E",
    "error":     "#FF9800",
    "stopped":   "#607D8B",
}

QUEUE_COLORS: dict[str, str] = {
    "fast":   "#4CAF50",
    "medium": "#FF9800",
    "slow":   "#F44336",
}


# ── Helper ───────────────────────────────────────────────────────────────────

def _derive_accent_variants(accent_hex: str) -> tuple[str, str]:
    """Return (lighter, darker) hex variants of an accent color."""
    c = QColor(accent_hex)
    return c.lighter(120).name(), c.darker(120).name()


def update_widget_style(w: QWidget, state: str | None = None) -> None:
    """Force Qt to re-evaluate CSS for a widget (unpolish → polish).

    Used the 'Elite Unpolish/Polish' technique from the design guide §2
    to ensure dynamic property changes take effect immediately.
    """
    if state is not None:
        w.setProperty("state", state)
    w.style().unpolish(w)
    w.style().polish(w)
    w.update()


# ── Stylesheet Generator ─────────────────────────────────────────────────────

def _generate_stylesheet(c: dict[str, str]) -> str:
    """Build the full application QSS from the token dictionary ``c``."""
    return f"""
    /* ═══════════════════════════════════════════════════════════
       STREAMCAP — Elite Neutral Dark Stylesheet
       Token-driven via ThemeManager (Pyside6_Native_Design_Guide §5)
    ═══════════════════════════════════════════════════════════ */

    /* ── Global reset ─────────────────────────────────────────── */
    QMainWindow, QDialog, QWidget {{
        background-color: {c["bg"]};
        color: {c["text"]};
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 13px;
    }}

    /* ── Scroll areas ──────────────────────────────────────────── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {c["scroll"]};
        min-height: 36px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c["scroll_h"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {c["scroll"]};
        min-width: 36px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c["scroll_h"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

    /* ── Labels ────────────────────────────────────────────────── */
    QLabel {{
        color: {c["text"]};
        background: transparent;
    }}
    QLabel[class="secondary"] {{ color: {c["text_sec"]}; }}
    QLabel[class="muted"]     {{ color: {c["text_muted"]}; font-size: 12px; }}
    QLabel[class="heading"]   {{ font-size: 20px; font-weight: 700; color: {c["text"]}; }}
    QLabel[class="subheading"]{{ font-size: 15px; font-weight: 500; color: {c["text_sec"]}; }}
    QLabel[class="accent"]    {{ color: {c["accent"]}; font-weight: 600; }}

    /* ── Buttons ───────────────────────────────────────────────── */
    QPushButton {{
        background-color: {c["accent"]};
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {c["accent_l"]};
    }}
    QPushButton:pressed {{
        background-color: {c["accent_d"]};
    }}
    QPushButton:disabled {{
        background-color: {c["border"]};
        color: {c["text_muted"]};
    }}
    QPushButton[class="secondary"] {{
        background-color: transparent;
        color: {c["accent"]};
        border: 1px solid {c["accent"]};
    }}
    QPushButton[class="secondary"]:hover {{
        background-color: {c["accent"]};
        color: #ffffff;
    }}
    QPushButton[class="danger"] {{
        background-color: {c["error"]};
        color: #ffffff;
        border: none;
    }}
    QPushButton[class="danger"]:hover {{
        background-color: #c62828;
    }}
    QPushButton[class="icon"] {{
        background-color: transparent;
        border: none;
        padding: 6px;
        border-radius: 5px;
        font-size: 15px;
    }}
    QPushButton[class="icon"]:hover {{
        background-color: {c["surface2"]};
    }}
    QPushButton[class="filter-btn"] {{
        background-color: transparent;
        color: {c["text_sec"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 5px 14px;
        font-weight: 500;
    }}
    QPushButton[class="filter-btn"]:hover {{
        background-color: {c["surface2"]};
        color: {c["text"]};
    }}
    QPushButton[class="filter-btn"]:checked {{
        background-color: {c["accent"]};
        color: #ffffff;
        border: 1px solid {c["accent"]};
    }}

    /* ── Inputs ────────────────────────────────────────────────── */
    QLineEdit, QTextEdit {{
        background-color: {c["input_bg"]};
        color: {c["text"]};
        border: 1px solid {c["input_border"]};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {c["accent"]};
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {c["input_focus"]};
    }}
    QLineEdit:read-only {{
        color: {c["text_sec"]};
    }}
    QLineEdit::placeholder, QTextEdit::placeholder {{
        color: {c["text_muted"]};
    }}

    /* ── ComboBox ──────────────────────────────────────────────── */
    QComboBox {{
        background-color: {c["input_bg"]};
        color: {c["text"]};
        border: 1px solid {c["input_border"]};
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 28px;
    }}
    QComboBox:focus {{ border-color: {c["input_focus"]}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {c["accent"]};
        selection-color: #ffffff;
    }}

    /* ── TabWidget ─────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: none;
        background-color: transparent;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {c["text_sec"]};
        padding: 10px 20px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 13px;
    }}
    QTabBar::tab:selected {{
        color: {c["accent"]};
        border-bottom: 2px solid {c["accent"]};
        font-weight: 700;
    }}
    QTabBar::tab:hover {{
        color: {c["text"]};
        background-color: {c["surface2"]};
    }}

    /* ── Cards (QFrame[class="card"]) ──────────────────────────── */
    QFrame[class="card"] {{
        background-color: {c["card"]};
        border: 1px solid {c["border"]};
        border-radius: 10px;
    }}
    QFrame[class="card"]:hover {{
        background-color: {c["card_hover"]};
        border-color: {c["accent"]};
    }}

    /* ── Sidebar ───────────────────────────────────────────────── */
    QFrame[class="sidebar"] {{
        background-color: {c["sidebar"]};
        border-right: 1px solid {c["divider"]};
    }}
    QPushButton[class="sidebar-item"] {{
        background-color: transparent;
        color: {c["text_sec"]};
        text-align: left;
        padding: 10px 14px;
        border: none;
        border-radius: 7px;
        font-size: 13px;
    }}
    QPushButton[class="sidebar-item"]:hover {{
        background-color: {c["sb_hover"]};
        color: {c["text"]};
    }}
    QPushButton[class="sidebar-item"][selected="true"] {{
        background-color: {c["sb_selected"]};
        color: {c["accent"]};
        font-weight: 700;
    }}

    /* ── Dividers ──────────────────────────────────────────────── */
    QFrame[class="divider-h"] {{
        background-color: {c["divider"]};
        max-height: 1px; min-height: 1px;
    }}
    QFrame[class="divider-v"] {{
        background-color: {c["divider"]};
        max-width: 1px; min-width: 1px;
    }}

    /* ── ToolTip ───────────────────────────────────────────────── */
    QToolTip {{
        background-color: {c["tooltip_bg"]};
        color: {c["tooltip_text"]};
        border: 1px solid {c["border_h"]};
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 12px;
    }}

    /* ── ProgressBar ───────────────────────────────────────────── */
    QProgressBar {{
        background-color: {c["surface2"]};
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {c["accent"]};
        border-radius: 4px;
    }}

    /* ── CheckBox ──────────────────────────────────────────────── */
    QCheckBox {{
        color: {c["text"]};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border: 2px solid {c["border_h"]};
        border-radius: 4px;
        background-color: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {c["accent"]};
        border-color: {c["accent"]};
    }}

    /* ── Dialog ────────────────────────────────────────────────── */
    QDialog {{
        background-color: {c["surface"]};
        border-radius: 12px;
    }}

    /* ── StatusBar ─────────────────────────────────────────────── */
    QStatusBar {{
        background-color: {c["sidebar"]};
        color: {c["text_sec"]};
        border-top: 1px solid {c["divider"]};
        font-size: 12px;
    }}

    /* ── Menu ──────────────────────────────────────────────────── */
    QMenu {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 8px 24px;
        color: {c["text"]};
    }}
    QMenu::item:selected {{
        background-color: {c["accent"]};
        color: #ffffff;
        border-radius: 4px;
    }}

    /* ── GroupBox ──────────────────────────────────────────────── */
    QGroupBox {{
        font-weight: 600;
        font-size: 13px;
        color: {c["text_sec"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        margin-top: 14px;
        padding-top: 22px;
        background-color: {c["surface"]};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        left: 10px;
        color: {c["accent"]};
    }}

    /* ── ListWidget ────────────────────────────────────────────── */
    QListWidget {{
        background-color: {c["surface"]};
        border: 1px solid {c["border"]};
        border-radius: 8px;
        padding: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 10px 12px;
        border-radius: 6px;
        color: {c["text"]};
    }}
    QListWidget::item:hover {{
        background-color: {c["surface2"]};
    }}
    QListWidget::item:selected {{
        background-color: {c["accent"]};
        color: #ffffff;
    }}
    """


# ── ThemeManager ─────────────────────────────────────────────────────────────

class ThemeManager(QObject):
    """Reactive theme engine.

    - Watches ``theme.json`` with QFileSystemWatcher for live hot-reload
    - Emits ``themeChanged`` so any subscriber can refresh colours
    - Maintains the current colour token dict for synchronous reads
    """

    themeChanged = Signal()  # §2: "Subscription and Polish" pattern

    # Singleton-ish: modules that import `theme_manager` get the same instance
    _instance: "ThemeManager | None" = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True

        self._dark: bool = True
        self._accent: str | None = None
        self.colors: dict[str, str] = {}

        # File watcher for hot-reload
        self._watcher = QFileSystemWatcher()
        self._theme_file: str | None = None
        self._watcher.fileChanged.connect(self._on_file_changed)

        # Apply default palette immediately
        self._rebuild_colors()

    # ── Public API ───────────────────────────────────────────────

    def set_mode(self, dark: bool) -> None:
        """Switch between dark and light mode and emit themeChanged."""
        self._dark = dark
        self._rebuild_colors()
        self._apply_to_app()
        self.themeChanged.emit()

    def set_accent(self, hex_color: str) -> None:
        """Override the accent/brand colour and emit themeChanged."""
        self._accent = hex_color
        self._rebuild_colors()
        self._apply_to_app()
        self.themeChanged.emit()

    def set_theme_file(self, path: str) -> None:
        """Register an external JSON file for hot-reload (§1)."""
        if self._theme_file:
            self._watcher.removePath(self._theme_file)
        self._theme_file = path
        if os.path.exists(path):
            self._watcher.addPath(path)
            self._load_from_file(path)

    def apply(self, app: QApplication | None = None) -> None:
        """Apply the current stylesheet to the QApplication."""
        self._apply_to_app(app)

    def get_color(self, token: str, fallback: str = "#FF6428") -> str:
        """Return a design-token colour for use in QPainter code (§2)."""
        return self.colors.get(token, fallback)

    @property
    def is_dark(self) -> bool:
        return self._dark

    # ── Internal ─────────────────────────────────────────────────

    def _rebuild_colors(self) -> None:
        base = dict(NEUTRAL_DARK if self._dark else NEUTRAL_LIGHT)
        if self._accent:
            l, d = _derive_accent_variants(self._accent)
            base["accent"]   = self._accent
            base["accent_l"] = l
            base["accent_d"] = d
            base["input_focus"] = self._accent
        self.colors = base

    def _apply_to_app(self, app: QApplication | None = None) -> None:
        target = app or QApplication.instance()
        if target:
            target.setStyleSheet(_generate_stylesheet(self.colors))

    def _on_file_changed(self, path: str) -> None:
        """QFileSystemWatcher callback: reload JSON and propagate."""
        # Some editors write-and-replace (file is briefly missing)
        if not os.path.exists(path):
            return
        # Re-watch (some editors unwatch on save)
        self._watcher.addPath(path)
        self._load_from_file(path)

    def _load_from_file(self, path: str) -> None:
        """Parse theme.json and merge overrides (§1)."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mode_key = "neutral_dark" if self._dark else "neutral_light"
            overrides: dict = data.get(mode_key, {})
            if overrides:
                self.colors.update(overrides)
                self._apply_to_app()
                self.themeChanged.emit()
        except Exception:
            pass  # Never crash on a bad JSON edit


# ── Module-level singleton ────────────────────────────────────────────────────
# Import this from anywhere: `from app.qt.themes.theme import theme_manager`
theme_manager = ThemeManager()


# ── Legacy helpers (backwards compat) ────────────────────────────────────────

def get_colors(dark: bool = True) -> dict[str, str]:
    """Return a copy of the current colour dictionary."""
    return dict(NEUTRAL_DARK if dark else NEUTRAL_LIGHT)


def apply_theme(
    app: QApplication,
    dark: bool = True,
    accent_color: str | None = None,
) -> None:
    """Convenience wrapper — updates the singleton and applies."""
    theme_manager._dark = dark
    if accent_color:
        theme_manager._accent = accent_color
    theme_manager._rebuild_colors()
    theme_manager._apply_to_app(app)


# Keep old colour dicts available for components that import them directly
DARK_COLORS  = NEUTRAL_DARK
LIGHT_COLORS = NEUTRAL_LIGHT
