from collections.abc import Callable

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPainter, QColor, QFontMetrics
from PySide6.QtWidgets import QWidget, QToolTip


class HeatmapChart(QWidget):
    DAYS = 7
    HOURS = 24

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[tuple[int, int, int]] = []
        self._grid: list[list[int]] = [[0 for _ in range(self.HOURS)] for _ in range(self.DAYS)]
        self._max_count = 0
        self._hover_cell: tuple[int, int] | None = None
        self._tooltip_formatter: Callable[[int, int, int], str] | None = None
        self.setMouseTracking(True)
        self.setMinimumSize(560, 200)

    def set_tooltip_formatter(self, fmt: Callable[[int, int, int], str] | None) -> None:
        """Set a callable (day, hour, count) -> str for localized tooltips."""
        self._tooltip_formatter = fmt

    def set_day_labels(self, labels: list[str]) -> None:
        """Set localized day labels for the Y-axis (7 strings)."""
        self._day_labels = list(labels)
        self.update()

    def set_data(self, data: list[tuple[int, int, int]]) -> None:
        """data: list of (weekday: 0-6, start_hour: 0-23, count: int)"""
        self._data = data
        self._grid = [[0 for _ in range(self.HOURS)] for _ in range(self.DAYS)]
        for weekday, hour, count in data:
            if 0 <= weekday < self.DAYS and 0 <= hour < self.HOURS:
                self._grid[weekday][hour] = count
        self._max_count = max((c for _, _, c in data), default=0)
        self.update()

    def set_colors(self, surface: str, accent: str) -> None:
        self._surface_color = surface
        self._accent_color = accent
        self.update()

    def _build_tooltip(self, day: int, hour: int) -> str:
        count = self._grid[day][hour]
        if self._tooltip_formatter:
            return self._tooltip_formatter(day, hour, count)
        # Fallback English
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return f"{day_names[day]}, {hour}:00 — {count} sessions"

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self._data:
            self._hover_cell = None
            QToolTip.hideText()
            super().mouseMoveEvent(event)
            return

        rect = self.rect()
        left_pad = 40
        top_pad = 24
        right_pad = 8
        bottom_pad = 8
        chart_w = max(rect.width() - left_pad - right_pad, 1)
        chart_h = max(rect.height() - top_pad - bottom_pad, 1)
        cell_w = chart_w / self.HOURS
        cell_h = chart_h / self.DAYS

        x = event.pos().x() - left_pad
        y = event.pos().y() - top_pad
        col = int(x // cell_w)
        row = int(y // cell_h)

        if 0 <= row < self.DAYS and 0 <= col < self.HOURS:
            self._hover_cell = (row, col)
            QToolTip.showText(self.mapToGlobal(event.pos()), self._build_tooltip(row, col), self)
        else:
            self._hover_cell = None
            QToolTip.hideText()
        self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hover_cell = None
        QToolTip.hideText()
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        left_pad = 40
        top_pad = 24
        right_pad = 8
        bottom_pad = 8
        chart_w = max(rect.width() - left_pad - right_pad, 1)
        chart_h = max(rect.height() - top_pad - bottom_pad, 1)
        cell_w = chart_w / self.HOURS
        cell_h = chart_h / self.DAYS

        # Background
        surface = getattr(self, "_surface_color", None)
        if surface:
            p.fillRect(rect, QColor(surface))

        day_labels = getattr(self, "_day_labels", None) or ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        font = p.font()
        font.setPointSize(8)
        p.setFont(font)
        fm = QFontMetrics(font)

        # Draw day labels
        for i, label in enumerate(day_labels):
            y = top_pad + int((i + 0.5) * cell_h)
            p.setPen(QColor(getattr(self, "_accent_color", "#888888")))
            p.drawText(4, y + fm.ascent() // 2 - 2, label)

        max_val = max(self._max_count, 1)
        accent = QColor(getattr(self, "_accent_color", "#3B82F6"))

        for row in range(self.DAYS):
            for col in range(self.HOURS):
                count = self._grid[row][col]
                x = left_pad + int(col * cell_w)
                y = top_pad + int(row * cell_h)
                w = int((col + 1) * cell_w) - int(col * cell_w)
                h = int((row + 1) * cell_h) - int(row * cell_h)

                intensity = count / max_val
                col_val = QColor(accent)
                col_val.setAlphaF(0.08 + intensity * 0.92)

                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(col_val)
                p.drawRoundedRect(x + 1, y + 1, w - 2, h - 2, 2, 2)

                if self._hover_cell == (row, col):
                    p.setPen(QColor("#FFFFFF"))
                    p.setBrush(Qt.BrushStyle.NoBrush)
                    p.drawRoundedRect(x + 1, y + 1, w - 2, h - 2, 2, 2)

        # Hour labels (every 4 hours)
        for hour in range(0, self.HOURS, 4):
            x = left_pad + int(hour * cell_w)
            p.setPen(QColor(getattr(self, "_accent_color", "#888888")))
            p.drawText(x, top_pad - 4, f"{hour:02d}")

        p.end()
