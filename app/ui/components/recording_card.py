import asyncio
import os.path
from functools import partial

import flet as ft

from ...models.recording_model import Recording
from ...models.recording_status_model import RecordingStatus
from ...utils import utils
from .card_dialog import CardDialog
from .recording_dialog import RecordingDialog


class RecordingCardManager:
    def __init__(self, app):
        self.app = app
        self.cards_obj = {}
        self.update_duration_tasks = {}
        self.is_card_selected = {}
        self.app.language_manager.add_observer(self)
        self._ = {}
        self.load()
        self.pubsub_subscribe()

    def load(self):
        language = self.app.language_manager.language
        for key in ("recording_card", "recording_manager", "base", "home_page", "video_quality"):
            self._.update(language.get(key, {}))

    def pubsub_subscribe(self):
        self.app.page.pubsub.subscribe_topic("update", self.subscribe_update_card)
        self.app.page.pubsub.subscribe_topic("delete", self.subscribe_remove_cards)

    async def create_card(self, recording: Recording):
        """Create a card for a given recording."""
        rec_id = recording.rec_id
        if not self.cards_obj.get(rec_id):
            if self.app.recording_enabled:
                self.app.page.run_task(self.app.record_manager.check_if_live, recording)
            else:
                recording.status_info = RecordingStatus.NOT_RECORDING_SPACE
        card_data = self._create_card_components(recording)
        self.cards_obj[rec_id] = card_data
        self.start_update_task(recording)
        return card_data["card"]

    def _create_card_components(self, recording: Recording):
        """create card components."""
        speed = recording.speed
        duration_text_label = ft.Text(self.app.record_manager.get_duration(recording), size=12)

        record_button = ft.IconButton(
            icon=self.get_icon_for_recording_state(recording),
            tooltip=self.get_tip_for_recording_state(recording),
            on_click=partial(self.recording_button_on_click, recording=recording),
        )

        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT,
            tooltip=self._["edit_record_config"],
            on_click=partial(self.edit_recording_button_click, recording=recording),
        )

        monitor_button = ft.IconButton(
            icon=self.get_icon_for_monitor_state(recording),
            tooltip=self.get_tip_for_monitor_state(recording),
            on_click=partial(self.monitor_button_on_click, recording=recording),
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE,
            tooltip=self._["delete_monitor"],
            on_click=partial(self.recording_delete_button_click, recording=recording),
        )

        if recording.monitor_status:
            display_title = recording.title
        else:
            display_title = f"[{self._['monitor_stopped']}] {recording.title}"
        display_title_label = ft.Text(display_title, size=14, selectable=True, max_lines=1, no_wrap=True)
        open_folder_button = ft.IconButton(
            icon=ft.Icons.FOLDER,
            tooltip=self._["open_folder"],
            on_click=partial(self.recording_dir_button_on_click, recording=recording),
        )
        recording_info_button = ft.IconButton(
            icon=ft.Icons.INFO,
            tooltip=self._["recording_info"],
            on_click=partial(self.recording_info_button_on_click, recording=recording),
        )
        speed_text_label = ft.Text(speed, size=12)

        card_container = ft.Container(
            content=ft.Column(
                [
                    display_title_label,
                    duration_text_label,
                    speed_text_label,
                    ft.Row(
                        [
                            record_button,
                            open_folder_button,
                            recording_info_button,
                            delete_button,
                            edit_button,
                            monitor_button,
                        ]
                    ),
                ],
                spacing=5,
                tight=True,

            ),
            padding=10,
            on_click=partial(self.recording_card_on_click, recording=recording),
            bgcolor=None,
            border_radius=5,

        )
        card = ft.Card(key=str(recording.rec_id), content=card_container)

        return {
            "card": card,
            "display_title_label": display_title_label,
            "duration_label": duration_text_label,
            "speed_label": speed_text_label,
            "record_button": record_button,
            "open_folder_button": open_folder_button,
            "recording_info_button": recording_info_button,
            "edit_button": edit_button,
            "monitor_button": monitor_button,
        }

    async def update_card(self, recording):
        """Update only the recordings cards in the scrollable content area."""
        if recording.rec_id in self.cards_obj:
            recording_card = self.cards_obj[recording.rec_id]
            recording_card["display_title_label"].value = recording.display_title
            recording_card["duration_label"].value = self.app.record_manager.get_duration(recording)
            recording_card["speed_label"].value = recording.speed
            recording_card["record_button"].icon = self.get_icon_for_recording_state(recording)
            recording_card["record_button"].tooltip = self.get_tip_for_recording_state(recording)
            recording_card["monitor_button"].icon = self.get_icon_for_monitor_state(recording)
            recording_card["monitor_button"].tooltip = self.get_tip_for_monitor_state(recording)
            recording_card["card"].content.bgcolor = await self.update_record_hover(recording)
            recording_card["card"].update()

    async def update_monitor_state(self, recording: Recording):
        """Update the monitor button state based on the current monitoring status."""
        if recording.monitor_status:
            recording.update(
                {
                    "recording": False,
                    "monitor_status": not recording.monitor_status,
                    "status_info": RecordingStatus.STOPPED_MONITORING,
                    "display_title": f"[{self._['monitor_stopped']}] {recording.title}",
                }
            )
            self.app.record_manager.stop_recording(recording)
            self.app.page.run_task(self.app.snack_bar.show_snack_bar, self._["stop_monitor_tip"])
        else:
            recording.update(
                {
                    "monitor_status": not recording.monitor_status,
                    "status_info": RecordingStatus.MONITORING,
                    "display_title": f"{recording.title}",
                }
            )
            self.app.page.run_task(self.app.record_manager.check_if_live, recording)
            self.app.page.run_task(self.app.snack_bar.show_snack_bar, self._["start_monitor_tip"], ft.Colors.GREEN)

        await self.update_card(recording)
        self.app.page.pubsub.send_others_on_topic("update", recording)
        self.app.page.run_task(self.app.record_manager.persist_recordings)

    async def show_recording_info_dialog(self, recording: Recording):
        """Display a dialog with detailed information about the recording."""
        dialog = CardDialog(self.app, recording)
        dialog.open = True
        self.app.dialog_area.content = dialog
        self.app.page.update()

    async def edit_recording_callback(self, recording_list: list[dict]):
        recording_dict = recording_list[0]
        rec_id = recording_dict["rec_id"]
        recording = self.app.record_manager.find_recording_by_id(rec_id)

        await self.app.record_manager.update_recording_card(recording, updated_info=recording_dict)
        if not recording_dict["monitor_status"]:
            recording.display_title = f"[{self._['monitor_stopped']}] " + recording.title

        recording.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
            recording.scheduled_start_time, recording.monitor_hours)

        await self.update_card(recording)
        self.app.page.pubsub.send_others_on_topic("update", recording_dict)

    async def on_toggle_recording(self, recording: Recording):
        """Toggle the recording state for a specific recording."""
        if recording and self.app.recording_enabled:
            if recording.recording:
                self.app.record_manager.stop_recording(recording)
                await self.app.snack_bar.show_snack_bar(self._["stop_record_tip"])
            else:
                if recording.monitor_status:
                    await self.app.record_manager.check_if_live(recording)
                    if recording.is_live:
                        self.app.record_manager.start_update(recording)
                        await self.app.snack_bar.show_snack_bar(self._["pre_record_tip"], bgcolor=ft.Colors.GREEN)
                    else:
                        await self.app.snack_bar.show_snack_bar(self._["is_not_live_tip"])
                else:
                    await self.app.snack_bar.show_snack_bar(self._["please_start_monitor_tip"])

            await self.update_card(recording)
            self.app.page.pubsub.send_others_on_topic("update", recording)

    async def on_delete_recording(self, recording: Recording):
        """Delete a recording from the list and update UI."""
        if recording:
            if recording.recording:
                await self.app.snack_bar.show_snack_bar(self._["please_stop_monitor_tip"])
                return
            await self.app.record_manager.delete_recording_cards([recording])
            await self.app.snack_bar.show_snack_bar(
                self._["delete_recording_success_tip"], bgcolor=ft.Colors.GREEN, duration=2000
            )

    async def remove_recording_card(self, recordings: list[Recording]):
        home_page = self.app.current_page

        existing_ids = {rec.rec_id for rec in self.app.record_manager.recordings}
        remove_ids = {rec.rec_id for rec in recordings}
        keep_ids = existing_ids - remove_ids

        cards_to_remove = [
            card_data["card"]
            for rec_id, card_data in self.cards_obj.items()
            if rec_id not in keep_ids
        ]

        home_page.recording_card_area.controls = [
            control
            for control in home_page.recording_card_area.controls
            if control not in cards_to_remove
        ]

        self.cards_obj = {
            k: v for k, v in self.cards_obj.items()
            if k in keep_ids
        }
        home_page.recording_card_area.update()

    @staticmethod
    async def update_record_hover(recording: Recording):
        return ft.Colors.GREY_400 if recording.selected else None

    @staticmethod
    def get_icon_for_recording_state(recording: Recording):
        """Return the appropriate icon based on the recording's state."""
        return ft.Icons.PLAY_CIRCLE if not recording.recording else ft.Icons.STOP_CIRCLE

    def get_tip_for_recording_state(self, recording: Recording):
        return self._["stop_record"] if recording.recording else self._["start_record"]

    @staticmethod
    def get_icon_for_monitor_state(recording: Recording):
        """Return the appropriate icon based on the monitor's state."""
        return ft.Icons.VISIBILITY if recording.monitor_status else ft.Icons.VISIBILITY_OFF

    def get_tip_for_monitor_state(self, recording: Recording):
        return self._["stop_monitor"] if recording.monitor_status else self._["start_monitor"]

    async def update_duration(self, recording: Recording):
        """Update the duration text periodically."""
        while True:
            await asyncio.sleep(1)  # Update every second
            if not recording or recording.rec_id not in self.cards_obj:  # Stop task if card is removed
                break

            if recording.recording:
                duration_label = self.cards_obj[recording.rec_id]["duration_label"]
                duration_label.value = self.app.record_manager.get_duration(recording)
                duration_label.update()

    def start_update_task(self, recording: Recording):
        """Start a background task to update the duration text."""
        self.update_duration_tasks[recording.rec_id] = self.app.page.run_task(self.update_duration, recording)

    async def on_card_click(self, recording: Recording):
        """Handle card click events."""
        recording.selected = not recording.selected
        self.cards_obj[recording.rec_id]["card"].content.bgcolor = await self.update_record_hover(recording)
        self.cards_obj[recording.rec_id]["card"].update()

    async def recording_dir_on_click(self, recording: Recording):
        if recording.recording_dir:
            if os.path.exists(recording.recording_dir):
                if not utils.open_folder(recording.recording_dir):
                    await self.app.snack_bar.show_snack_bar(self._['no_support_open_dir'])
            else:
                await self.app.snack_bar.show_snack_bar(self._["no_folder_tip"])

    async def edit_recording_button_click(self, _, recording: Recording):
        """Handle edit button click by showing the edit dialog with existing recording info."""

        if recording.recording or recording.monitor_status:
            await self.app.snack_bar.show_snack_bar(self._["please_stop_monitor_tip"])
            return

        await RecordingDialog(
            self.app,
            on_confirm_callback=self.edit_recording_callback,
            recording=recording,
        ).show_dialog()

    async def recording_delete_button_click(self, _, recording: Recording):
        async def confirm_dlg(_):
            self.app.page.run_task(self.on_delete_recording, recording)
            await close_dialog(None)

        async def close_dialog(_):
            delete_alert_dialog.open = False
            delete_alert_dialog.update()

        delete_alert_dialog = ft.AlertDialog(
            title=ft.Text(self._["confirm"]),
            content=ft.Text(self._["delete_confirm_tip"]),
            actions=[
                ft.TextButton(text=self._["cancel"], on_click=close_dialog),
                ft.TextButton(text=self._["sure"], on_click=confirm_dlg),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=False,
        )
        delete_alert_dialog.open = True
        self.app.dialog_area.content = delete_alert_dialog
        self.app.page.update()

    async def recording_button_on_click(self, _, recording: Recording):
        await self.on_toggle_recording(recording)

    async def recording_dir_button_on_click(self, _, recording: Recording):
        await self.recording_dir_on_click(recording)

    async def recording_info_button_on_click(self, _, recording: Recording):
        await self.show_recording_info_dialog(recording)

    async def monitor_button_on_click(self, _, recording: Recording):
        await self.update_monitor_state(recording)

    async def recording_card_on_click(self, _, recording: Recording):
        await self.on_card_click(recording)

    async def subscribe_update_card(self, _, recording: Recording):
        await self.update_card(recording)

    async def subscribe_remove_cards(self, _, recordings: list[Recording]):
        await self.remove_recording_card(recordings)
