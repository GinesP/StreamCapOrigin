"""
Qt Recording Info Dialog — StreamCap.
Detailed view of stream metadata and intelligence stats.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QWidget,
    QGridLayout
)
from datetime import datetime

class QtRecordingInfoDialog(QDialog):
    def __init__(self, app_context, recording, parent=None):
        super().__init__(parent)
        self.app = app_context
        self.rec = recording
        
        self.setWindowTitle(f"Stream Info — {self.rec.streamer_name}")
        self.setMinimumWidth(450)
        self.setMinimumHeight(500)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Header with Avatar-like circle
        header = QHBoxLayout()
        header.setSpacing(15)
        
        color = "#4CAF50" if self.rec.is_live else "#757575"
        letter = self.rec.streamer_name[0].upper() if self.rec.streamer_name else "?"
        
        avatar = QLabel(letter)
        avatar.setFixedSize(60, 60)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            background: #4A4A6A;
            color: #E1E1E1;
            border-radius: 30px;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid {color};
        """)
        header.addWidget(avatar)
        
        title_v = QVBoxLayout()
        name_lbl = QLabel(self.rec.streamer_name)
        name_lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #E1E1E1;")
        title_v.addWidget(name_lbl)
        
        status_lbl = QLabel(self.rec.status_info or "Idle")
        status_lbl.setStyleSheet(f"color: {color}; font-weight: 600;")
        title_v.addWidget(status_lbl)
        header.addLayout(title_v)
        header.addStretch()
        
        layout.addLayout(header)

        # Content Area (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        container_lay = QVBoxLayout(container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(15)
        
        # 1. Configuration Section
        self._add_section(container_lay, "Configuration", [
            ("URL", self.rec.url),
            ("Platform", getattr(self.rec, "platform", "N/A") or "Unknown"),
            ("Quality", getattr(self.rec, "quality", "OD")),
            ("Format", getattr(self.rec, "record_format", "ts")),
            ("Save Path", getattr(self.rec, "recording_dir", "Default")),
        ])
        
        # 2. Intelligence Section
        last_seen = "Never"
        if getattr(self.rec, "last_seen_live", None):
            try:
                dt = datetime.fromisoformat(self.rec.last_seen_live)
                last_seen = dt.strftime("%Y-%m-%d %H:%M")
            except:
                last_seen = self.rec.last_seen_live

        consistency = getattr(self.rec, "consistency_score", 0.0)
        priority = getattr(self.rec, "priority_score", 0.0)

        self._add_section(container_lay, "Intelligence & Stats", [
            ("Consistency", f"{consistency:.1%}"),
            ("Priority Score", f"{priority:.4f}"),
            ("Last Seen Live", last_seen),
            ("Checks Count", str(getattr(self.rec, "live_check_count", 0))),
            ("Found Live", str(getattr(self.rec, "live_found_count", 0))),
        ])
        
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Footer Buttons
        btns = QHBoxLayout()
        
        folder_btn = QPushButton("Open Folder")
        folder_btn.setProperty("class", "secondary")
        folder_btn.clicked.connect(self._on_open_folder)
        
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "primary")
        close_btn.clicked.connect(self.accept)
        
        btns.addWidget(folder_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        layout.addLayout(btns)

    def _add_section(self, parent_lay, title, items):
        group = QGroupBox(title)
        vlay = QVBoxLayout(group)
        vlay.setContentsMargins(15, 15, 15, 15)
        
        grid = QGridLayout()
        grid.setSpacing(10)
        
        for i, (key, val) in enumerate(items):
            key_lbl = QLabel(f"{key}:")
            key_lbl.setStyleSheet("color: #777; font-weight: 600;")
            val_lbl = QLabel(str(val))
            val_lbl.setWordWrap(True)
            val_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            
            grid.addWidget(key_lbl, i, 0)
            grid.addWidget(val_lbl, i, 1)
        
        grid.setColumnStretch(1, 1)
        vlay.addLayout(grid)
        parent_lay.addWidget(group)

    def _on_open_folder(self):
        path = getattr(self.rec, "recording_dir", None) or self.app.settings.get_video_save_path()
        from app.utils import utils
        utils.open_folder(path)

from PySide6.QtWidgets import QGroupBox
