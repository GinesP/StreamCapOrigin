"""
Qt Settings View for StreamCap.

Migrates the complex Flet settings page to a modern Qt layout.
Uses SettingsLogic for framework-agnostic data persistence.
Supports tabs for: Recording, Push, Cookies, Accounts.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QPushButton,
    QFrame,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QGroupBox,
    QTabWidget
)

from app.utils.logger import logger


class SettingsGroup(QGroupBox):
    """A visually distinct group of settings with a title and optional description."""
    def __init__(self, title, description="", parent=None):
        super().__init__(parent)
        self.setTitle(title)
        self.setObjectName("settingsGroup")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 30, 20, 20)
        self.layout.setSpacing(15)
        
        if description:
            desc_label = QLabel(description)
            desc_label.setProperty("class", "muted")
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("font-size: 11px; margin-bottom: 10px; color: #888;")
            self.layout.addWidget(desc_label)

    def add_setting(self, label, widget, tooltip=""):
        row = QHBoxLayout()
        row.setSpacing(20)
        
        lbl = QLabel(label)
        lbl.setStyleSheet("font-weight: 500; font-size: 13px;")
        if tooltip:
            lbl.setToolTip(tooltip)
            
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(widget)
        
        self.layout.addLayout(row)


class QtSettingsView(QWidget):
    """
    Main settings view with tabs for Recording, Push, Cookies, and Accounts.
    """

    def __init__(self, app_context):
        super().__init__()
        self.app = app_context
        self.settings = self.app.settings # SettingsLogic instance
        
        self.initial_load = True
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setProperty("class", "heading")
        header.addWidget(title)
        header.addStretch()
        
        self.restore_btn = QPushButton("Restore Defaults")
        self.restore_btn.setProperty("class", "secondary")
        header.addWidget(self.restore_btn)
        
        main_layout.addLayout(header)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setObjectName("settingsTabs")
        
        # 1. Recording Tab
        self.tabs.addTab(self._create_recording_tab(), "Recording")
        
        # 2. Push Tab
        self.tabs.addTab(self._create_push_tab(), "Notifications")
        
        # 3. Cookies Tab
        self.tabs.addTab(self._create_cookies_tab(), "Cookies")
        
        # 4. Accounts Tab
        self.tabs.addTab(self._create_accounts_tab(), "Accounts")
        
        main_layout.addWidget(self.tabs)

    def _create_scroll_wrapper(self, widget):
        """Wraps a widget in a scroll area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setWidget(widget)
        return scroll

    def _create_recording_tab(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(25)
        
        # Basic
        rec_group = SettingsGroup("Basic Settings", "General recording behavior.")
        
        self.lang_combo = QComboBox()
        for lang_name in self.settings.language_option.keys():
            self.lang_combo.addItem(lang_name)
        self.lang_combo.currentTextChanged.connect(lambda v: self._save_setting("language", v))
        rec_group.add_setting("Program Language:", self.lang_combo)
        
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        path_row = QHBoxLayout()
        path_row.addWidget(self.path_input)
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        path_row.addWidget(self.browse_btn)
        path_widget = QWidget()
        path_widget.setLayout(path_row)
        rec_group.add_setting("Save Path:", path_widget)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["OD", "UHD", "HD", "SD", "LD"])
        self.quality_combo.currentTextChanged.connect(lambda v: self._save_setting("record_quality", v))
        rec_group.add_setting("Default Quality:", self.quality_combo)
        
        self.title_check = QCheckBox()
        self.title_check.stateChanged.connect(lambda s: self._save_setting("filename_includes_title", s == Qt.CheckState.Checked.value))
        rec_group.add_setting("Include Title in Filename:", self.title_check)
        
        layout.addWidget(rec_group)
        
        # Monitoring
        monitor_group = SettingsGroup("Monitoring", "Frequency check for live streams.")
        self.loop_input = QLineEdit()
        self.loop_input.setFixedWidth(80)
        self.loop_input.textChanged.connect(lambda v: self._save_setting("loop_time_seconds", v))
        monitor_group.add_setting("Check Interval (seconds):", self.loop_input)
        layout.addWidget(monitor_group)
        
        return self._create_scroll_wrapper(content)

    def _create_push_tab(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(25)
        
        notif_group = SettingsGroup("Push Notifications", "Behavior for start/end stream alerts.")
        
        self.notif_enabled = QCheckBox()
        self.notif_enabled.stateChanged.connect(lambda s: self._save_setting("system_notification_enabled", s == Qt.CheckState.Checked.value))
        notif_group.add_setting("Enable System Notifications:", self.notif_enabled)
        
        self.start_notif = QCheckBox()
        self.start_notif.stateChanged.connect(lambda s: self._save_setting("stream_start_notification_enabled", s == Qt.CheckState.Checked.value))
        notif_group.add_setting("Stream Start Alert:", self.start_notif)
        
        self.end_notif = QCheckBox()
        self.end_notif.stateChanged.connect(lambda s: self._save_setting("stream_end_notification_enabled", s == Qt.CheckState.Checked.value))
        notif_group.add_setting("Stream End Alert:", self.end_notif)
        
        layout.addWidget(notif_group)
        
        custom_group = SettingsGroup("Custom Content", "Personalize alert messages.")
        self.notif_title = QLineEdit()
        self.notif_title.textChanged.connect(lambda v: self._save_setting("custom_notification_title", v))
        custom_group.add_setting("Custom Title:", self.notif_title)
        layout.addWidget(custom_group)
        
        return self._create_scroll_wrapper(content)

    def _create_cookies_tab(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        cookie_group = SettingsGroup("Platform Cookies", "JSON-format cookies for authenticated stream extraction.")
        
        self.cookie_fields = {}
        platforms = ["douyin", "tiktok", "twitch", "youtube", "bilibili", "tiktok_cookie_file"]
        
        for p in platforms:
            field = QLineEdit()
            field.setPlaceholderText(f"Enter {p} cookies...")
            field.textChanged.connect(lambda v, plat=p: self._save_cookie(plat, v))
            cookie_group.add_setting(f"{p.capitalize()}:", field)
            self.cookie_fields[p] = field
            
        layout.addWidget(cookie_group)
        return self._create_scroll_wrapper(content)

    def _create_accounts_tab(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        acc_group = SettingsGroup("Credential Storage", "Usernames and passwords for restricted regions.")
        
        self.acc_fields = {}
        fields = [
            ("sooplive_username", "SoopLive Username"),
            ("sooplive_password", "SoopLive Password")
        ]
        
        for key, label in fields:
            field = QLineEdit()
            if "password" in key: field.setEchoMode(QLineEdit.EchoMode.Password)
            field.textChanged.connect(lambda v, k=key: self._save_account(k, v))
            acc_group.add_setting(f"{label}:", field)
            self.acc_fields[key] = field
            
        layout.addWidget(acc_group)
        return self._create_scroll_wrapper(content)

    def _on_browse_clicked(self):
        from PySide6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(self, "Select Download Directory", self.path_input.text())
        if path:
            self.path_input.setText(path)
            self._save_setting("live_save_path", path)

    def _load_settings(self):
        self.initial_load = True
        s = self.settings
        
        # Recording
        current_lang = s.user_config.get("language")
        idx = self.lang_combo.findText(current_lang if current_lang else "")
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
        self.path_input.setText(s.get_video_save_path())
        idx_q = self.quality_combo.findText(s.get_config_value("record_quality", "OD"))
        if idx_q >= 0: self.quality_combo.setCurrentIndex(idx_q)
        self.title_check.setChecked(s.get_config_value("filename_includes_title", False))
        self.loop_input.setText(str(s.get_config_value("loop_time_seconds", "60")))
        
        # Push
        self.notif_enabled.setChecked(s.get_config_value("system_notification_enabled", False))
        self.start_notif.setChecked(s.get_config_value("stream_start_notification_enabled", False))
        self.end_notif.setChecked(s.get_config_value("stream_end_notification_enabled", False))
        self.notif_title.setText(s.get_config_value("custom_notification_title", "StreamCap"))
        
        # Cookies
        for p, field in self.cookie_fields.items():
            field.setText(s.get_cookies_value(p, ""))
            
        # Accounts
        for k, field in self.acc_fields.items():
            field.setText(s.get_accounts_value(k, ""))
            
        self.initial_load = False

    def _save_setting(self, key, value):
        if self.initial_load: return
        self.app.event_bus.run_task(self.settings.update_setting, key, value)

    def _save_cookie(self, key, value):
        if self.initial_load: return
        self.app.event_bus.run_task(self.settings.update_cookie, key, value)

    def _save_account(self, key, value):
        if self.initial_load: return
        plat, k = key.split("_", 1)
        self.app.event_bus.run_task(self.settings.update_account, plat, k, value)
