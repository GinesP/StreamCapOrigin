import asyncio
import os
import time

import flet as ft

from . import execute_dir
from .core.config.config_manager import ConfigManager
from .core.config.language_manager import LanguageManager
from .core.recording.record_manager import RecordingManager
from .core.runtime.process_manager import AsyncProcessManager
from .core.update.update_checker import UpdateChecker
from .initialization.installation_manager import InstallationManager
from .ui.components.business.recording_card import RecordingCardManager
from .ui.components.common.show_snackbar import ShowSnackBar
from .ui.navigation.sidebar import LeftNavigationMenu, NavigationSidebar
from .ui.views.about_view import AboutPage
from .ui.views.home_view import HomePage
from .ui.views.recordings_view import RecordingsPage
from .ui.views.settings_view import SettingsPage
from .ui.views.storage_view import StoragePage
from .utils import utils
from .utils.logger import logger


class App:
    def __init__(self, page: ft.Page):
        self.install_progress = None
        self.page = page
        self.run_path = execute_dir
        self.assets_dir = os.path.join(execute_dir, "assets")
        self.process_manager = AsyncProcessManager()
        self.config_manager = ConfigManager(self.run_path)
        self.is_web_mode = False
        self.auth_manager = None
        self.current_username = None
        self.content_area = ft.Column(
            controls=[],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        self.settings = SettingsPage(self)
        self.language_manager = LanguageManager(self)
        self.language_code = self.settings.language_code
        self.about = AboutPage(self)
        self.recordings = RecordingsPage(self)
        self.home = HomePage(self)
        self.storage = StoragePage(self)
        self.pages = self.initialize_pages()
        self.sidebar = NavigationSidebar(self)
        self.left_navigation_menu = LeftNavigationMenu(self)

        self.complete_page = ft.Row(
            expand=True,
            controls=[
                self.left_navigation_menu,
                ft.VerticalDivider(width=1),
                self.content_area,
            ]
        )
        self.dialog_area = ft.Stack()
        self.page.overlay.append(self.dialog_area)
        self.snack_bar = ShowSnackBar(self)
        self.subprocess_start_up_info = utils.get_startup_info()
        self.record_card_manager = RecordingCardManager(self)
        self.record_manager = RecordingManager(self)
        self.current_page = None
        self._loading_page = False
        self.recording_enabled = True
        self.install_manager = InstallationManager(self)
        self.update_checker = UpdateChecker(self)
        self.page.run_task(self.install_manager.check_env)
        self.page.run_task(self.record_manager.check_free_space)
        self.page.run_task(self._check_for_updates)

    def initialize_pages(self):
        return {
            "settings": self.settings,
            "home": self.home,
            "recordings": self.recordings,
            "storage": self.storage,
            "about": self.about,
        }

    async def on_keyboard(self, e: ft.KeyboardEvent):
        if self.current_page and hasattr(self.current_page, "on_keyboard"):
            await self.current_page.on_keyboard(e)

    async def switch_page(self, page_name):
        if self._loading_page:
            return

        self._loading_page = True
        logger.debug(f"Switching page to: {page_name}")
        try:
            self.content_area.controls.clear()
            self.content_area.update()
            
            if page := self.pages.get(page_name):
                # Timeout safety for potentially slow operations
                try:
                    await asyncio.wait_for(self.settings.is_changed(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Settings save timed out during page switch")
                except Exception as e:
                    logger.error(f"Error in is_changed during switch: {e}")

                self.current_page = page
                
                try:
                    await asyncio.wait_for(page.load(), timeout=10.0)
                    self.content_area.update()
                except asyncio.TimeoutError:
                    logger.error(f"Page load timed out: {page_name}")
                except Exception as e:
                    logger.error(f"Error loading page {page_name}: {e}")
        except Exception as e:
            logger.error(f"Critical error in switch_page: {e}")
        finally:
            self._loading_page = False
            self.page.update()
            logger.debug(f"Finished switching page to: {page_name}")

    async def clear_content_area(self, update=True):
        self.content_area.clean()
        if update:
            self.content_area.update()

    async def cleanup(self):
        try:
            await self.process_manager.cleanup()
        except ConnectionError:
            logger.warning("Connection lost, process may have terminated")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def add_ffmpeg_process(self, process):
        self.process_manager.add_process(process)

    async def _check_for_updates(self):
        """Check for updates when the application starts"""
        try:
            if not self.update_checker.update_config["auto_check"]:
                return
                
            last_check_time = self.settings.user_config.get("last_update_check", 0)
            current_time = time.time()
            check_interval = self.update_checker.update_config["check_interval"]
            
            if current_time - last_check_time >= check_interval:
                update_info = await self.update_checker.check_for_updates()
                self.settings.user_config["last_update_check"] = current_time
                await self.config_manager.save_user_config(self.settings.user_config)

                if update_info.get("has_update", False):
                    await self.update_checker.show_update_dialog(update_info)
        except Exception as e:
            logger.error(f"Update check failed: {e}")

    async def start_periodic_tasks(self):
        """Start all periodic tasks"""
        # The 30s interval is the "heartrate" that allows individual adjustments 
        # (like 60s or 180s) to be checked accurately.
        await self.record_manager.setup_periodic_live_check(30)
