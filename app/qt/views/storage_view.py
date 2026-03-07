"""
Qt Storage View for StreamCap.

A file browser for recorded streams.
Allows navigating folders and opening the video player.
"""

import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFrame
)
from PySide6.QtGui import QIcon, QFont

from app.utils.logger import logger


class QtStorageView(QWidget):
    """
    Storage view: Browse and manage recorded video files.
    """

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.root_path = self.app.settings.get_video_save_path()
        self.current_path = self.root_path
        
        self._ = {}
        self._load_language()
        
        self._setup_ui()
        self._update_file_list()

    def _load_language(self):
        """Load localized strings."""
        language = self.app.language_manager.language
        for key in ("storage_page", "base"):
            self._.update(language.get(key, {}))

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        # Header
        header = QVBoxLayout()
        title = QLabel(self._.get("manage_storage", "Storage"))
        title.setProperty("class", "heading")
        header.addWidget(title)
        
        # Path breadcrumb
        self.path_label = QLabel()
        self.path_label.setProperty("class", "secondary")
        self.path_label.setWordWrap(True)
        header.addWidget(self.path_label)
        
        main_layout.addLayout(header)

        # Actions row (Back button)
        self.nav_row = QHBoxLayout()
        self.back_btn = QPushButton(f"  {self._.get('go_back', 'Go Back')}")
        self.back_btn.setProperty("class", "secondary")
        self.back_btn.setFixedWidth(120)
        self.back_btn.clicked.connect(self._navigate_up)
        self.nav_row.addWidget(self.back_btn)
        self.nav_row.addStretch()
        
        main_layout.addLayout(self.nav_row)

        # File List
        self.file_list = QListWidget()
        self.file_list.setSpacing(2)
        self.file_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: 1px solid palette(dark);
                border-radius: 8px;
                padding: 10px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-radius: 6px;
                color: palette(text);
            }}
            QListWidget::item:hover {{
                background-color: palette(highlight);
                color: white;
            }}
            QListWidget::item:selected {{
                background-color: palette(highlight);
                color: white;
            }}
        """)
        main_layout.addWidget(self.file_list)

    def _update_file_list(self):
        """Scan current_path and update the UI."""
        self.file_list.clear()
        self.path_label.setText(f"{self._.get('current_path', 'Current Path')}: {self.current_path}")
        
        # Enable/Disable back button
        self.back_btn.setEnabled(self.current_path != self.root_path)

        if not os.path.exists(self.current_path):
            self._show_empty("Path does not exist")
            return

        try:
            items = []
            with os.scandir(self.current_path) as it:
                for entry in it:
                    items.append((entry.name, entry.is_dir(), entry.path))
            
            # Sort: folders first, then alphabetical
            items.sort(key=lambda x: (-x[1], x[0].lower()))

            if not items:
                self._show_empty(self._.get("empty_recording_folder", "Empty Folder"))
                return

            for name, is_dir, full_path in items:
                icon = "📁 " if is_dir else "📄 "
                item = QListWidgetItem(f"{icon} {name}")
                item.setData(Qt.ItemDataRole.UserRole, (is_dir, full_path))
                self.file_list.addItem(item)
                
        except Exception as e:
            logger.error(f"Error listing directory: {e}")
            self._show_empty("Error loading files")

    def _show_empty(self, message):
        item = QListWidgetItem(message)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_list.addItem(item)

    def _on_item_double_clicked(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data: return
        
        is_dir, full_path = data
        if is_dir:
            self.current_path = full_path
            self._update_file_list()
        else:
            # Open Video Player (lazy creation on first use)
            player = self.app.main_window.get_video_player()
            self.app.event_bus.run_task(player.preview_video, full_path)

    def _navigate_up(self):
        if self.current_path != self.root_path:
            self.current_path = os.path.dirname(self.current_path)
            self._update_file_list()
