from __future__ import annotations

import re

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from app.qt.themes.theme import theme_manager


_RGBA_RE = re.compile(
    r"rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*([0-1](?:\.\d+)?)\s*\)",
    re.IGNORECASE,
)


def _to_qcolor(value: str, fallback_alpha: float) -> QColor:
    match = _RGBA_RE.fullmatch((value or "").strip())
    if match:
        r, g, b, a = match.groups()
        color = QColor(int(r), int(g), int(b))
        color.setAlphaF(max(0.0, min(1.0, float(a))))
        return color

    color = QColor(0, 0, 0)
    color.setAlphaF(fallback_alpha)
    return color


def apply_elevation(widget: QWidget, level: int = 1, hovered: bool = False) -> None:
    """Apply a subtle shadow elevation style to a widget."""
    level = 2 if level >= 2 else 1
    token = "elevation_2" if level == 2 else "elevation_1"
    fallback_alpha = 0.28 if level == 2 else 0.18
    color = _to_qcolor(theme_manager.get_color(token), fallback_alpha)

    if hovered:
        color.setAlphaF(min(1.0, color.alphaF() * 1.25))

    blur = 26 if level == 2 else 16
    if hovered:
        blur += 4
    y_offset = 4 if level == 2 else 2
    if hovered:
        y_offset += 1

    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsDropShadowEffect):
        effect = QGraphicsDropShadowEffect(widget)
        widget.setGraphicsEffect(effect)

    effect.setBlurRadius(float(blur))
    effect.setOffset(0, float(y_offset))
    effect.setColor(color)
