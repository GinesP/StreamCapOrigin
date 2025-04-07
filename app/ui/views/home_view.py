import uuid

import flet as ft

from ...models.recording_model import Recording
from ...utils.logger import logger
from ..base_page import PageBase
from ..components.help_dialog import HelpDialog
from ..components.recording_dialog import RecordingDialog
from ..components.search_dialog import SearchDialog


class HomePage(PageBase):
    def __init__(self, app):
        super().__init__(app)
        self.page_name = "home"
        self.recording_card_area = None
        self.add_recording_dialog = None
        self.app.language_manager.add_observer(self)
        self.load_language()
        self.init()

    def load_language(self):
        language = self.app.language_manager.language
        for key in ("home_page", "video_quality", "base"):
            self._.update(language.get(key, {}))

    def init(self):
        self.recording_card_area = ft.Column(controls=[], spacing=10, expand=True)
        self.add_recording_dialog = RecordingDialog(self.app, self.add_recording)
        self.pubsub_subscribe()

    async def load(self):
        """Load the home page content."""
        self.content_area.controls.extend([self.create_home_title_area(), self.create_home_content_area()])
        self.content_area.update()
        await self.add_record_cards()
        self.page.run_task(self.show_all_cards)
        self.page.on_keyboard_event = self.on_keyboard

    def pubsub_subscribe(self):
        self.app.page.pubsub.subscribe_topic('add', self.subscribe_add_cards)
        self.app.page.pubsub.subscribe_topic('delete_all', self.subscribe_del_all_cards)

    def create_home_title_area(self):
        return ft.Row(
            [
                ft.Text(self._["recording_list"], theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.Icons.SEARCH, tooltip=self._["search"], on_click=self.search_on_click),
                ft.IconButton(icon=ft.Icons.ADD, tooltip=self._["add_record"], on_click=self.add_recording_on_click),
                ft.IconButton(icon=ft.Icons.REFRESH, tooltip=self._["refresh"], on_click=self.refresh_cards_on_click),
                ft.IconButton(
                    icon=ft.Icons.PLAY_ARROW,
                    tooltip=self._["batch_start"],
                    on_click=self.start_monitor_recordings_on_click,
                ),
                ft.IconButton(
                    icon=ft.Icons.STOP, tooltip=self._["batch_stop"], on_click=self.stop_monitor_recordings_on_click
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE_SWEEP,
                    tooltip=self._["batch_delete"],
                    on_click=self.delete_monitor_recordings_on_click,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
        )

    async def filter_recordings(self, query):
        recordings = self.app.record_manager.recordings
        cards_obj = self.app.record_card_manager.cards_obj
        new_ids = {}

        if not query.strip():
            for card in cards_obj.values():
                card["card"].visible = True
        else:
            lower_query = query.strip().lower()
            new_ids = {
                rec.rec_id
                for rec in recordings
                if lower_query in str(rec.to_dict()).lower() or lower_query in rec.display_title
            }

            for card_info in cards_obj.values():
                card_info["card"].visible = card_info["card"].key in new_ids
        self.recording_card_area.update()

        if not new_ids:
            await self.app.snack_bar.show_snack_bar(self._["not_search_result"], duration=2000)
        return new_ids

    def create_home_content_area(self):
        return ft.Column(
            expand=True,
            controls=[
                ft.Divider(height=1),
                ft.Container(
                    content=self.recording_card_area,
                    alignment=ft.alignment.top_left,
                    expand=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    async def add_record_card(self, recording, update=True):
        if recording.rec_id not in self.app.record_card_manager.cards_obj:
            card = await self.app.record_card_manager.create_card(recording)
            self.recording_card_area.controls.append(card)
            self.app.record_card_manager.cards_obj[recording.rec_id]["card"] = card

            recording.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
                recording.scheduled_start_time, recording.monitor_hours)

            if update:
                self.recording_card_area.update()

    async def add_record_cards(self):
        for recording in self.app.record_manager.recordings:
            await self.add_record_card(recording, update=False)
        self.recording_card_area.update()
        if not self.app.record_manager.periodic_task_started:
            self.page.run_task(
                self.app.record_manager.setup_periodic_live_check, self.app.record_manager.loop_time_seconds
            )

    async def show_all_cards(self):
        cards_obj = self.app.record_card_manager.cards_obj
        for card in cards_obj.values():
            card["card"].visible = True
        self.recording_card_area.update()

    async def add_recording(self, recordings_info):
        user_config = self.app.settings.user_config
        logger.info(f"Add items: {len(recordings_info)}")
        for recording_info in recordings_info:
            if recording_info.get("record_format"):
                recording = Recording(
                    rec_id=str(uuid.uuid4()),
                    url=recording_info["url"],
                    streamer_name=recording_info["streamer_name"],
                    quality=recording_info["quality"],
                    record_format=recording_info["record_format"],
                    segment_record=recording_info["segment_record"],
                    segment_time=recording_info["segment_time"],
                    monitor_status=recording_info["monitor_status"],
                    scheduled_recording=recording_info["scheduled_recording"],
                    scheduled_start_time=recording_info["scheduled_start_time"],
                    monitor_hours=recording_info["monitor_hours"],
                    recording_dir=recording_info["recording_dir"],
                )
            else:
                recording = Recording(
                    rec_id=str(uuid.uuid4()),
                    url=recording_info["url"],
                    streamer_name=recording_info["streamer_name"],
                    quality=recording_info["quality"],
                    record_format=user_config.get("video_format", "TS"),
                    segment_record=user_config.get("segmented_recording_enabled", False),
                    segment_time=user_config.get("video_segment_time", "1800"),
                    monitor_status=True,
                    scheduled_recording=user_config.get("scheduled_recording", False),
                    scheduled_start_time=user_config.get("scheduled_start_time"),
                    monitor_hours=user_config.get("monitor_hours"),
                    recording_dir=None,
                )

            recording.loop_time_seconds = int(user_config.get("loop_time_seconds", 300))
            recording.update_title(self._[recording.quality])
            await self.app.record_manager.add_recording(recording)
            self.page.run_task(self.add_record_card, recording, True)
            self.app.page.pubsub.send_others_on_topic("add", recording)

        await self.app.snack_bar.show_snack_bar(self._["add_recording_success_tip"], bgcolor=ft.Colors.GREEN)

    async def search_on_click(self, _e):
        """Open the search dialog when the search button is clicked."""
        search_dialog = SearchDialog(home_page=self)
        search_dialog.open = True
        self.app.dialog_area.content = search_dialog
        self.app.dialog_area.update()

    async def add_recording_on_click(self, _e):
        await self.add_recording_dialog.show_dialog()

    async def refresh_cards_on_click(self, _e):
        cards_obj = self.app.record_card_manager.cards_obj
        recordings = self.app.record_manager.recordings
        new_ids = {rec.rec_id for rec in recordings}
        to_remove = [card for card_id, card in cards_obj.items() if card_id not in new_ids]
        for card in to_remove:
            del cards_obj[card["card"].key]
            self.recording_card_area.controls.remove(card["card"])
        await self.show_all_cards()
        await self.app.snack_bar.show_snack_bar(self._["refresh_success_tip"], bgcolor=ft.Colors.GREEN)

    async def start_monitor_recordings_on_click(self, _):
        await self.app.record_manager.check_free_space()
        if self.app.recording_enabled:
            await self.app.record_manager.start_monitor_recordings()
            await self.app.snack_bar.show_snack_bar(self._["start_recording_success_tip"], bgcolor=ft.Colors.GREEN)

    async def stop_monitor_recordings_on_click(self, _):
        await self.app.record_manager.stop_monitor_recordings()
        await self.app.snack_bar.show_snack_bar(self._["stop_recording_success_tip"])

    async def delete_monitor_recordings_on_click(self, _):
        selected_recordings = await self.app.record_manager.get_selected_recordings()
        tips = self._["batch_delete_confirm_tip"] if selected_recordings else self._["clear_all_confirm_tip"]

        async def confirm_dlg(_):

            if selected_recordings:
                await self.app.record_manager.stop_monitor_recordings(selected_recordings)
                await self.app.record_manager.delete_recording_cards(selected_recordings)
            else:
                await self.app.record_manager.stop_monitor_recordings(self.app.record_manager.recordings)
                await self.app.record_manager.clear_all_recordings()
                await self.delete_all_recording_cards()
                self.app.page.pubsub.send_others_on_topic("delete_all", None)

            self.recording_card_area.update()
            await self.app.snack_bar.show_snack_bar(
                self._["delete_recording_success_tip"], bgcolor=ft.Colors.GREEN, duration=2000
            )
            await close_dialog(None)

        async def close_dialog(_):
            batch_delete_alert_dialog.open = False
            batch_delete_alert_dialog.update()

        batch_delete_alert_dialog = ft.AlertDialog(
            title=ft.Text(self._["confirm"]),
            content=ft.Text(tips),
            actions=[
                ft.TextButton(text=self._["cancel"], on_click=close_dialog),
                ft.TextButton(text=self._["sure"], on_click=confirm_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=False,
        )

        batch_delete_alert_dialog.open = True
        self.app.dialog_area.content = batch_delete_alert_dialog
        self.page.update()

    async def delete_all_recording_cards(self):
        self.recording_card_area.controls.clear()
        self.recording_card_area.update()
        self.app.record_card_manager.cards_obj = {}

    async def subscribe_del_all_cards(self, *_):
        await self.delete_all_recording_cards()

    async def subscribe_add_cards(self, _, recording):
        await self.add_record_card(recording, True)

    async def on_keyboard(self, e: ft.KeyboardEvent):
        if e.alt and e.key == "H":
            self.app.dialog_area.content = HelpDialog(self.app)
            self.app.dialog_area.content.open = True
            self.app.dialog_area.update()
        if self.app.current_page == self:
            if e.ctrl and e.key == "F":
                self.page.run_task(self.search_on_click, e)
            elif e.ctrl and e.key == "R":
                self.page.run_task(self.refresh_cards_on_click, e)
            elif e.alt and e.key == "N":
                self.page.run_task(self.add_recording_on_click, e)
            elif e.alt and e.key == "B":
                self.page.run_task(self.start_monitor_recordings_on_click, e)
            elif e.alt and e.key == "P":
                self.page.run_task(self.stop_monitor_recordings_on_click, e)
            elif e.alt and e.key == "D":
                self.page.run_task(self.delete_monitor_recordings_on_click, e)
