"""
Qt Sidebar navigation for StreamCap.

Replaces the Flet NavigationSidebar / LeftNavigationMenu with a
PySide6 implementation using QPushButtons inside a QVBoxLayout.
"""

from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpacerItem,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SidebarItem(QPushButton):
    """A single navigation item in the sidebar."""

    def __init__(self, icon_char: str, label: str, name: str, parent=None):
        super().__init__(parent)
        self.name = name
        self._selected = False

        self.setProperty("class", "sidebar-item")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(44)

        # Layout: icon + label
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(12)

        self.icon_label = QLabel(icon_char)
        self.icon_label.setFixedWidth(24)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel(label)
        self.text_label.setStyleSheet("background: transparent; font-size: 13px;")
        layout.addWidget(self.text_label)

        layout.addStretch()

    @property
    def selected(self) -> bool:
        return self._selected

    @selected.setter
    def selected(self, value: bool):
        self._selected = value
        self.setProperty("selected", "true" if value else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_label(self, text: str):
        """Update the displayed label text (for language changes)."""
        self.text_label.setText(text)


class Sidebar(QFrame):
    """
    Left navigation sidebar with navigation items.

    Signals:
        page_changed(str): Emitted when a navigation item is clicked,
                           with the page name as payload.
    """

    page_changed = Signal(str)

    # Navigation items definition: (icon, default_label, page_name)
    NAV_ITEMS = [
        ("🏠", "Home", "home"),
        ("📺", "Recordings", "recordings"),
        ("⚙️", "Settings", "settings"),
        ("📁", "Storage", "storage"),
        ("ℹ️", "About", "about"),
    ]

    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app = app_context
        self.setProperty("class", "sidebar")
        self.setFixedWidth(180)
        self.setMinimumHeight(400)

        self._items: list[SidebarItem] = []
        self._selected_index = 0

        self._setup_ui()
        self._load_translations()
        self._select_item(0)

    def _load_translations(self):
        """Load translated labels from the app context."""
        try:
            language = self.app.language_manager.language
            sidebar_labels = language.get("record_sidebar", {})
            
            # Map of sidebar keys to page names
            keys_map = {
                "home": "home",
                "recordings": "recordings",
                "settings": "settings",
                "storage": "storage",
                "about": "about"
            }
            
            translated = {}
            for key, page_name in keys_map.items():
                if key in sidebar_labels:
                    translated[page_name] = sidebar_labels[key]
            
            if translated:
                self.update_labels(translated)
        except Exception:
            pass

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(2)

        # ── App Logo / Title ────────────────────────
        logo_container = QWidget()
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(12, 8, 12, 16)

        title = QLabel("StreamCap")
        title.setProperty("class", "heading")
        title.setStyleSheet("font-size: 18px; font-weight: 700; background: transparent;")
        logo_layout.addWidget(title)
        layout.addWidget(logo_container)

        # ── Navigation Items ────────────────────────
        for icon_char, label, name in self.NAV_ITEMS:
            item = SidebarItem(icon_char, label, name, self)
            item.clicked.connect(lambda checked=False, n=name: self._on_item_clicked(n))
            self._items.append(item)
            layout.addWidget(item)

        layout.addStretch()

        # ── Theme Toggle ────────────────────────────
        self.theme_btn = QPushButton("🌙  Dark")
        self.theme_btn.setProperty("class", "sidebar-item")
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.setFixedHeight(44)
        layout.addWidget(self.theme_btn)

    def _on_item_clicked(self, name: str):
        """Handle navigation item click."""
        for i, item in enumerate(self._items):
            if item.name == name:
                self._select_item(i)
                break
        self.page_changed.emit(name)

    def _select_item(self, index: int):
        """Visually select the item at the given index."""
        for i, item in enumerate(self._items):
            item.selected = (i == index)
        self._selected_index = index

    def select_page(self, name: str):
        """Programmatically select a page by name."""
        for i, item in enumerate(self._items):
            if item.name == name:
                self._select_item(i)
                return

    def update_labels(self, labels: dict[str, str]):
        """Update sidebar labels for i18n.

        Args:
            labels: Dict mapping page name → translated label.
                    e.g. {"home": "Inicio", "recordings": "Grabaciones", ...}
        """
        for item in self._items:
            if item.name in labels:
                item.set_label(labels[item.name])

    def set_theme_text(self, text: str):
        """Update the theme toggle button label."""
        self.theme_btn.setText(text)
