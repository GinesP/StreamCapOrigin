import sys

import flet as ft

from .theme import create_dark_theme, create_light_theme


class ThemeManager:
    def __init__(self, app):
        self.page = app.page
        self.custom_font = None
        self.theme_color = None
        self.assets_dir = app.assets_dir
        self.init_fonts()
        self.page.run_task(self.apply_initial_theme)

    def init_fonts(self):
        """Initialize fonts for the application."""
        custom_font = "AlibabaPuHuiTi Light"
        if sys.platform == "darwin":
            custom_font = "AlibabaPuHuiTi Light Mac"

        self.page.fonts = {
            "AlibabaPuHuiTi Light": f"{self.assets_dir}/fonts/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-45-Light.otf",
            "AlibabaPuHuiTi Light Mac": f"{self.assets_dir}/fonts/AlibabaPuHuiTi-2/AlibabaPuHuiTi-2-45-Light-Mac.otf",
        }
        self.custom_font = custom_font

    async def apply_initial_theme(self):
        """Apply initial theme based on saved settings or default to light theme."""
        self.page.theme = create_light_theme(self.custom_font)
        self.page.dark_theme = create_dark_theme(self.custom_font)
        try:
            self.theme_color = await self.page.client_storage.get_async("theme_color")
            if self.theme_color is not None:
                await self.update_theme_color(self.theme_color)
                return
        except Exception:
            pass
        await self.update_theme_color("blue")

    async def update_theme_color(self, color):
        """Update the current theme color scheme and save it."""
        self.page.theme.color_scheme_seed = color
        self.page.theme.color_scheme = ft.ColorScheme(primary=color)
        self.page.update()
        try:    
            await self.page.client_storage.set_async("theme_color", color)
        except Exception:
            pass
