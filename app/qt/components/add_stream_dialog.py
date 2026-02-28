"""
Qt Add Stream Dialog for StreamCap.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFrame,
    QMessageBox
)

from app.utils.logger import logger
from app.models.recording.recording_model import Recording
from app.core.platforms.platform_handlers import get_platform_info


class QtAddStreamDialog(QDialog):
    def __init__(self, app_context, parent=None):
        super().__init__(parent)
        self.app = app_context
        self.setWindowTitle("Add New Stream")
        self.setMinimumWidth(450)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        # Title
        title = QLabel("Add New Stream")
        title.setProperty("class", "heading")
        layout.addWidget(title)

        # URL Input
        layout.addWidget(QLabel("Stream URL (Twitch, YouTube, etc.)"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://twitch.tv/example")
        layout.addWidget(self.url_input)

        # Quality Selection
        layout.addWidget(QLabel("Preferred Quality"))
        self.quality_combo = QComboBox()
        # Map indices to VideoQuality standard keys if needed
        self.qualities = {
            "Best": "OD",
            "1080p60": "UHD",
            "720p60": "HD",
            "480p": "SD",
            "Audio Only": "AUDIO"
        }
        self.quality_combo.addItems(list(self.qualities.keys()))
        layout.addWidget(self.quality_combo)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.add_btn = QPushButton("Add Stream")
        self.add_btn.setProperty("class", "primary")
        self.add_btn.clicked.connect(self._on_add_clicked)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.add_btn)
        
        layout.addLayout(btn_layout)

    def _on_add_clicked(self):
        url = self.url_input.text().strip()
        quality_label = self.quality_combo.currentText()
        quality_key = self.qualities.get(quality_label, "OD")
        
        if not url:
            return

        # Validate platform
        platform, platform_key = get_platform_info(url)
        if not platform:
            QMessageBox.warning(self, "Unsupported Platform", f"The platform for this URL is not supported yet: {url}")
            return

        # Check for duplicates
        if any(rec.url == url for rec in self.app.record_manager.recordings):
            QMessageBox.information(self, "Duplicate Stream", "This stream is already in your list.")
            return

        logger.info(f"Adding stream: {url} with quality {quality_key}")
        
        # Create Recording object
        # We use streamer_name as URL tail if not specified, similar to Flet version
        streamer_name = url.split("/")[-1] or "New Stream"
        
        new_rec = Recording(
            url=url,
            streamer_name=streamer_name,
            quality=quality_key,
            monitor_status=True
        )
        
        # Add to manager (async)
        self.app.event_bus.run_task(self.app.record_manager.add_recording, new_rec)
        
        # Publish event
        self.app.event_bus.publish("add", new_rec)
        
        self.accept()
