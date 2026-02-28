"""
Qt Theme system for StreamCap.

Provides dark and light themes using Qt StyleSheets (QSS),
replacing the Flet theme system.
"""

from PySide6.QtGui import QColor, QPalette, QFont
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


# ── Color Palettes ───────────────────────────────────────────────────

DARK_COLORS = {
    "background": "#1e1e2e",
    "surface": "#282840",
    "surface_variant": "#313148",
    "card": "#2a2a3d",
    "card_hover": "#32324a",
    "primary": "#7c6ff7",
    "primary_light": "#9d93f9",
    "primary_dark": "#5a4fd4",
    "secondary": "#4fc3f7",
    "accent": "#f06292",
    "text": "#e0e0e0",
    "text_secondary": "#a0a0b0",
    "text_muted": "#707085",
    "border": "#3a3a55",
    "divider": "#2e2e45",
    "success": "#66bb6a",
    "warning": "#ffa726",
    "error": "#ef5350",
    "info": "#42a5f5",
    "scrollbar": "#3a3a55",
    "scrollbar_hover": "#50507a",
    "input_bg": "#252540",
    "input_border": "#3a3a55",
    "input_focus": "#7c6ff7",
    "sidebar_bg": "#1a1a2e",
    "sidebar_item_hover": "#2a2a45",
    "sidebar_item_selected": "#35355a",
    "tooltip_bg": "#3a3a55",
    "tooltip_text": "#e0e0e0",
}

LIGHT_COLORS = {
    "background": "#f5f5f8",
    "surface": "#ffffff",
    "surface_variant": "#f0f0f5",
    "card": "#ffffff",
    "card_hover": "#f8f8ff",
    "primary": "#5c6bc0",
    "primary_light": "#8e99d4",
    "primary_dark": "#3949ab",
    "secondary": "#00acc1",
    "accent": "#e91e63",
    "text": "#2c2c2c",
    "text_secondary": "#5a5a6e",
    "text_muted": "#9e9eb0",
    "border": "#dcdce5",
    "divider": "#e8e8f0",
    "success": "#43a047",
    "warning": "#ef6c00",
    "error": "#d32f2f",
    "info": "#1976d2",
    "scrollbar": "#c0c0d0",
    "scrollbar_hover": "#a0a0b5",
    "input_bg": "#fafafe",
    "input_border": "#dcdce5",
    "input_focus": "#5c6bc0",
    "sidebar_bg": "#eeeef5",
    "sidebar_item_hover": "#e0e0ec",
    "sidebar_item_selected": "#d5d5e8",
    "tooltip_bg": "#424252",
    "tooltip_text": "#ffffff",
}


# ── Status Colors (shared between themes) ───────────────────────────

STATUS_COLORS = {
    "recording": "#ef5350",
    "living": "#66bb6a",
    "offline": "#9e9e9e",
    "error": "#ff7043",
    "stopped": "#78909c",
}

QUEUE_COLORS = {
    "fast": "#66bb6a",
    "medium": "#ffa726",
    "slow": "#ef5350",
}


def get_colors(dark: bool = True) -> dict[str, str]:
    """Return the color dictionary for the given theme mode."""
    return DARK_COLORS if dark else LIGHT_COLORS


# ── StyleSheet Generation ────────────────────────────────────────────

