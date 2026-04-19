from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFontDatabase, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton

try:
    from PySide6.QtSvg import QSvgRenderer
except Exception:  # pragma: no cover - optional dependency path
    QSvgRenderer = None


_ICON_FONT_CANDIDATES = [
    "Segoe Fluent Icons",
    "Segoe MDL2 Assets",
]

_GLYPHS = {
    "home": "\uE80F",
    "recordings": "\uE7F4",
    "settings": "\uE713",
    "logs": "\uE9D9",
    "about": "\uE946",
    "theme_dark": "\uE708",
    "theme_light": "\uE706",
    "collapse": "\uE014",
    "expand": "\uE015",
    "refresh": "\uE72C",
    "add": "\uE710",
    "play": "\uE768",
    "stop": "\uE71A",
    "grid": "\uECA5",
    "list": "\uE8FD",
    "folder": "\uE8B7",
    "preview": "\uE8A7",
    "edit": "\uE70F",
    "info": "\uE946",
    "delete": "\uE74D",
    "success": "\uE73E",
    "error": "\uEA39",
    "warning": "\uE814",
}

_FALLBACK = {
    "home": "⌂",
    "recordings": "▦",
    "settings": "⚙",
    "logs": "☰",
    "about": "i",
    "theme_dark": "◐",
    "theme_light": "◑",
    "collapse": "«",
    "expand": "»",
    "refresh": "↻",
    "add": "+",
    "play": "▶",
    "stop": "■",
    "grid": "⊞",
    "list": "≣",
    "folder": "⌂",
    "preview": "◉",
    "edit": "✎",
    "info": "i",
    "delete": "×",
    "success": "✓",
    "error": "×",
    "warning": "!",
}

_SVG_MAP = {
    "home": "home.svg",
    "recordings": "recordings.svg",
    "settings": "settings.svg",
    "logs": "logs.svg",
    "about": "info.svg",
    "theme_dark": "moon.svg",
    "theme_light": "sun.svg",
    "collapse": "chevron-left.svg",
    "expand": "chevron-right.svg",
    "refresh": "refresh.svg",
    "add": "add.svg",
    "play": "play.svg",
    "stop": "stop.svg",
    "grid": "grid.svg",
    "list": "list.svg",
    "folder": "folder.svg",
    "preview": "preview.svg",
    "edit": "edit.svg",
    "info": "info.svg",
    "delete": "delete.svg",
    "success": "success.svg",
    "error": "error.svg",
    "warning": "warning.svg",
}

_ICON_DIR = Path(__file__).resolve().parents[3] / "assets" / "icons" / "ui"


def icon_font_family() -> str:
    if QGuiApplication.instance() is None:
        return "Segoe UI"
    families = set(QFontDatabase.families())
    for family in _ICON_FONT_CANDIDATES:
        if family in families:
            return family
    return "Segoe UI"


def icon_glyph(name: str) -> str:
    if QGuiApplication.instance() is None:
        return _FALLBACK.get(name, "•")
    families = set(QFontDatabase.families())
    has_icon_font = any(f in families for f in _ICON_FONT_CANDIDATES)
    if has_icon_font and name in _GLYPHS:
        return _GLYPHS[name]
    return _FALLBACK.get(name, "•")


def icon_svg_path(name: str) -> Path | None:
    file_name = _SVG_MAP.get(name)
    if not file_name:
        return None
    path = _ICON_DIR / file_name
    return path if path.exists() else None


def _render_svg(path: Path, size: int) -> QPixmap:
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    if QSvgRenderer is None:
        icon = QIcon(str(path))
        return icon.pixmap(size, size)

    renderer = QSvgRenderer(str(path))
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


def icon_pixmap(name: str, size: int = 18, color: str | QColor | None = None) -> QPixmap:
    if QGuiApplication.instance() is None:
        return QPixmap()

    path = icon_svg_path(name)
    if path is None:
        return QPixmap()

    pix = _render_svg(path, size)
    if pix.isNull() or color is None:
        return pix

    tint = QColor(color) if not isinstance(color, QColor) else color
    if not tint.isValid():
        return pix

    painter = QPainter(pix)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pix.rect(), tint)
    painter.end()
    return pix


def apply_button_icon(
    button: QPushButton,
    name: str,
    size: int = 18,
    color: str | QColor | None = None,
    fallback_text: bool = True,
) -> None:
    pix = icon_pixmap(name, size=size, color=color)
    if pix.isNull():
        if fallback_text:
            button.setText(icon_glyph(name))
        return

    button.setIcon(QIcon(pix))
    button.setIconSize(QSize(size, size))
    button.setText("")


def apply_label_icon(
    label: QLabel,
    name: str,
    size: int = 18,
    color: str | QColor | None = None,
    fallback_text: bool = True,
) -> None:
    pix = icon_pixmap(name, size=size, color=color)
    if pix.isNull():
        if fallback_text:
            label.setText(icon_glyph(name))
        return

    label.setPixmap(pix)
    label.setText("")
