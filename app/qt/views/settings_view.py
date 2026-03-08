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
        self.restore_btn.clicked.connect(self._on_restore_clicked)
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

    def _on_restore_clicked(self):
        from app.qt.components.confirm_dialog import QtConfirmDialog
        if QtConfirmDialog.confirm(
            self,
            "Confirm Restore",
            "Are you sure you want to restore all settings to their default values?",
            "This will not affect your cookies or accounts.",
            type="warning"
        ):
            self.app.event_bus.run_task(self.settings.restore_default_config)
            
            if hasattr(self.app.main_window, "show_toast"):
                self.app.main_window.show_toast("Settings restored to defaults", "success")
                
            QTimer.singleShot(200, self._load_settings)


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
        
        from PySide6.QtWidgets import QListView
        self.lang_combo = QComboBox()
        self.lang_combo.setView(QListView())
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

        # Folder Naming Rules
        naming_group = SettingsGroup("Folder Naming Rules", "Organize downloads into subfolders.")
        
        self.name_plat = QCheckBox()
        self.name_plat.stateChanged.connect(lambda s: self._save_setting("folder_name_platform", s == Qt.CheckState.Checked.value))
        naming_group.add_setting("Include Platform:", self.name_plat)

        self.name_auth = QCheckBox()
        self.name_auth.stateChanged.connect(lambda s: self._save_setting("folder_name_author", s == Qt.CheckState.Checked.value))
        naming_group.add_setting("Include Author:", self.name_auth)

        self.name_time = QCheckBox()
        self.name_time.stateChanged.connect(lambda s: self._save_setting("folder_name_time", s == Qt.CheckState.Checked.value))
        naming_group.add_setting("Include Date/Time:", self.name_time)

        self.name_title = QCheckBox()
        self.name_title.stateChanged.connect(lambda s: self._save_setting("folder_name_title", s == Qt.CheckState.Checked.value))
        naming_group.add_setting("Include Title:", self.name_title)

        layout.addWidget(naming_group)

        self.quality_combo = QComboBox()
        self.quality_combo.setView(QListView())
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

        # Proxy
        proxy_group = SettingsGroup("Proxy Settings", "Route traffic through a proxy server.")
        self.proxy_enabled = QCheckBox()
        self.proxy_enabled.stateChanged.connect(lambda s: self._save_setting("enable_proxy", s == Qt.CheckState.Checked.value))
        proxy_group.add_setting("Enable Proxy:", self.proxy_enabled)
        
        self.proxy_addr = QLineEdit()
        self.proxy_addr.setPlaceholderText("http://user:pass@host:port")
        self.proxy_addr.textChanged.connect(lambda v: self._save_setting("proxy_address", v))
        proxy_group.add_setting("Proxy Address:", self.proxy_addr)
        layout.addWidget(proxy_group)

        # Advanced / Post-Processing
        adv_group = SettingsGroup("Advanced Recording", "Segmenting and Post-processing.")
        
        self.seg_check = QCheckBox()
        self.seg_check.stateChanged.connect(lambda s: self._save_setting("segmented_recording_enabled", s == Qt.CheckState.Checked.value))
        adv_group.add_setting("Enable Segmented Recording:", self.seg_check)
        
        self.seg_time = QLineEdit()
        self.seg_time.setFixedWidth(80)
        self.seg_time.textChanged.connect(lambda v: self._save_setting("video_segment_time", v))
        adv_group.add_setting("Segment Time (seconds):", self.seg_time)

        self.mp4_check = QCheckBox()
        self.mp4_check.stateChanged.connect(lambda s: self._save_setting("convert_to_mp4", s == Qt.CheckState.Checked.value))
        adv_group.add_setting("Convert to MP4 (FFmpeg):", self.mp4_check)

        self.del_check = QCheckBox()
        self.del_check.stateChanged.connect(lambda s: self._save_setting("delete_original", s == Qt.CheckState.Checked.value))
        adv_group.add_setting("Delete Original (after convert):", self.del_check)
        
        layout.addWidget(adv_group)
        
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

        # Telegram
        tg_group = SettingsGroup("Telegram Bot", "Get alerts via Telegram.")
        self.tg_token = QLineEdit()
        self.tg_token.setPlaceholderText("Token (5555:AAAA...)")
        self.tg_token.textChanged.connect(lambda v: self._save_setting("telegram_bot_token", v))
        tg_group.add_setting("Bot Token:", self.tg_token)
        
        self.tg_chat = QLineEdit()
        self.tg_chat.setPlaceholderText("Chat ID (-100123...)")
        self.tg_chat.textChanged.connect(lambda v: self._save_setting("telegram_chat_id", v))
        tg_group.add_setting("Chat ID:", self.tg_chat)
        layout.addWidget(tg_group)

        # Generic Webhook
        hook_group = SettingsGroup("Discord / Webhook", "Route alerts to a Discord channel or custom URL.")
        self.hook_url = QLineEdit()
        self.hook_url.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.hook_url.textChanged.connect(lambda v: self._save_setting("discord_webhook_url", v))
        hook_group.add_setting("Webhook URL:", self.hook_url)
        layout.addWidget(hook_group)
        
        return self._create_scroll_wrapper(content)

    def _create_cookies_tab(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        cookie_group = SettingsGroup("Platform Cookies", "JSON-format cookies for authenticated stream extraction.")
        
        self.cookie_fields = {}
        platforms = ["douyin", "tiktok", "twitch", "youtube", "bilibili"]
        
        for p in platforms:
            field = QLineEdit()
            field.setPlaceholderText(f"Enter {p} cookies...")
            field.textChanged.connect(lambda v, plat=p: self._save_cookie(plat, v))
            self.cookie_fields[p] = field
            
            if p == "tiktok":
                row = QHBoxLayout()
                row.addWidget(field)
                btn = QPushButton("Import JSON")
                btn.setFixedWidth(100)
                btn.clicked.connect(lambda _, f=field, plat=p: self._on_browse_cookie_clicked(f, plat))
                row.addWidget(btn)
                wrapper = QWidget()
                wrapper.setLayout(row)
                cookie_group.add_setting(f"{p.capitalize()}:", wrapper)
            else:
                cookie_group.add_setting(f"{p.capitalize()}:", field)
            
        layout.addWidget(cookie_group)
        return self._create_scroll_wrapper(content)

    def _on_browse_cookie_clicked(self, target_line_edit, plat):
        from PySide6.QtWidgets import QFileDialog
        from app.utils.cookie_importer import load_json_cookies, convert_json_to_cookie_string
        
        path, _ = QFileDialog.getOpenFileName(self, "Select JSON Cookie File", "", "JSON Files (*.json);;Text Files (*.txt);;All Files (*)")
        if path:
            try:
                cookies_json = load_json_cookies(path)
                if cookies_json:
                    cookie_string = convert_json_to_cookie_string(cookies_json)
                    if cookie_string:
                        target_line_edit.setText(cookie_string)
                        self._save_cookie(plat, cookie_string) # Automatically save
                        
                        if hasattr(self.app.main_window, "show_toast"):
                            self.app.main_window.show_toast(f"Cookies imported successfully from {path.split('/')[-1]}", "success")
                    else:
                        if hasattr(self.app.main_window, "show_toast"):
                            self.app.main_window.show_toast("Failed to convert cookies from JSON.", "error")
                else:
                    if hasattr(self.app.main_window, "show_toast"):
                        self.app.main_window.show_toast("No cookies found in file.", "error")
            except Exception as e:
                logger.error(f"Error importing cookies: {e}")
                if hasattr(self.app.main_window, "show_toast"):
                    self.app.main_window.show_toast(f"Error importing cookies: {e}", "error")

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
        
        self.name_plat.setChecked(s.get_config_value("folder_name_platform", False))
        self.name_auth.setChecked(s.get_config_value("folder_name_author", False))
        self.name_time.setChecked(s.get_config_value("folder_name_time", False))
        self.name_title.setChecked(s.get_config_value("folder_name_title", False))
        
        idx_q = self.quality_combo.findText(s.get_config_value("record_quality", "OD"))
        if idx_q >= 0: self.quality_combo.setCurrentIndex(idx_q)
        self.title_check.setChecked(s.get_config_value("filename_includes_title", False))
        self.loop_input.setText(str(s.get_config_value("loop_time_seconds", "60")))
        
        # Proxy
        self.proxy_enabled.setChecked(s.get_config_value("enable_proxy", False))
        self.proxy_addr.setText(s.get_config_value("proxy_address", ""))
        
        # Advanced
        self.seg_check.setChecked(s.get_config_value("segmented_recording_enabled", False))
        self.seg_time.setText(str(s.get_config_value("video_segment_time", "3600")))
        self.mp4_check.setChecked(s.get_config_value("convert_to_mp4", False))
        self.del_check.setChecked(s.get_config_value("delete_original", False))
        
        # Push
        self.notif_enabled.setChecked(s.get_config_value("system_notification_enabled", False))
        self.start_notif.setChecked(s.get_config_value("stream_start_notification_enabled", False))
        self.end_notif.setChecked(s.get_config_value("stream_end_notification_enabled", False))
        self.notif_title.setText(s.get_config_value("custom_notification_title", "StreamCap"))
        
        # Telegram & Webhook
        self.tg_token.setText(s.get_config_value("telegram_bot_token", ""))
        self.tg_chat.setText(s.get_config_value("telegram_chat_id", ""))
        self.hook_url.setText(s.get_config_value("discord_webhook_url", ""))
        
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
