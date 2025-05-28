import asyncio
import threading
import time

import flet as ft

from ..utils.logger import logger


def _safe_destroy_window(page):
    try:
        page.update()
        to_cancel = asyncio.all_tasks(page.loop)
        if not to_cancel:
            return
        for task in to_cancel:
            task.cancel()
    except Exception as ex:
        logger.error(f"close window error: {ex}")
    finally:
        page.window.destroy()


async def handle_app_close(page: ft.Page, app, save_progress_overlay) -> None:
    _ = {}
    language = app.language_manager.language
    for key in ("app_close_handler", "base"):
        _.update(language.get(key, {}))

    async def close_dialog_dismissed(e):
        app.recording_enabled = False

        # check if there are active recordings
        active_recordings = [p for p in app.process_manager.ffmpeg_processes if p.returncode is None]
        active_recordings_count = len(active_recordings)

        if active_recordings_count > 0:
            save_progress_overlay.show(_["saving_recordings"].format(active_recordings_count=active_recordings_count), 
                                       cancellable=True)
            page.update()

            def close_app():
                try:
                    # adjust wait time based on the number of recordings, at least 2 seconds
                    base_wait_time = max(2, min(active_recordings_count, 10))
                    logger.info(
                        f"waiting for {active_recordings_count} recordings to finish, waiting {base_wait_time} seconds")

                    time.sleep(base_wait_time)

                    # check again if there are active processes
                    remaining = len([p for p in app.process_manager.ffmpeg_processes if p.returncode is None])
                    if remaining > 0:
                        logger.info(f"still {remaining} recordings are not finished, waiting for extra time")
                        time.sleep(min(remaining, 5))

                    time.sleep(0.5)

                except Exception as ex:
                    logger.error(f"close window error: {ex}")
                finally:
                    page.window.destroy()

            threading.Thread(target=close_app, daemon=True).start()
        else:
            _safe_destroy_window(page)

        await close_dialog(e)

    async def close_dialog(_):
        confirm_dialog.open = False
        page.update()

    confirm_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(_["confirm_exit"]),
        content=ft.Text(_["confirm_exit_content"]),
        actions=[
            ft.TextButton(_["cancel"], on_click=close_dialog),
            ft.TextButton(_["confirm"], on_click=close_dialog_dismissed),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    confirm_dialog.open = True
    app.dialog_area.content = confirm_dialog
    page.update()
