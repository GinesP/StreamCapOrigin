import os
from pathlib import Path

import flet as ft

from ...utils.logger import logger
from ..base_page import PageBase as BasePage


class StoragePage(BasePage):
    def __init__(self, app):
        super().__init__(app)
        self.page_name = "storage"
        self.root_path = app.settings.get_video_save_path()
        self.current_path = self.root_path
        self._ = {}
        self.load_language()
        self.path_display = ft.Text(
            self._["storage_path"] + ": " + self.current_path,
            size=14,
            color=ft.colors.GREY_600
        )
        self.file_list = ft.ListView(expand=True)
        self.content = ft.Column(controls=[self.path_display, self.file_list])

    async def load(self):
        self.app.content_area.controls = [self.content]
        self.app.content_area.update()
        await self.update_file_list()

    def load_language(self):
        language = self.app.language_manager.language
        for key in ("storage_page", "base"):
            self._.update(language.get(key, {}))

    async def update_file_list(self):
        self.path_display.value = self._["current_path"] + ":" + self.current_path
        self.file_list.controls.clear()

        if not os.path.exists(self.current_path):
            self.file_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.icons.FOLDER_OPEN),
                                ft.Text(self._["empty_recording_folder"], size=16, weight=ft.FontWeight.BOLD)
                            ],
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        padding=20
                    ),
                    elevation=2,
                    margin=10,
                    width=400
                )
            )
            self.file_list.update()
            return

        if self.current_path != self.root_path:
            parent = ft.ElevatedButton(
                self._["go_back"],
                on_click=lambda e: self.app.page.run_task(self.navigate_to_parent)
            )
            self.file_list.controls.append(parent)

        for item in sorted(os.listdir(self.current_path)):
            full_path = os.path.join(self.current_path, item)
            if os.path.isdir(full_path):
                btn = ft.ElevatedButton(
                    f"📁 {item}",
                    on_click=lambda e, path=full_path: self.app.page.run_task(self.navigate_to, path)
                )
            else:
                btn = ft.ElevatedButton(
                    f"📄 {item}",
                    on_click=lambda e, path=full_path: self.app.page.run_task(self.preview_file, path)
                )
            self.file_list.controls.append(btn)

        self.file_list.update()

    async def navigate_to(self, path):
        self.current_path = path
        self.path_display.value = self._["current_path"] + ":" + self.current_path
        await self.update_file_list()
        self.content.update()

    async def navigate_to_parent(self):
        self.current_path = os.path.dirname(self.current_path)
        self.path_display.value = self._["current_path"] + ":" + self.current_path
        await self.update_file_list()
        self.content.update()

    async def preview_file(self, file_path):
        video_extensions = ['.mp4', '.mov', '.mkv', '.ts', '.flv', '.mp3', '.m4a', '.wav', '.aac', '.wma']
        if Path(file_path).suffix.lower() in video_extensions:

            def close_dialog(_):
                dialog.open = False
                self.app.dialog_area.update()

            video = ft.Video(
                width=800,
                height=450,
                playlist=[ft.VideoMedia(file_path)],
                autoplay=True
            )

            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text(self._["previewing"] + ":" + os.path.basename(file_path)),
                content=video,
                actions=[ft.TextButton(self._["close"], on_click=close_dialog)],
                actions_alignment=ft.MainAxisAlignment.END
            )
            dialog.open = True
            self.app.dialog_area.content = dialog
            self.app.dialog_area.update()
        else:
            logger.warning(f"unsupported file type: {Path(file_path).suffix.lower()}")
            await self.app.snack_bar.show_snack_bar(self._["unsupported_file_type"] + ":" + os.path.basename(file_path))
