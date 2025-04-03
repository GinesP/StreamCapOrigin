
import multiprocessing
import os

import flet as ft
from screeninfo import get_monitors

from app.app_manager import App, execute_dir
from app.ui.components.progress_overlay import ProgressOverlay


def main(page: ft.Page):
    page.title = "StreamCap"
    page.theme_mode = ft.ThemeMode.LIGHT

    screens = get_monitors()
    if screens:
        screen = screens[0]
        screen_width = screen.width
        screen_height = screen.height
        page.window.width = int(screen_width * 0.65)
        page.window.height = int(screen_height * 0.65)

    page.window.icon = os.path.join(execute_dir, "assets", "icon.ico")
    page.window.center()
    app = App(page)

    progress_overlay = ProgressOverlay()
    page.overlay.append(progress_overlay.overlay)

    def route_change(e):
        tr = ft.TemplateRoute(e.route)
        if tr.match("/"):
            page.run_task(app.switch_page, "home")
        elif tr.match("/settings"):
            page.run_task(app.switch_page, "settings")
        elif tr.match("/about"):
            page.run_task(app.switch_page, "about")
        else:
            page.go("/")

    async def on_window_event(e):
        if e.data == "close":
            progress_overlay.show()
            page.update()
            await app.cleanup()
            page.window.destroy()

    page.window.prevent_close = True
    page.window.on_event = on_window_event
    page.on_route_change = route_change
    page.update()
    route_change(ft.RouteChangeEvent(route=page.route))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    ft.app(target=main, assets_dir="assets")
