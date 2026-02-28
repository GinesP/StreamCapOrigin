"""
SettingsLogic: Framework-agnostic settings management.

Extracted from settings_view.py to allow both Flet and Qt 
to share the same settings logic and persistence.
"""

import asyncio
import os
from app.utils.logger import logger


class SettingsLogic:
    def __init__(self, app):
        self.app = app
        self.config_manager = self.app.config_manager
        
        # Load initial configurations
        self.user_config = self.config_manager.load_user_config()
        self.language_option = self.config_manager.load_language_config()
        self.default_config = self.config_manager.load_default_config()
        self.cookies_config = self.config_manager.load_cookies_config()
        self.accounts_config = self.config_manager.load_accounts_config()
        
        self.language_code = None
        self.default_language = None
        self.load_language_code()

    def load_language_code(self):
        """Determine the current language code based on user config."""
        try:
            self.default_language, default_language_code = list(self.language_option.items())[0]
            select_language = self.user_config.get("language")
            self.language_code = self.language_option.get(select_language, default_language_code)
        except Exception as e:
            logger.error(f"Failed to load language code: {e}")
            self.language_code = "en"

    def get_config_value(self, key, default=None):
        return self.user_config.get(key, self.default_config.get(key, default))

    def get_cookies_value(self, key, default=""):
        return self.cookies_config.get(key, default)

    def get_accounts_value(self, key, default=None):
        try:
            k1, k2 = key.split("_", maxsplit=1)
            return self.accounts_config.get(k1, {}).get(k2, default)
        except ValueError:
            return default

    async def update_setting(self, key, value):
        """Update a setting and save it."""
        self.user_config[key] = value
        
        # Specific logic for some settings
        if key in ["folder_name_platform", "folder_name_author", "folder_name_time", "folder_name_title"]:
            for recording in self.app.record_manager.recordings:
                recording.recording_dir = None
            await self.app.record_manager.persist_recordings()
            
        if key == "language":
            self.load_language_code()
            if hasattr(self.app, "language_manager"):
                self.app.language_manager.load()
                self.app.language_manager.notify_observers()

        if key == "loop_time_seconds":
            if hasattr(self.app.record_manager, "initialize_dynamic_state"):
                self.app.record_manager.initialize_dynamic_state()
                
        await self.config_manager.save_user_config(self.user_config)
        return True

    async def update_cookie(self, key, value):
        self.cookies_config[key] = value
        await self.config_manager.save_cookies_config(self.cookies_config)

    async def update_account(self, platform, key, value):
        if platform not in self.accounts_config:
            self.accounts_config[platform] = {}
        self.accounts_config[platform][key] = value
        await self.config_manager.save_accounts_config(self.accounts_config)

    def get_video_save_path(self):
        live_save_path = self.get_config_value("live_save_path")
        if not live_save_path:
            live_save_path = os.path.join(self.app.run_path, 'downloads')
        return live_save_path
