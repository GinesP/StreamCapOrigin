import argparse
import multiprocessing
import os

import flet as ft
from dotenv import load_dotenv
from screeninfo import get_monitors

from app.app_manager import App, execute_dir
from app.ui.components.progress_overlay import ProgressOverlay
from app.utils.logger import logger

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 6006
WINDOW_SCALE = 0.65
ASSETS_DIR = "assets"


def setup_window(page: ft.Page, is_web: bool) -> None:
    page.window.icon = os.path.join(execute_dir, ASSETS_DIR, "icon.ico")
    page.window.center()
    page.window.to_front()
    page.skip_task_bar = True
    page.always_on_top = True
    page.focused = True

    if not is_web:
        try:
            screen = get_monitors()[0]
            page.window.width = int(screen.width * WINDOW_SCALE)
            page.window.height = int(screen.height * WINDOW_SCALE)
        except IndexError:
            logger.warning("No monitors detected, using default window size.")


def get_route_handler() -> dict[str, str]:
    return {
        "/": "home",
        "/home": "home",
        "/settings": "settings",
        "/about": "about",
    }


def handle_route_change(page: ft.Page, app: App) -> callable:
    route_map = get_route_handler()

    def route_change(e: ft.RouteChangeEvent) -> None:
        tr = ft.TemplateRoute(e.route)
        page_name = route_map.get(tr.route)
        if page_name:
            page.run_task(app.switch_page, page_name)
        else:
            logger.warning(f"Unknown route: {e.route}, redirecting to /")
            page.go("/")

    return route_change


def handle_window_event(page: ft.Page, app: App, progress_overlay: 'ProgressOverlay') -> callable:

    async def on_window_event(e: ft.ControlEvent) -> None:
        if e.data == "close":
            progress_overlay.show()
            page.update()
            try:
                await app.cleanup()
            except Exception as ex:
                logger.error(f"Cleanup failed: {ex}")
            finally:
                page.window.destroy()

    return on_window_event


def handle_disconnect(page: ft.Page) -> callable:
    """Handle disconnection for web mode."""

    def disconnect(_: ft.ControlEvent) -> None:
        page.pubsub.unsubscribe_all()

    return disconnect


def main(page: ft.Page) -> None:

    page.title = "StreamCap"
    page.theme_mode = ft.ThemeMode.LIGHT

    is_web = args.web or platform == "web"
    setup_window(page, is_web)

    app = App(page)
    progress_overlay = ProgressOverlay()
    page.overlay.append(progress_overlay.overlay)

    page.on_route_change = handle_route_change(page, app)
    page.window.prevent_close = True
    page.window.on_event = handle_window_event(page, app, progress_overlay)

    if is_web:
        page.on_disconnect = handle_disconnect(page)

    page.update()
    page.on_route_change(ft.RouteChangeEvent(route=page.route))


if __name__ == "__main__":
    load_dotenv()
    platform = os.getenv("PLATFORM")
    default_host = os.getenv("HOST", DEFAULT_HOST)
    default_port = int(os.getenv("PORT", DEFAULT_PORT))

    parser = argparse.ArgumentParser(description="Run the Flet app with optional web mode.")
    parser.add_argument("--web", action="store_true", help="Run the app in web mode")
    parser.add_argument("--host", type=str, default=default_host, help=f"Host address (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port number (default: {default_port})")
    args = parser.parse_args()

    multiprocessing.freeze_support()
    if args.web or platform == "web":
        logger.debug("Running in web mode on http://" + args.host + ":" + str(args.port))
        ft.app(
            target=main,
            view=ft.AppView.WEB_BROWSER,
            host=args.host,
            port=args.port,
            assets_dir=ASSETS_DIR,
            use_color_emoji=True,
        )

    else:
        ft.app(target=main, assets_dir=ASSETS_DIR)
