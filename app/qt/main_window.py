"""
Main Qt window for StreamCap.

This is the Qt equivalent of main.py + app_manager.py.
It provides the application shell: sidebar + content area.
"""

import asyncio
import sys

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QIcon, QFont, QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.qt.navigation.sidebar import Sidebar
from app.qt.themes.theme import apply_theme, DARK_COLORS, LIGHT_COLORS
from app.qt.views.recordings_view import QtRecordingsView
from app.qt.views.settings_view import QtSettingsView


class MainWindow(QMainWindow):
    """
    The main application window.

    Provides:
    - Left sidebar navigation
    - Stacked content area (one widget per page)
    - Theme toggling (dark/light)
    """

    MIN_WIDTH = 950
    MIN_HEIGHT = 600
    WINDOW_TITLE = "StreamCap"

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(QSize(self.MIN_WIDTH, self.MIN_HEIGHT))
        self.resize(1200, 750)

        self._dark_mode = self.app.settings.user_config.get("theme_mode", "dark") == "dark"
        self._pages: dict[str, QWidget] = {}

        self._setup_ui()
        self._apply_theme()

    # ── UI Setup ─────────────────────────────────────────────────────

    def _setup_ui(self):
        """Build the main layout: sidebar | divider | content stack."""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self.app)
        self.sidebar.page_changed.connect(self._on_page_changed)
        self.sidebar.theme_btn.clicked.connect(self._toggle_theme)
        main_layout.addWidget(self.sidebar)

        # Register EventBus listeners
        self.app.event_bus.subscribe("language_changed", self._on_language_changed)

        # Vertical divider
        divider = QFrame()
        divider.setProperty("class", "divider-v")
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setFixedWidth(1)
        main_layout.addWidget(divider)

        # Content stack
        self.content_stack = QStackedWidget()
        self.content_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.content_stack)

        # Register pages
        self._register_pages()

    def _register_pages(self):
        """Register all pages in the content stack."""
        # Migrated views
        self.register_page("recordings", QtRecordingsView(self.app))
        self.register_page("settings", QtSettingsView(self.app))
        
        # Placeholders
        page_names = ["home", "storage", "about"]
        for name in page_names:
            page = self._create_placeholder(name)
            self.register_page(name, page)

        # Show recordings by default for now to check card loading
        self.show_page("recordings")

    def _create_placeholder(self, name: str) -> QWidget:
        """Create a simple placeholder widget for a page not yet migrated."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(f"📦  {name.capitalize()} Page")
        label.setProperty("class", "heading")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        sub = QLabel("This page will be migrated from Flet to Qt.")
        sub.setProperty("class", "secondary")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(sub)

        return widget

    # ── Page Management ──────────────────────────────────────────────

    def register_page(self, name: str, widget: QWidget):
        """Register a page widget into the content stack."""
        if name in self._pages:
            old = self._pages[name]
            index = self.content_stack.indexOf(old)
            self.content_stack.removeWidget(old)
            old.deleteLater()

        self.content_stack.addWidget(widget)
        self._pages[name] = widget

    def show_page(self, name: str):
        """Switch the visible page in the content stack."""
        if name in self._pages:
            self.content_stack.setCurrentWidget(self._pages[name])
            self.sidebar.select_page(name)

    def _on_page_changed(self, name: str):
        """Handle sidebar navigation click."""
        self.show_page(name)

    # ── Events ───────────────────────────────────────────────────────

    def _on_language_changed(self, topic, language_data):
        """Update the UI when the language changes."""
        sidebar_labels = language_data.get("record_sidebar", {})
        keys_map = {
            "home": "home",
            "recordings": "recordings",
            "settings": "settings",
            "storage": "storage",
            "about": "about"
        }
        translated = {page_name: sidebar_labels[key] for key, page_name in keys_map.items() if key in sidebar_labels}
        self.sidebar.update_labels(translated)

    # ── Theme ────────────────────────────────────────────────────────

    def _toggle_theme(self):
        """Toggle between dark and light mode."""
        self._dark_mode = not self._dark_mode
        self._apply_theme()

    def _apply_theme(self):
        """Apply the current theme to the application."""
        app = QApplication.instance()
        if app:
            apply_theme(app, dark=self._dark_mode)
        emoji = "☀️" if self._dark_mode else "🌙"
        label = "Light" if self._dark_mode else "Dark"
        self.sidebar.set_theme_text(f"{emoji}  {label}")

    @property
    def is_dark_mode(self) -> bool:
        return self._dark_mode

    # ── Window Events ────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent):
        """Handle window close: cleanup before exit."""
        event.accept()

def run_qt_app():
    # Deprecated for main_qt.py approach
    pass
