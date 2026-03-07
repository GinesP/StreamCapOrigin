"""
Qt About View for StreamCap.

Displays project information, version updates, license, and developer details.
"""

import os
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QFont, QDesktopServices, QColor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QSizePolicy
)

from app.utils.logger import logger


class InfoCard(QFrame):
    """A styled container for information sections."""
    def __init__(self, title, content_layout=None, parent=None):
        super().__init__(parent)
        self.setObjectName("infoCard")
        self.setStyleSheet("""
            QFrame#infoCard {
                background-color: #2b2b3b;
                border-radius: 12px;
                border: 1px solid #3d3d5d;
            }
            QLabel#cardTitle {
                color: #a0a0c0;
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 10px;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.layout.addWidget(self.title_label)
        
        if content_layout:
            self.layout.addLayout(content_layout)

class QtAboutView(QWidget):
    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self._ = {}
        self.about_config = {}
        
        self.load_language()
        self._setup_ui()

    def load_language(self):
        language = self.app.language_manager.language
        self._ = language.get("about_page", {})
        self.about_config = self.app.config_manager.load_about_config()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 1. Header (Title & Version)
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(self._.get("about_project", "About Project"))
        title_label.setStyleSheet("font-size: 32px; font-weight: 800; color: #7c4dff;")
        header_layout.addWidget(title_label)
        
        v_updates = self.about_config.get("version_updates", [{}])[0]
        ver_info = (
            f"{self._.get('ui_version', 'UI Version')}: {v_updates.get('version', 'N/A')} | "
            f"{self._.get('kernel_version', 'Kernel Version')}: {v_updates.get('kernel_version', 'N/A')} | "
            f"{self._.get('license', 'License')}: {self.about_config.get('open_source_license', 'GPL')}"
        )
        ver_label = QLabel(ver_info)
        ver_label.setStyleSheet("color: #8888aa; font-size: 13px;")
        header_layout.addWidget(ver_label)
        
        main_layout.addLayout(header_layout)

        # Scroll Area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setSpacing(20)
        self.content_layout.setContentsMargins(0, 0, 10, 0)

        # 2. Introduction Card
        intro_text = self.about_config.get("introduction", {}).get(self.app.language_code, "")
        intro_label = QLabel(intro_text)
        intro_label.setWordWrap(True)
        intro_label.setStyleSheet("color: #bbbbcc; font-size: 14px; line-height: 1.5;")
        
        card_intro = InfoCard(self._.get("introduction", "Introduction"))
        card_intro.layout.addWidget(intro_label)
        self.content_layout.addWidget(card_intro)

        # 3. Features Card
        features_layout = QHBoxLayout()
        features_layout.setSpacing(15)
        
        feature_defs = [
            (self._.get("support_platforms", "Platforms"), "🌐"),
            (self._.get("customize_recording", "Customize"), "⚙️"),
            (self._.get("open_source", "Open Source"), "💡"),
            (self._.get("automatic_transcoding", "Transcode"), "🔄"),
            (self._.get("status_push", "Notifications"), "🔔"),
        ]
        
        for name, icon in feature_defs:
            f_box = QVBoxLayout()
            f_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            i_label = QLabel(icon)
            i_label.setStyleSheet("font-size: 24px;")
            f_box.addWidget(i_label)
            
            n_label = QLabel(name)
            n_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            n_label.setStyleSheet("font-size: 11px; color: #a0a0c0;")
            n_label.setWordWrap(True)
            f_box.addWidget(n_label)
            
            features_layout.addLayout(f_box)
            
        card_features = InfoCard(self._.get("feature", "Features"), features_layout)
        self.content_layout.addWidget(card_features)

        # 4. Developer & Links Row
        dev_row = QHBoxLayout()
        
        # Dev Info
        dev_col = QVBoxLayout()
        dev_title = QLabel("Hmily")
        dev_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        dev_col.addWidget(dev_title)
        
        dev_sub = QLabel(self._.get("author", "Author / Developer"))
        dev_sub.setStyleSheet("color: #8888aa; font-size: 12px;")
        dev_col.addWidget(dev_sub)
        
        dev_card = InfoCard(self._.get("developer", "Developer"), dev_col)
        dev_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        dev_row.addWidget(dev_card)
        
        # Buttons
        btns_col = QVBoxLayout()
        
        btn_updates = QPushButton("📦 " + self._.get("view_update", "Releases"))
        btn_updates.clicked.connect(lambda: QDesktopServices.openUrl("https://github.com/ihmily/StreamCap/releases"))
        btns_col.addWidget(btn_updates)
        
        btn_docs = QPushButton("📄 " + self._.get("view_docs", "Wiki / Docs"))
        btn_docs.clicked.connect(lambda: QDesktopServices.openUrl("https://github.com/ihmily/StreamCap/wiki"))
        btns_col.addWidget(btn_docs)
        
        btn_check = QPushButton("🔄 " + self.app.language_manager.language.get("update", {}).get("check_update", "Check Updates"))
        btn_check.clicked.connect(self._check_updates)
        btns_col.addWidget(btn_check)
        
        dev_row.addLayout(btns_col)
        self.content_layout.addLayout(dev_row)

        # 5. Changelog Card
        card_updates = InfoCard(self._.get("update", "Updates"))
        for update in v_updates.get("updates", {}).get(self.app.language_code, []):
            u_label = QLabel(f"• {update}")
            u_label.setWordWrap(True)
            u_label.setStyleSheet("color: #8888aa; font-size: 12px; margin-bottom: 4px;")
            card_updates.layout.addWidget(u_label)
            
        self.content_layout.addWidget(card_updates)
        
        self.content_layout.addStretch()
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    async def _check_updates(self):
        logger.info("Checking for updates from About view...")
        # Reusing update checker logic here if needed
        pass
