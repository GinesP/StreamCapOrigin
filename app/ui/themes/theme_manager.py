import sys

import flet as ft

from .theme import create_dark_theme, create_light_theme


class ThemeManager:
    def __init__(self, app):
        self.page = app.page
        self.custom_font = None
        self.assets_dir = app.assets_dir
        self.init_fonts()
        self.apply_initial_theme()

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

    def apply_initial_theme(self):
        """Apply initial theme based on saved settings or default to light theme."""
        self.page.theme = create_light_theme(self.custom_font)
        self.page.dark_theme = create_dark_theme(self.custom_font)

        theme_color = self.page.client_storage.get("theme_color")
        if theme_color is not None:
            self.update_theme_color(theme_color)
        else:
            self.update_theme_color("blue")

    def update_theme_color(self, color):
        """Update the current theme color scheme and save it."""
        self.page.theme.color_scheme_seed = color
        self.page.theme.color_scheme = ft.ColorScheme(primary=color)
        self.page.update()
        self.page.client_storage.set("theme_color", color)
