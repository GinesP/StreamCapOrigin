import asyncio
import os.path

import flet as ft

from ....models.recording.recording_model import Recording
from ....models.recording.recording_status_model import RecordingStatus
from ....utils import utils
from ....utils.logger import logger
from ...views.storage_view import StoragePage
from ..dialogs.card_dialog import CardDialog
from ..state.recording_card_state import RecordingCardState
from .recording_dialog import RecordingDialog
from .video_player import VideoPlayer


class RecordingCardManager:
    def __init__(self, app):
        self.app = app
        self.cards_obj = {}
        self.update_duration_tasks = {}
        self.selected_cards = {}
        self.app.language_manager.add_observer(self)
        self._ = {}
        self.load()
        self.pubsub_subscribe()
        self._duration_task_started = False

    def load(self):
        language = self.app.language_manager.language
        for key in ("recording_card", "recording_manager", "base", "recordings_page", "video_quality", "storage_page"):
            self._.update(language.get(key, {}))

    def pubsub_subscribe(self):
        self.app.page.pubsub.subscribe_topic("update", self.subscribe_update_card)
        self.app.page.pubsub.subscribe_topic("delete", self.subscribe_remove_cards)

    async def create_card(self, recording: Recording, subscribe_add_cards: bool = False):
        """Create a card for a given recording."""
        rec_id = recording.rec_id
            
        card_data = self._create_card_components(recording)
        self.cards_obj[rec_id] = card_data
        
        if not self._duration_task_started:
            self._duration_task_started = True
            self.app.page.run_task(self.global_update_durations)
            
        return card_data["card"]

    def _format_date(self, date_str):
        if not date_str:
            return ""
        try:
            from datetime import datetime
            # Date can be "YYYY-MM-DD HH:MM:SS" or just "YYYY-MM-DD"
            if " " in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            now = datetime.now()
            diff = now - dt
            
            is_es = self.app.language_manager.language_code == "es"
            
            if diff.days == 0:
                if diff.seconds < 60: return "Ahora" if is_es else "Just now"
                if diff.seconds < 3600: 
                    m = diff.seconds // 60
                    return f"Hace {m}m" if is_es else f"{m}m ago"
                h = diff.seconds // 3600
                return f"Hace {h}h" if is_es else f"{h}h ago"
            if diff.days == 1: return "Ayer" if is_es else "Yesterday"
            if diff.days < 7: return f"Hace {diff.days}d" if is_es else f"{diff.days}d ago"
            if diff.days < 30: 
                w = diff.days // 7
                if w == 1: return "Hace 1 sem." if is_es else "1w ago"
                return f"Hace {w} sem." if is_es else f"{w}w ago"
            if diff.days < 365:
                m = diff.days // 30
                if m == 1: return "Hace 1 mes" if is_es else "1mo ago"
                return f"Hace {m} meses" if is_es else f"{m}mo ago"
            y = diff.days // 365
            if y == 1: return "Hace 1 año" if is_es else "1y ago"
            return f"Hace {y} años" if is_es else f"{y}y ago"
        except:
            return date_str.split(" ")[0] if " " in date_str else date_str

    def _create_card_components(self, recording: Recording):
        """create card components."""
        # --- 1. Basic Controls & Labels ---
        duration_text_label = ft.Text(
            self.app.record_manager.get_duration(recording),
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            visible=recording.is_recording or recording.is_live
        )

        record_button = ft.IconButton(
            icon=self.get_icon_for_recording_state(recording),
            tooltip=self.get_tip_for_recording_state(recording),
            icon_size=20,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.recording_button_on_click, e, rec),
        )

        open_folder_button = ft.IconButton(
            icon=ft.Icons.FOLDER_OUTLINED,
            tooltip=self._["open_folder"],
            icon_size=20,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.recording_dir_button_on_click, e, rec),
        )

        # Secondary buttons (hidden by default)
        edit_button = ft.IconButton(
            icon=ft.Icons.EDIT_OUTLINED,
            tooltip=self._["edit_record_config"],
            icon_size=18,
            visible=False,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.edit_recording_button_click, e, rec),
        )

        preview_button = ft.IconButton(
            icon=ft.Icons.VIDEO_LIBRARY_OUTLINED,
            tooltip=self._["preview_video"],
            icon_size=18,
            visible=False,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.preview_video_button_on_click, e, rec),
        )

        monitor_button = ft.IconButton(
            icon=self.get_icon_for_monitor_state(recording),
            tooltip=self.get_tip_for_monitor_state(recording),
            icon_size=18,
            visible=False,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.monitor_button_on_click, e, rec),
        )

        delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            tooltip=self._["delete_monitor"],
            icon_size=18,
            visible=False,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.recording_delete_button_click, e, rec),
        )

        recording_info_button = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            tooltip=self._["recording_info"],
            icon_size=18,
            visible=False,
            on_click=lambda e, rec=recording: self.app.page.run_task(self.recording_info_button_on_click, e, rec),
        )

        # --- 2. Title & Metadata ---
        display_title = RecordingCardState.get_display_title(recording, self._)
        display_title_label = ft.Text(
            display_title,
            size=15,
            weight=ft.FontWeight.W_600,
            selectable=True,
            max_lines=1,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        status_label = self.create_status_label(recording)

        added_at = getattr(recording, "added_at", None)
        added_at_text = f"{self._.get('added_at', 'Added')}: {self._format_date(added_at)}" if added_at else ""
        added_at_label = ft.Text(added_at_text, size=11, color=ft.Colors.ON_SURFACE_VARIANT, visible=bool(added_at))

        last_active = getattr(recording, "last_active_at", None)
        last_active_text = f"{self._.get('last_active_at', 'Last active')}: {self._format_date(last_active)}" if last_active else ""
        last_active_label = ft.Text(last_active_text, size=11, color=ft.Colors.ON_SURFACE_VARIANT, visible=bool(last_active))

        priority_score = getattr(recording, "priority_score", 0.0)
        priority_badge = ft.Container(
            content=ft.Text(f"{priority_score:.0%}", size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=ft.Colors.BLUE_GREY_400,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=5,
            height=26,
            alignment=ft.alignment.center,
            visible=priority_score > 0,
            tooltip=self._.get('priority', 'Priority Score')
        )

        # --- 3. Badges (Intelligence) ---
        from ....core.recording.history_manager import HistoryManager
        likelihood_score = HistoryManager.get_likelihood_score(recording)
        
        if likelihood_score >= 0.9:
            l_text = self._.get("likelihood_high", "High")
            l_color = ft.Colors.GREEN_400
        elif likelihood_score >= 0.5:
            l_text = self._.get("likelihood_normal", "Normal")
            l_color = ft.Colors.BLUE_400
        else:
            l_text = self._.get("likelihood_low", "Low")
            l_color = ft.Colors.AMBER_400

        likelihood_label = ft.Container(
            content=ft.Text(l_text, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=l_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=5,
            height=26,
            alignment=ft.alignment.center,
            visible=bool(recording.historical_intervals),
            tooltip=self._.get('likelihood', 'Likelihood')
        )

        interval = recording.loop_time_seconds
        if interval <= 60:
            q_text, q_color, q_tip = "F", ft.Colors.GREEN_400, "Fast Queue"
        elif interval <= 180:
            q_text, q_color, q_tip = "M", ft.Colors.BLUE_400, "Medium Queue"
        else:
            q_text, q_color, q_tip = "S", ft.Colors.AMBER_400, "Slow Queue"

        queue_label = ft.Container(
            content=ft.Text(q_text, size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=q_color,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=5,
            height=26,
            alignment=ft.alignment.center,
            tooltip=q_tip
        )


        # --- 4. Layout ---
        avatar_image = ft.CircleAvatar(
            foreground_image_src=recording.avatar_url,
            content=ft.Text(recording.streamer_name[0] if recording.streamer_name else "?"),
            radius=20,
        )

        # Status Bar (Left indicator)
        status_bar = ft.VerticalDivider(
            width=4,
            thickness=4,
            color=self.get_card_border_color(recording),
            visible=True
        )

        action_icons = ft.Row(
            [
                open_folder_button,
                record_button,
                recording_info_button,
                preview_button,
                edit_button,
                monitor_button,
                delete_button,
            ],
            spacing=0,
            alignment=ft.MainAxisAlignment.START,
        )

        # Header: Avatar | (Title, Status, Duration) | Badges
        title_col = ft.Column(
            [
                display_title_label,
                ft.Row([status_label, duration_text_label], spacing=10) if status_label else duration_text_label,
            ],
            spacing=2,
            expand=True,
        )

        header_row = ft.Row(
            [
                avatar_image,
                title_col,
                ft.Column(
                    [
                        ft.Row([queue_label, likelihood_label, priority_badge], spacing=5),
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                )
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

        # Hover handler
        async def on_hover(e):
            is_hovered = e.data == "true"
            # Optimization: avoid redundant updates if state hasn't changed
            if getattr(card_container, "_is_hovered", False) == is_hovered:
                return
            card_container._is_hovered = is_hovered
            
            recording_info_button.visible = is_hovered
            preview_button.visible = is_hovered
            edit_button.visible = is_hovered
            monitor_button.visible = is_hovered
            delete_button.visible = is_hovered
            
            # Subtle background change on hover
            if is_hovered:
                if not recording.selected:
                    card_container.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
            else:
                card_container.bgcolor = self.get_card_background_color(recording)
            
            if card_container.page:
                card_container.update()

        card_container = ft.Container(
            content=ft.Row(
                [
                    status_bar,
                    ft.Column(
                        [
                            header_row,
                            ft.Row([added_at_label, last_active_label], spacing=15),
                            action_icons,
                        ],
                        spacing=8,
                        expand=True,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=10,
            ),
            padding=ft.padding.only(left=0, top=12, right=12, bottom=8),
            on_click=lambda e, rec=recording: self.app.page.run_task(self.recording_card_on_click, e, rec),
            on_hover=on_hover,
            bgcolor=self.get_card_background_color(recording),
            border_radius=8,
            shadow=ft.BoxShadow(
                blur_radius=10,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2),
            ),
        )

        card = ft.Card(
            key=str(recording.rec_id),
            content=card_container,
            elevation=0,
        )

        return {
            "card": card,
            "display_title_label": display_title_label,
            "duration_label": duration_text_label,
            "priority_badge": priority_badge,
            "record_button": record_button,
            "open_folder_button": open_folder_button,
            "recording_info_button": recording_info_button,
            "edit_button": edit_button,
            "monitor_button": monitor_button,
            "preview_button": preview_button,
            "delete_button": delete_button,
            "status_label": status_label,
            "added_at_label": added_at_label,
            "last_active_label": last_active_label,
            "likelihood_label": likelihood_label,
            "queue_label": queue_label,
            "avatar_image": avatar_image,
            "status_bar": status_bar,
            "action_icons": action_icons,
            "title_col": title_col,
        }

    def get_card_background_color(self, recording: Recording):
        if recording.selected:
            return ft.colors.SECONDARY_CONTAINER
        return ft.colors.SURFACE_VARIANT

    @staticmethod
    def get_card_border_color(recording: Recording):
        """Get the border color of the card."""
        return RecordingCardState.get_border_color(recording)

    def create_status_label(self, recording: Recording):
        config = RecordingCardState.get_status_label_config(recording, self._)
        if not config:
            return None

        return ft.Container(
            content=ft.Text(
                config["text"],
                color=config["text_color"],
                size=12,
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=config["bgcolor"],
            border_radius=5,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            height=26,
            alignment=ft.alignment.center,
        )

    async def update_card(self, recording: Recording):
        """Update only the recordings cards in the scrollable content area."""
        if recording.rec_id not in self.cards_obj:
            return

        try:
            card_info = self.cards_obj[recording.rec_id]
            
            # Update background and border based on selection/state
            if card_info.get("card") and card_info["card"].content:
                card_container = card_info["card"].content
                card_container.bgcolor = self.get_card_background_color(recording)
                
                # Update status bar color
                if card_info.get("status_bar"):
                    card_info["status_bar"].color = self.get_card_border_color(recording)

            # Update title
            if card_info.get("display_title_label"):
                card_info["display_title_label"].value = RecordingCardState.get_display_title(recording, self._)
                # weight is now fixed in the component creation

            # Update status label
            new_status_label = self.create_status_label(recording)
            if card_info.get("status_label") != new_status_label:
                try:
                    title_col = card_info.get("title_col")
                    if title_col:
                        # title_col.controls[0] is display_title_label
                        # title_col.controls[1] is the status/duration component
                        if new_status_label:
                            if isinstance(title_col.controls[1], ft.Text): # Only duration present
                                duration_label = title_col.controls.pop()
                                title_col.controls.append(ft.Row([new_status_label, duration_label], spacing=10))
                            else: # Status row already exists
                                status_duration_row = title_col.controls[1]
                                status_duration_row.controls[0] = new_status_label
                        else:
                            # Remove status label if it exists
                            if not isinstance(title_col.controls[1], ft.Text):
                                status_duration_row = title_col.controls[1]
                                duration_label = status_duration_row.controls[1]
                                title_col.controls[1] = duration_label
                    
                    card_info["status_label"] = new_status_label
                except Exception as e:
                    logger.debug(f"Update status label failed: {e}")

            # Update duration
            if card_info.get("duration_label"):
                card_info["duration_label"].value = self.app.record_manager.get_duration(recording)
                card_info["duration_label"].visible = recording.is_recording or recording.is_live

            # Update metadata labels
            if card_info.get("added_at_label"):
                added_at = getattr(recording, "added_at", None)
                card_info["added_at_label"].value = f"{self._.get('added_at', 'Added')}: {self._format_date(added_at)}" if added_at else ""
                card_info["added_at_label"].visible = bool(added_at)

            if card_info.get("last_active_label"):
                last_active = getattr(recording, "last_active_at", None)
                card_info["last_active_label"].value = f"{self._.get('last_active_at', 'Last active')}: {self._format_date(last_active)}" if last_active else ""
                card_info["last_active_label"].visible = bool(last_active)

            if card_info.get("priority_badge"):
                priority_score = getattr(recording, "priority_score", 0.0)
                card_info["priority_badge"].content.value = f"{priority_score:.0%}"
                card_info["priority_badge"].visible = priority_score > 0

            # Update likelihood
            if card_info.get("likelihood_label"):
                from ....core.recording.history_manager import HistoryManager
                likelihood_score = HistoryManager.get_likelihood_score(recording)
                if likelihood_score >= 0.9:
                    l_text = self._.get("likelihood_high", "High")
                    l_color = ft.Colors.GREEN_400
                elif likelihood_score >= 0.5:
                    l_text = self._.get("likelihood_normal", "Normal")
                    l_color = ft.Colors.BLUE_400
                else:
                    l_text = self._.get("likelihood_low", "Low")
                    l_color = ft.Colors.AMBER_400
                
                card_info["likelihood_label"].content.value = l_text
                card_info["likelihood_label"].bgcolor = l_color
                card_info["likelihood_label"].visible = bool(recording.historical_intervals)

            # Update queue label
            if card_info.get("queue_label"):
                interval = recording.loop_time_seconds or 300
                if interval <= 60:
                    q_text, q_color, q_tip = "F", ft.Colors.GREEN_400, "Fast Queue"
                elif interval <= 180:
                    q_text, q_color, q_tip = "M", ft.Colors.BLUE_400, "Medium Queue"
                else:
                    q_text, q_color, q_tip = "S", ft.Colors.AMBER_400, "Slow Queue"
                
                card_info["queue_label"].content.value = q_text
                card_info["queue_label"].bgcolor = q_color
                card_info["queue_label"].tooltip = q_tip

            # Update buttons
            if card_info.get("record_button"):
                card_info["record_button"].icon = self.get_icon_for_recording_state(recording)
                card_info["record_button"].tooltip = self.get_tip_for_recording_state(recording)

            if card_info.get("monitor_button"):
                card_info["monitor_button"].icon = self.get_icon_for_monitor_state(recording)
                card_info["monitor_button"].tooltip = self.get_tip_for_monitor_state(recording)

            if card_info.get("avatar_image"):
                card_info["avatar_image"].foreground_image_src = recording.avatar_url
                if not recording.avatar_url:
                    card_info["avatar_image"].content = ft.Text(recording.streamer_name[0] if recording.streamer_name else "?")
                else:
                    card_info["avatar_image"].content = None

            # Refresh card
            try:
                if card_info["card"].page:
                    card_info["card"].update()
            except Exception as e:
                pass

        except Exception as e:
            logger.debug(f"Update card failed: {e}")

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
            self.app.record_manager.stop_recording(recording, manually_stopped=True)
            self.app.page.run_task(self.app.snack_bar.show_snack_bar, self._["stop_monitor_tip"])
        else:
            recording.update(
                {
                    "monitor_status": not recording.monitor_status,
                    "status_info": RecordingStatus.STATUS_CHECKING,
                    "display_title": f"{recording.title}",
                    "showed_checking_status": False,
                }
            )
            self.app.page.run_task(self.app.record_manager.check_if_live, recording)
            self.app.page.run_task(self.app.snack_bar.show_snack_bar, self._["start_monitor_tip"], ft.Colors.GREEN)

        await self.update_card(recording)
        self.app.page.pubsub.send_others_on_topic("update", recording)
        self.app.page.run_task(self.app.record_manager.persist_recordings)

    async def show_recording_info_dialog(self, recording: Recording):
        """Display a dialog with detailed information about the recording."""
        try:
            dialog = CardDialog(self.app, recording)
            self.app.page.open(dialog)
        except Exception as e:
            logger.debug(f"Show recording info dialog failed: {e}")
        except Exception as e:
            logger.debug(f"Show recording info dialog failed: {e}")

    async def edit_recording_callback(self, recording_list: list[dict]):
        recording_dict = recording_list[0]
        rec_id = recording_dict["rec_id"]
        recording = self.app.record_manager.find_recording_by_id(rec_id)

        await self.app.record_manager.update_recording_card(recording, updated_info=recording_dict)
        # The display_title is now dynamically generated by RecordingCardState.get_display_title
        # No need to manually set it here based on monitor_status.

        recording.scheduled_time_range = await self.app.record_manager.get_scheduled_time_range(
            recording.scheduled_start_time, recording.monitor_hours)

        await self.update_card(recording)
        self.app.page.pubsub.send_others_on_topic("update", recording_dict)

    async def on_toggle_recording(self, recording: Recording):
        """Toggle the recording state for a specific recording."""
        if recording and self.app.recording_enabled:
            if recording.is_recording:
                self.app.record_manager.stop_recording(recording, manually_stopped=True)
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
            if recording.is_recording:
                await self.app.snack_bar.show_snack_bar(self._["please_stop_monitor_tip"])
                return
            await self.app.record_manager.delete_recording_cards([recording])
            await self.app.snack_bar.show_snack_bar(
                self._["delete_recording_success_tip"], bgcolor=ft.Colors.GREEN, duration=2000
            )

    async def remove_recording_card(self, recordings: list[Recording]):
        try:
            recordings_page = self.app.current_page

            existing_ids = {rec.rec_id for rec in self.app.record_manager.recordings}
            remove_ids = {rec.rec_id for rec in recordings}
            keep_ids = existing_ids - remove_ids

            cards_to_remove = [
                card_data["card"]
                for rec_id, card_data in self.cards_obj.items()
                if rec_id not in keep_ids
            ]

            recordings_page.recording_card_area.content.controls = [
                control
                for control in recordings_page.recording_card_area.content.controls
                if control not in cards_to_remove
            ]

            self.cards_obj = {
                k: v for k, v in self.cards_obj.items()
                if k in keep_ids
            }

            try:
                recordings_page.recording_card_area.update()
            except (ft.core.page.PageDisconnectedException, AssertionError) as e:
                logger.debug(f"Update recording card area failed: {e}")

        except (ft.core.page.PageDisconnectedException, AssertionError) as e:
            logger.debug(f"Remove recording card failed: {e}")
        except Exception as e:
            logger.debug(f"Remove recording card failed: {e}")

    @staticmethod
    async def update_record_hover(recording: Recording):
        return ft.Colors.GREY_400 if recording.selected else None

    @staticmethod
    def get_icon_for_recording_state(recording: Recording):
        """Return the appropriate icon based on the recording's state."""
        return RecordingCardState.get_recording_icon(recording)

    def get_tip_for_recording_state(self, recording: Recording):
        return self._["stop_record"] if recording.is_recording else self._["start_record"]

    @staticmethod
    def get_icon_for_monitor_state(recording: Recording):
        """Return the appropriate icon based on the monitor's state."""
        return RecordingCardState.get_monitor_icon(recording)

    def get_tip_for_monitor_state(self, recording: Recording):
        return self._["stop_monitor"] if recording.monitor_status else self._["start_monitor"]

    async def global_update_durations(self):
        """Update active recording durations in a single background task."""
        while True:
            await asyncio.sleep(1)
            try:
                # Iterate over a copy of recordings to avoid concurrent modification issues
                for recording in list(self.app.record_manager.recordings):
                    if recording.rec_id in self.cards_obj:
                        card_info = self.cards_obj[recording.rec_id]
                        
                        # Optimization: Only update duration if values changed
                        if (recording.is_recording or recording.is_live) and card_info.get("duration_label"):
                            new_duration = self.app.record_manager.get_duration(recording)
                            if card_info["duration_label"].value != new_duration:
                                card_info["duration_label"].value = new_duration
                                if card_info["duration_label"].page:
                                    card_info["duration_label"].update()
            except Exception as e:
                logger.debug(f"Global duration update failed: {e}")

    def start_update_task(self, recording: Recording):
        """No longer used individually, kept for compatibility if called elsewhere."""
        pass

    async def on_card_click(self, recording: Recording):
        """Handle card click events."""
        try:
            recording.selected = not recording.selected
            self.selected_cards[recording.rec_id] = recording
            await self.update_card(recording)
        except Exception as e:
            logger.debug(f"Handle card click event failed: {e}")

    async def recording_dir_on_click(self, recording: Recording):
        if recording.recording_dir:
            if os.path.exists(recording.recording_dir):
                if not utils.open_folder(recording.recording_dir):
                    await self.app.snack_bar.show_snack_bar(self._['no_video_file'])
            else:
                await self.app.snack_bar.show_snack_bar(self._["no_recording_folder"])

    async def edit_recording_button_click(self, _, recording: Recording):
        """Handle edit button click by showing the edit dialog with existing recording info."""

        if recording.is_recording or recording.monitor_status:
            await self.app.snack_bar.show_snack_bar(self._["please_stop_monitor_tip"])
            return

        await RecordingDialog(
            self.app,
            on_confirm_callback=self.edit_recording_callback,
            recording=recording,
        ).show_dialog()

    async def recording_delete_button_click(self, _, recording: Recording):
        try:
            async def confirm_dlg(_):
                self.app.page.run_task(self.on_delete_recording, recording)
                await close_dialog(None)

            async def close_dialog(_):
                try:
                    delete_alert_dialog.open = False
                    self.app.page.update()
                except (ft.core.page.PageDisconnectedException, AssertionError) as err:
                    logger.debug(f"Close delete dialog failed: {err}")

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
            self.app.page.open(delete_alert_dialog)
        except (ft.core.page.PageDisconnectedException, AssertionError) as e:
            logger.debug(f"Show delete dialog failed: {e}")
        except (ft.core.page.PageDisconnectedException, AssertionError) as e:
            logger.debug(f"Show delete dialog failed: {e}")
        except Exception as e:
            logger.debug(f"Show delete dialog failed: {e}")

    async def preview_video_button_on_click(self, _, recording: Recording):
        if self.app.page.web and recording.record_url:
            video_player = VideoPlayer(self.app)
            await video_player.preview_video(recording.preview_url, is_file_path=False, room_url=recording.url)
        elif recording.recording_dir and os.path.exists(recording.recording_dir):
            video_files = []
            streamer_prefix = utils.clean_name(recording.streamer_name)
            for root, _, files in os.walk(recording.recording_dir):
                for file in files:
                    if utils.is_valid_video_file(file) and streamer_prefix in file:
                        video_files.append(os.path.join(root, file))

            if video_files:
                video_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                latest_video = video_files[0]
                await StoragePage(self.app).preview_file(latest_video, recording.url)
            else:
                await self.app.snack_bar.show_snack_bar(self._["no_video_file"])
        else:
            await self.app.snack_bar.show_snack_bar(self._["no_recording_folder"])

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
