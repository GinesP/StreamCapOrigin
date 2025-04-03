import os

import flet as ft

from . import InstallationManager, execute_dir
from .core.config_manager import ConfigManager
from .core.language_manager import LanguageManager
from .core.record_manager import RecordingManager
from .process_manager import AsyncProcessManager
from .ui.components.recording_card import RecordingCardManager
from .ui.components.show_snackbar import ShowSnackBar
from .ui.navigation.sidebar import LeftNavigationMenu, NavigationSidebar
from .ui.views.about_view import AboutPage
from .ui.views.home_view import HomePage
from .ui.views.settings_view import SettingsPage
from .utils import utils


class App:
    def __init__(self, page: ft.Page):
        self.install_progress = None
        self.page = page
        self.run_path = execute_dir
        self.assets_dir = os.path.join(execute_dir, "assets")
        self.process_manager = AsyncProcessManager()
        self.config_manager = ConfigManager(self.run_path)
        self.content_area = ft.Column(
            controls=[],
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

        self.settings = SettingsPage(self)
        self.language_manager = LanguageManager(self)
        self.about = AboutPage(self)
        self.home = HomePage(self)
        self.pages = self.initialize_pages()
        self.language_code = self.settings.language_code
        self.sidebar = NavigationSidebar(self)
        self.left_navigation_menu = LeftNavigationMenu(self)

        self.page.snack_bar_area = ft.Container()
        self.dialog_area = ft.Container()
        self.complete_page = ft.Row(
            expand=True,
            controls=[
                self.left_navigation_menu,
                ft.VerticalDivider(width=1),
                self.content_area,
                self.dialog_area,
                self.page.snack_bar_area,
            ]
        )
        self.page.add(self.complete_page)
        self.snack_bar = ShowSnackBar(self.page)
        self.subprocess_start_up_info = utils.get_startup_info()
        self.record_card_manager = RecordingCardManager(self)
        self.record_manager = RecordingManager(self)
        self.current_page = None
        self._loading_page = False
        self.recording_enabled = True
        self.install_manager = InstallationManager(self)
        self.page.run_task(self.install_manager.check_env)
        self.page.run_task(self.record_manager.check_free_space)

    def initialize_pages(self):
        return {
            "settings": self.settings,
            "home": HomePage(self),
            "about": AboutPage(self),
        }

    async def switch_page(self, page_name):
        if self._loading_page:
            return

        self._loading_page = True

        try:
            await self.clear_content_area()
            if page := self.pages.get(page_name):
                await self.settings.is_changed()
                self.current_page = page
                await page.load()
        finally:
            self._loading_page = False

    async def clear_content_area(self):
        self.content_area.clean()
        self.content_area.update()

    async def cleanup(self):
        await self.process_manager.cleanup()

    def add_ffmpeg_process(self, process):
        self.process_manager.add_process(process)