def generate_stylesheet(colors: dict[str, str]) -> str:
    """Generate the full application stylesheet from a color dictionary."""
    return f"""
    /* ── Global ─────────────────────────────────────────── */
    QMainWindow, QWidget {{
        background-color: {colors["background"]};
        color: {colors["text"]};
        font-family: "Segoe UI", "Inter", "Roboto", sans-serif;
        font-size: 13px;
    }}

    /* ── Scroll Areas ───────────────────────────────────── */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {colors["scrollbar"]};
        min-height: 40px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {colors["scrollbar_hover"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {colors["scrollbar"]};
        min-width: 40px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {colors["scrollbar_hover"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ── Labels ─────────────────────────────────────────── */
    QLabel {{
        color: {colors["text"]};
        background: transparent;
    }}
    QLabel[class="secondary"] {{
        color: {colors["text_secondary"]};
    }}
    QLabel[class="muted"] {{
        color: {colors["text_muted"]};
        font-size: 12px;
    }}
    QLabel[class="heading"] {{
        font-size: 20px;
        font-weight: 600;
    }}
    QLabel[class="subheading"] {{
        font-size: 15px;
        font-weight: 500;
        color: {colors["text_secondary"]};
    }}

    /* ── Buttons ────────────────────────────────────────── */
    QPushButton {{
        background-color: {colors["primary"]};
        color: #ffffff;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        font-weight: 500;
        font-size: 13px;
    }}
    QPushButton:hover {{
        background-color: {colors["primary_light"]};
    }}
    QPushButton:pressed {{
        background-color: {colors["primary_dark"]};
    }}
    QPushButton:disabled {{
        background-color: {colors["border"]};
        color: {colors["text_muted"]};
    }}
    QPushButton[class="secondary"] {{
        background-color: transparent;
        color: {colors["primary"]};
        border: 1px solid {colors["primary"]};
    }}
    QPushButton[class="secondary"]:hover {{
        background-color: {colors["primary"]};
        color: #ffffff;
    }}
    QPushButton[class="danger"] {{
        background-color: {colors["error"]};
    }}
    QPushButton[class="danger"]:hover {{
        background-color: #c62828;
    }}
    QPushButton[class="icon"] {{
        background-color: transparent;
        border: none;
        padding: 6px;
        border-radius: 4px;
    }}
    QPushButton[class="icon"]:hover {{
        background-color: {colors["surface_variant"]};
    }}

    /* ── Inputs ─────────────────────────────────────────── */
    QLineEdit, QTextEdit {{
        background-color: {colors["input_bg"]};
        color: {colors["text"]};
        border: 1px solid {colors["input_border"]};
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        selection-background-color: {colors["primary"]};
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border-color: {colors["input_focus"]};
    }}

    /* ── ComboBox ───────────────────────────────────────── */
    QComboBox {{
        background-color: {colors["input_bg"]};
        color: {colors["text"]};
        border: 1px solid {colors["input_border"]};
        border-radius: 6px;
        padding: 6px 12px;
        min-height: 28px;
    }}
    QComboBox:focus {{
        border-color: {colors["input_focus"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {colors["primary"]};
        selection-color: #ffffff;
    }}

    /* ── TabWidget ──────────────────────────────────────── */
    QTabWidget::pane {{
        border: none;
        background-color: transparent;
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {colors["text_secondary"]};
        padding: 10px 18px;
        border: none;
        border-bottom: 2px solid transparent;
        font-size: 13px;
    }}
    QTabBar::tab:selected {{
        color: {colors["primary"]};
        border-bottom: 2px solid {colors["primary"]};
        font-weight: 600;
    }}
    QTabBar::tab:hover {{
        color: {colors["text"]};
        background-color: {colors["surface_variant"]};
    }}

    /* ── Cards (QFrame) ────────────────────────────────── */
    QFrame[class="card"] {{
        background-color: {colors["card"]};
        border: 1px solid {colors["border"]};
        border-radius: 10px;
    }}
    QFrame[class="card"]:hover {{
        background-color: {colors["card_hover"]};
        border-color: {colors["primary"]};
    }}

    /* ── Sidebar ───────────────────────────────────────── */
    QFrame[class="sidebar"] {{
        background-color: {colors["sidebar_bg"]};
        border-right: 1px solid {colors["divider"]};
    }}
    QPushButton[class="sidebar-item"] {{
        background-color: transparent;
        color: {colors["text_secondary"]};
        text-align: left;
        padding: 12px 16px;
        border: none;
        border-radius: 8px;
        font-size: 13px;
    }}
    QPushButton[class="sidebar-item"]:hover {{
        background-color: {colors["sidebar_item_hover"]};
        color: {colors["text"]};
    }}
    QPushButton[class="sidebar-item"][selected="true"] {{
        background-color: {colors["sidebar_item_selected"]};
        color: {colors["primary"]};
        font-weight: 600;
    }}

    /* ── Dividers ───────────────────────────────────────── */
    QFrame[class="divider-h"] {{
        background-color: {colors["divider"]};
        max-height: 1px;
        min-height: 1px;
    }}
    QFrame[class="divider-v"] {{
        background-color: {colors["divider"]};
        max-width: 1px;
        min-width: 1px;
    }}

    /* ── ToolTip ────────────────────────────────────────── */
    QToolTip {{
        background-color: {colors["tooltip_bg"]};
        color: {colors["tooltip_text"]};
        border: 1px solid {colors["border"]};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
    }}

    /* ── Progress Bar ──────────────────────────────────── */
    QProgressBar {{
        background-color: {colors["surface_variant"]};
        border: none;
        border-radius: 4px;
        height: 6px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: {colors["primary"]};
        border-radius: 4px;
    }}

    /* ── CheckBox ───────────────────────────────────────── */
    QCheckBox {{
        color: {colors["text"]};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {colors["border"]};
        border-radius: 4px;
        background-color: transparent;
    }}
    QCheckBox::indicator:checked {{
        background-color: {colors["primary"]};
        border-color: {colors["primary"]};
    }}

    /* ── Dialog ─────────────────────────────────────────── */
    QDialog {{
        background-color: {colors["surface"]};
        border-radius: 12px;
    }}

    /* ── StatusBar ──────────────────────────────────────── */
    QStatusBar {{
        background-color: {colors["surface"]};
        color: {colors["text_secondary"]};
        border-top: 1px solid {colors["divider"]};
        font-size: 12px;
    }}

    /* ── Menu ───────────────────────────────────────────── */
    QMenu {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        padding: 4px 0;
    }}
    QMenu::item {{
        padding: 8px 24px;
        color: {colors["text"]};
    }}
    QMenu::item:selected {{
        background-color: {colors["primary"]};
        color: #ffffff;
        border-radius: 4px;
    }}

    /* ── GroupBox ───────────────────────────────────────── */
    QGroupBox {{
        font-weight: 600;
        font-size: 14px;
        color: {colors["primary"]};
        border: 1px solid {colors["border"]};
        border-radius: 8px;
        margin-top: 15px;
        padding-top: 25px;
        background-color: {colors["surface"]};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        left: 10px;
    }}
    """


# ── Apply Theme ──────────────────────────────────────────────────────

def apply_theme(app: QApplication, dark: bool = True, accent_color: str | None = None):
    """Apply the selected theme to the entire application.

    Args:
        app: The QApplication instance.
        dark: True for dark mode, False for light mode.
        accent_color: Optional hex color override for the primary/accent color.
    """
    colors = get_colors(dark)

    if accent_color:
        colors = dict(colors)  # shallow copy
        colors["primary"] = accent_color
        # Derive light/dark variants
        qc = QColor(accent_color)
        colors["primary_light"] = qc.lighter(120).name()
        colors["primary_dark"] = qc.darker(120).name()
        colors["input_focus"] = accent_color

    stylesheet = generate_stylesheet(colors)
    app.setStyleSheet(stylesheet)
