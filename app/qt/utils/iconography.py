from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import QRectF, QSize, Qt
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
_MAX_PIXMAP_CACHE = 256
_PIXMAP_CACHE: OrderedDict[tuple[str, int, str | None, float, int], QPixmap] = OrderedDict()
_RENDER_COUNT = 0


def _device_pixel_ratio() -> float:
    app = QGuiApplication.instance()
    screen = app.primaryScreen() if app else None
    return round(float(screen.devicePixelRatio()), 2) if screen else 1.0


def _color_key(color: str | QColor | None) -> str | None:
    if color is None:
        return None
    tint = color if isinstance(color, QColor) else QColor(color)
    return tint.name(QColor.NameFormat.HexArgb) if tint.isValid() else None


def clear_icon_cache() -> None:
    """Clear tinted SVG pixmaps after theme/accent changes."""
    _PIXMAP_CACHE.clear()


def icon_cache_stats() -> dict[str, int]:
    """Return lightweight cache diagnostics for optional theme profiling."""
    return {"entries": len(_PIXMAP_CACHE), "renders": _RENDER_COUNT}


def _cache_key(path: Path, size: int, color: str | QColor | None) -> tuple[str, int, str | None, float, int]:
    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0
    return (str(path), size, _color_key(color), _device_pixel_ratio(), mtime_ns)


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


def _render_svg(path: Path, size: int, color: str | QColor | None = None) -> QPixmap:
    global _RENDER_COUNT

    _RENDER_COUNT += 1
    dpr = _device_pixel_ratio()
    physical_size = max(1, round(size * dpr))
    pix = QPixmap(physical_size, physical_size)
    pix.fill(Qt.GlobalColor.transparent)
    if QSvgRenderer is None:
        icon = QIcon(str(path))
        fallback = icon.pixmap(physical_size, physical_size)
        fallback.setDevicePixelRatio(dpr)
        return fallback

    renderer = QSvgRenderer(str(path))
    painter = QPainter(pix)
    renderer.render(painter, QRectF(0, 0, physical_size, physical_size))
    painter.end()

    if color is not None:
        tint = QColor(color) if not isinstance(color, QColor) else color
        if tint.isValid():
            painter = QPainter(pix)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pix.rect(), tint)
            painter.end()

    pix.setDevicePixelRatio(dpr)
    return pix


def icon_pixmap(name: str, size: int = 18, color: str | QColor | None = None) -> QPixmap:
    if QGuiApplication.instance() is None:
        return QPixmap()

    path = icon_svg_path(name)
    if path is None:
        return QPixmap()

    key = _cache_key(path, size, color)
    cached = _PIXMAP_CACHE.get(key)
    if cached is not None:
        _PIXMAP_CACHE.move_to_end(key)
        return QPixmap(cached)

    pix = _render_svg(path, size, color=color)
    if pix.isNull():
        return pix

    _PIXMAP_CACHE[key] = QPixmap(pix)
    if len(_PIXMAP_CACHE) > _MAX_PIXMAP_CACHE:
        _PIXMAP_CACHE.popitem(last=False)
    return QPixmap(pix)


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
