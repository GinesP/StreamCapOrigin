from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

from app import bundle_dir, execute_dir


BODY_FONT_FAMILY = "Roboto"
DISPLAY_FONT_FAMILY = "Space Grotesk"


def _font_directories() -> list[Path]:
    candidates = [
        Path(bundle_dir) / "assets" / "fonts",
        Path(execute_dir) / "assets" / "fonts",
        Path(execute_dir) / "tmp",
    ]
    directories: list[Path] = []
    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        directories.append(resolved)
    return directories


def load_app_fonts() -> None:
    loaded_files: set[str] = set()
    for directory in _font_directories():
        for font_path in sorted(directory.glob("*.ttf")):
            key = font_path.name.lower()
            if key in loaded_files:
                continue
            QFontDatabase.addApplicationFont(str(font_path))
            loaded_files.add(key)


def body_font(size: int, weight: QFont.Weight = QFont.Weight.Normal) -> QFont:
    return QFont(BODY_FONT_FAMILY, size, weight)


def display_font(size: int, weight: QFont.Weight = QFont.Weight.Bold) -> QFont:
    return QFont(DISPLAY_FONT_FAMILY, size, weight)
