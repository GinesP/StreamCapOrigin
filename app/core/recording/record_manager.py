import asyncio
import threading
from collections import defaultdict
from datetime import datetime, timedelta
import random
import time

from ...messages import desktop_notify, message_pusher
from ...models.recording.recording_model import Recording
from ...models.recording.recording_status_model import RecordingStatus
from ...utils import utils
from ...utils.i18n import tr
from ...utils.logger import logger
from ...utils.delay import DelayedTaskExecutor
from ..platforms.platform_handlers import get_platform_info
from ..runtime.process_manager import BackgroundService
from .stream_manager import LiveStreamRecorder


class GlobalRecordingState:
    recordings = []
    lock = threading.Lock()


class RecordingManager:
    def __init__(self, app):
        self.app = app
        self.settings = app.settings
        self.periodic_task_started = False
        self.loop_time_seconds = None
        self.app.language_manager.add_observer(self)
        self.load_recordings()
        self._ = {}
        self.load()
        self.initialize_dynamic_state()
        max_concurrent = int(self.settings.user_config.get("platform_max_concurrent_requests", 3))
        self.platform_semaphores = defaultdict(lambda: asyncio.Semaphore(max_concurrent))
        self.active_recorders = {}
        self.persist_delay_handler = DelayedTaskExecutor(self.app, self, delay=2)
        
        # 1. Multi-Priority Task Queues (Intelligence)
        # Dedicated queues to ensure fast checks aren't blocked by slow ones
        self._queue_fast = asyncio.Queue()    # <= 60s
        self._queue_medium = asyncio.Queue()  # <= 180s
        self._queue_slow = asyncio.Queue()    # > 180s
        
        self._worker_tasks = [
            asyncio.create_task(self._process_priority_queue("fast", self._queue_fast)),
            asyncio.create_task(self._process_priority_queue("medium", self._queue_medium)),
            asyncio.create_task(self._process_priority_queue("medium", self._queue_medium)), # Second medium worker
            asyncio.create_task(self._process_priority_queue("slow", self._queue_slow))
        ]

    async def _process_priority_queue(self, name: str, queue: asyncio.Queue):
        """Dedicated worker for a specific priority queue."""
        logger.debug(f"Intelligence Worker-{name} started.")
        while True:
            recording = await queue.get()
            try:
                if recording.monitor_status and not recording.is_recording:
                    # Relying on Semaphore inside check_if_live for platform safety
                    await self.check_if_live(recording)
            except Exception as e:
                logger.error(f"Error in {name} queue worker: {e}")
            finally:
                queue.task_done()

    @property
    def recordings(self):
        return GlobalRecordingState.recordings

    @recordings.setter
    def recordings(self, value):
        raise AttributeError("Please use add_recording/update_recording methods to modify data")

    def load(self):
        language = self.app.language_manager.language
        for key in ("recording_manager", "video_quality"):
            self._.update(language.get(key, {}))

    def load_recordings(self):
        """Load recordings from a JSON file into objects."""
        recordings_data = self.app.config_manager.load_recordings_config()
        if not GlobalRecordingState.recordings:
            GlobalRecordingState.recordings = [Recording.from_dict(rec) for rec in recordings_data]
        logger.info(f"Live Recordings: Loaded {len(self.recordings)} items")

    def initialize_dynamic_state(self):
        """Initialize dynamic state for all recordings."""
        loop_time_seconds = self.settings.user_config.get("loop_time_seconds")
        self.loop_time_seconds = int(loop_time_seconds or 300)
        for recording in self.recordings:
            recording.loop_time_seconds = self.loop_time_seconds
            recording.update_title(self._[recording.quality])
            recording.is_checking = False

    async def add_recording(self, recording):
        with GlobalRecordingState.lock:
            GlobalRecordingState.recordings.append(recording)
            await self.persist_recordings()

    async def remove_recording(self, recording: Recording):
        with GlobalRecordingState.lock:
            GlobalRecordingState.recordings.remove(recording)
            await self.persist_recordings()

    async def clear_all_recordings(self):
        with GlobalRecordingState.lock:
            GlobalRecordingState.recordings.clear()
            await self.persist_recordings()

    async def persist_recordings(self):
        """Persist recordings to a JSON file with a small delay to batch updates."""
        self.app.page.run_task(self.persist_delay_handler.start_task_timer, self._actual_persist_recordings, None)

    async def _actual_persist_recordings(self, delay):
        """The actual disk write operation."""
        if delay:
            await asyncio.sleep(delay)
        data_to_save = [rec.to_dict() for rec in self.recordings]
        await self.app.config_manager.save_recordings_config(data_to_save)

    async def update_recording_card(self, recording: Recording, updated_info: dict):
        """Update an existing recording object and persist changes to a JSON file."""
        if recording:
            recording.update(updated_info)
            self.app.page.run_task(self.persist_recordings)

    @staticmethod
    async def _update_recording(
            recording: Recording, monitor_status: bool, display_title: str, status_info: str, selected: bool
    ):
        attrs_update = {
            "monitor_status": monitor_status,
            "display_title": display_title,
            "status_info": status_info,
            "selected": selected,
        }
        for attr, value in attrs_update.items():
            setattr(recording, attr, value)

    async def start_monitor_recording(self, recording: Recording, auto_save: bool = True):
        """
        Start monitoring a single recording if it is not already being monitored.
        """
        if not recording.monitor_status:
            recording.is_checking = True
            recording.is_live = False
            recording.showed_checking_status = False
            await self._update_recording(
                recording=recording,
                monitor_status=True,
                display_title=recording.title,
                status_info=RecordingStatus.STATUS_CHECKING,
                selected=False,
            )

            self.app.page.run_task(self.app.record_card_manager.update_card, recording)
            self.app.page.pubsub.send_others_on_topic("update", recording)

            self.app.page.run_task(self.check_if_live, recording)

            if auto_save:
                self.app.page.run_task(self.persist_recordings)

    async def stop_monitor_recording(self, recording: Recording, auto_save: bool = True):
        """
        Stop monitoring a single recording if it is currently being monitored.
        """
        if recording.monitor_status:
            await self._update_recording(
                recording=recording,
                monitor_status=False,
                display_title=f"[{self._['monitor_stopped']}] {recording.title}",
                status_info=RecordingStatus.STOPPED_MONITORING,
                selected=False,
            )
            self.stop_recording(recording, manually_stopped=True)
            self.app.page.run_task(self.app.record_card_manager.update_card, recording)
            self.app.page.pubsub.send_others_on_topic("update", recording)
            if auto_save:
                self.app.page.run_task(self.persist_recordings)

    async def start_monitor_recordings(self):
        """
        Start monitoring multiple recordings based on user selection or all recordings if none are selected.
        """
        selected_recordings = await self.get_selected_recordings()
        pre_start_monitor_recordings = selected_recordings if selected_recordings else self.recordings
        cards_obj = self.app.record_card_manager.cards_obj
        for recording in pre_start_monitor_recordings:
            if cards_obj[recording.rec_id]["card"].visible:
                self.app.page.run_task(self.start_monitor_recording, recording, auto_save=False)
        self.app.page.run_task(self.persist_recordings)
        logger.info(f"Batch Start Monitor Recordings: {[i.rec_id for i in pre_start_monitor_recordings]}")

    async def stop_monitor_recordings(self, selected_recordings: list[Recording | None] | None = None):
        """
        Stop monitoring multiple recordings based on user selection or all recordings if none are selected.
        """
        if not selected_recordings:
            selected_recordings = await self.get_selected_recordings()
        pre_stop_monitor_recordings = selected_recordings or self.recordings
        cards_obj = self.app.record_card_manager.cards_obj
        for recording in pre_stop_monitor_recordings:
            if cards_obj[recording.rec_id]["card"].visible:
                self.app.page.run_task(self.stop_monitor_recording, recording, auto_save=False)
        self.app.page.run_task(self.persist_recordings)
        logger.info(f"Batch Stop Monitor Recordings: {[i.rec_id for i in pre_stop_monitor_recordings]}")

    async def get_selected_recordings(self):
        return [recording for recording in self.recordings if recording.selected]

    async def remove_recordings(self, recordings: list[Recording]):
        """Remove a recording from the list and update the JSON file."""
        for recording in recordings:
            if recording in self.recordings:
                await self.remove_recording(recording)
                logger.info(f"Delete Items: {recording.rec_id}-{recording.streamer_name}")

    def find_recording_by_id(self, rec_id: str):
        """Find a recording by its ID (hash of dict representation)."""
        for rec in self.recordings:
            if rec.rec_id == rec_id:
                return rec
        return None

    async def check_all_live_status(self):
        """Check the live status of all recordings and update their display titles."""
        # Prioritize recordings based on their EMA priority score
        def get_priority_score(rec):
            return getattr(rec, 'priority_score', 0.0)

        recordings_to_check = sorted(
            self.recordings,
            key=lambda r: (get_priority_score(r), random.random()),
            reverse=True
        )
        
        dispatched_fast = 0
        dispatched_medium = 0
        dispatched_slow = 0
        busy_fast = 0
        busy_medium = 0
        busy_slow = 0
        skipping_count = 0
        
        for recording in recordings_to_check:
            if not recording.monitor_status:
                continue

            if recording.is_recording:
                # Still live, so update historical patterns!
                alpha_active = float(self.settings.user_config.get("ema_alpha_active", 0.1))
                alpha_offline = float(self.settings.user_config.get("ema_alpha_offline", 0.01))
                recording.increment_live_counts(is_live=True, alpha_active=alpha_active, alpha_offline=alpha_offline)
                self.app.page.run_task(self.app.record_card_manager.update_card, recording)
                continue

            # 1. Apply Smart Predictive Polling (Intelligence)
            from .history_manager import HistoryManager
            likelihood = HistoryManager.get_likelihood_score(recording)
            base_interval = int(self.settings.user_config.get("loop_time_seconds", 300))
            recording.loop_time_seconds = HistoryManager.get_adjusted_interval(recording, base_interval)

            # 2. Check if it's time to poll
            is_exceeded = utils.is_time_interval_exceeded(recording.detection_time, recording.loop_time_seconds)
            
            if not recording.detection_time or is_exceeded:
                # 3. Categorize by priority for logging and dispatch
                if recording.loop_time_seconds <= 60:
                    prio_key = "F"
                elif recording.loop_time_seconds <= 180:
                    prio_key = "M"
                else:
                    prio_key = "S"

                # 4. Prevent redundant queuing if already checking or in queue
                if recording.is_checking:
                    if prio_key == "F": busy_fast += 1
                    elif prio_key == "M": busy_medium += 1
                    else: busy_slow += 1
                    continue

                recording.is_checking = True
                
                # 5. Dispatch to priority-specific queue
                if prio_key == "F":
                    self._queue_fast.put_nowait(recording)
                    dispatched_fast += 1
                elif prio_key == "M":
                    self._queue_medium.put_nowait(recording)
                    dispatched_medium += 1
                else:
                    self._queue_slow.put_nowait(recording)
                    dispatched_slow += 1
                
                logger.debug(f"Intelligence: Dispatched {recording.streamer_name} to {prio_key} queue (Likelihood {likelihood:.2f})")
            else:
                skipping_count += 1

        # Summary Log
        total_active = dispatched_fast + dispatched_medium + dispatched_slow + busy_fast + busy_medium + busy_slow
        if total_active > 0:
            logger.opt(colors=True).info(
                f"<yellow>Intelligence Cycle Summary: "
                f"Disp({dispatched_fast}F+{dispatched_medium}M+{dispatched_slow}S) | "
                f"Busy({busy_fast}F+{busy_medium}M+{busy_slow}S) | "
                f"{skipping_count} waiting</yellow>"
            )
        
        # Persist all recording updates once after all checks are queued
        self.app.page.run_task(self.persist_recordings)

    _periodic_task_running = False

    @classmethod
    def is_periodic_task_running(cls):
        return cls._periodic_task_running

    @classmethod
    def set_periodic_task_running(cls, value=True):
        cls._periodic_task_running = value

    async def setup_periodic_live_check(self, interval: int = 180):
        """Set up a periodic task to check live status."""

        async def periodic_check():
            logger.info("Starting periodic live check background task")
            while True:
                immediate_check_on_startup = self.app.settings.user_config.get("check_live_on_browser_refresh", True)
                if immediate_check_on_startup:
                    # Run first check immediately (it is already staggered inside check_all_live_status)
                    if self.app.recording_enabled:
                        await self.check_all_live_status()
                    await asyncio.sleep(interval)
                else:
                    await asyncio.sleep(interval)
                
                await self.check_free_space()
                if self.app.recording_enabled:
                    await self.check_all_live_status()

        if not RecordingManager.is_periodic_task_running():
            RecordingManager.set_periodic_task_running(True)
            self.periodic_task_started = True
            logger.info(f"Initializing periodic live check task with interval: {interval}s")
            asyncio.create_task(periodic_check())
        else:
            logger.info("Periodic live check task already running globally, skipping initialization")

    async def check_if_live_with_retry(self, recording: Recording, retries: int = 2, delay: int = 20):
        """
        Check if the live stream is available with retries.
        Useful when a stream ends abruptly and might restart shortly.
        """
        for i in range(retries):
            if recording.is_recording or not recording.monitor_status:
                break
            
            logger.log("RETRY", f"Performing extra live check ({i + 1}/{retries}) for: {recording.url}")
            await self.check_if_live(recording)
            
            # If after check_if_live the recording started (is_recording will be True), we stop retrying
            if recording.is_recording:
                logger.log("RETRY", f"Stream resumed and recording started for: {recording.url}")
                break
            
            if i < retries - 1:
                await asyncio.sleep(delay)

    async def check_if_live(self, recording: Recording):
        """Check if the live stream is available, fetch stream data and update is_live status."""
        try:
            recording.manually_stopped = False
            if recording.is_recording:
                logger.debug(f"Skip check_if_live because recording is busy: {recording.url}")
                return

            if recording.rec_id in self.active_recorders:
                recorder = self.active_recorders[recording.rec_id]
                if not recorder.should_stop:
                    logger.debug(f"Skip check_if_live because recorder is active: {recording.url}")
                    return
                else:
                    logger.debug(f"Proceeding with check_if_live because existing recorder is stopping: {recording.url}")

            if not recording.monitor_status:
                recording.display_title = f"[{self._['monitor_stopped']}] {recording.title}"
                recording.status_info = RecordingStatus.STOPPED_MONITORING
                self.app.page.run_task(self.app.record_card_manager.update_card, recording)
                return

            recording.detection_time = datetime.now().time()
            recording.is_checking = True
            
            # Always update UI to show "Checking" status at the start of detection
            recording.status_info = RecordingStatus.STATUS_CHECKING
            self.app.page.run_task(self.app.record_card_manager.update_card, recording)

            if recording.scheduled_recording:
                scheduled_time_range_list = await self.get_scheduled_time_range(
                    recording.scheduled_start_time, recording.monitor_hours)
                recording.scheduled_time_range = scheduled_time_range_list
                in_scheduled = False
                for scheduled_time_range in scheduled_time_range_list:
                    in_scheduled = utils.is_current_time_within_range(scheduled_time_range)
                    if in_scheduled:
                        break

                if not in_scheduled:
                    recording.status_info = RecordingStatus.NOT_IN_SCHEDULED_CHECK
                    recording.is_live = False
                    logger.info(f"Skip Detection: {recording.url} not in scheduled check range {scheduled_time_range_list}")
                    self.app.page.run_task(self.app.record_card_manager.update_card, recording)
                    return

            recording.status_info = RecordingStatus.STATUS_CHECKING
            platform, platform_key = get_platform_info(recording.url)

            if platform and platform_key and (recording.platform is None or recording.platform_key is None):
                recording.platform = platform
                recording.platform_key = platform_key
                self.app.page.run_task(self.persist_recordings)

            if self.settings.user_config["language"] != "zh_CN":
                platform = platform_key

            output_dir = self.settings.get_video_save_path()
            await self.check_free_space(output_dir)
            if not self.app.recording_enabled:
                recording.status_info = RecordingStatus.NOT_RECORDING_SPACE
                return
            
            recording_info = {
                "platform": platform,
                "platform_key": platform_key,
                "live_url": recording.url,
                "output_dir": output_dir,
                "segment_record": recording.segment_record,
                "segment_time": recording.segment_time,
                "save_format": recording.record_format,
                "quality": recording.quality,
            }

            semaphore = self.platform_semaphores[platform_key]
            recorder = LiveStreamRecorder(self.app, recording, recording_info)
            async with semaphore:
                # Stagger requests slightly to avoid rate limiting
                await asyncio.sleep(random.uniform(2.0, 5.0))
                stream_info = await recorder.fetch_stream()
                logger.info(f"Stream Data: {stream_info.anchor_name if stream_info else 'None'}")
            
            if not stream_info or not stream_info.anchor_name:
                logger.error(f"Fetch stream data failed: {recording.url}")
                recording.status_info = RecordingStatus.LIVE_STATUS_CHECK_ERROR
                if recording.monitor_status:
                    self.app.page.run_task(self.app.record_card_manager.update_card, recording)
                    self.app.page.pubsub.send_others_on_topic("update", recording)
                return
                
            if self.settings.user_config.get("remove_emojis"):
                live_room_text = self._.get("live_room", "Live Room")
                stream_info.anchor_name = utils.clean_name(stream_info.anchor_name, live_room_text)

            if stream_info.is_live:
                # Update last active time
                recording.last_active_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Update counts using the new responsive method
                alpha_active = float(self.settings.user_config.get("ema_alpha_active", 0.1))
                alpha_offline = float(self.settings.user_config.get("ema_alpha_offline", 0.01))
                recording.increment_live_counts(is_live=True, alpha_active=alpha_active, alpha_offline=alpha_offline)
                
                recording.live_title = stream_info.title
                if recording.streamer_name.strip() == self._["live_room"]:
                    recording.streamer_name = stream_info.anchor_name
                recording.title = f"{recording.streamer_name} - {self._[recording.quality]}"
                recording.display_title = f"[{self._['is_live']}] {recording.title}"

                if not recording.is_live:
                    recording.is_live = stream_info.is_live
                    recording.notified_live_start = False
                    recording.notified_live_end = False

                    if desktop_notify.should_push_notification(self.app):
                        desktop_notify.send_notification(
                            title=self._["notify"],
                            message=recording.streamer_name + ' | ' + self._["live_recording_started_message"],
                            app_icon=self.app.tray_manager.icon_path
                        )

                msg_manager = message_pusher.MessagePusher(self.settings)
                user_config = self.settings.user_config
                if (msg_manager.should_push_message(self.settings, recording, message_type='start')
                        and not recording.notified_live_start):
                    push_content = self._["push_content"]
                    begin_push_message_text = user_config.get("custom_stream_start_content")
                    if begin_push_message_text:
                        push_content = begin_push_message_text

                    push_at = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
                    push_content = push_content.replace("[room_name]", recording.streamer_name).replace(
                        "[time]", push_at).replace("[title]", recording.live_title or "None")
                    msg_title = user_config.get("custom_notification_title").strip()
                    msg_title = msg_title or self._["status_notify"]

                    BackgroundService.get_instance().add_task(
                        msg_manager.push_messages_sync, msg_title, push_content
                    )
                    recording.notified_live_start = True

                if not recording.only_notify_no_record:
                    recording.status_info = RecordingStatus.PREPARING_RECORDING
                    recording.loop_time_seconds = self.loop_time_seconds
                    self.start_update(recording)
                    self.app.page.run_task(recorder.start_recording, stream_info)
                else:
                    if recording.notified_live_start:
                        notify_loop_time = user_config.get("notify_loop_time")
                        recording.loop_time_seconds = int(notify_loop_time or 600)
                    else:
                        recording.loop_time_seconds = self.loop_time_seconds

                    recording.cumulative_duration = timedelta()
                    recording.last_duration = timedelta()
                    recording.status_info = RecordingStatus.LIVE_BROADCASTING

            else:
                # Update counts for non-live case
                alpha_active = float(self.settings.user_config.get("ema_alpha_active", 0.1))
                alpha_offline = float(self.settings.user_config.get("ema_alpha_offline", 0.01))
                recording.increment_live_counts(is_live=False, alpha_active=alpha_active, alpha_offline=alpha_offline)

                recording.is_recording = False
                if recording.is_live:
                    recording.is_live = False
                    self.app.page.run_task(recorder.end_message_push)

                recording.status_info = RecordingStatus.MONITORING
                title = f"{stream_info.anchor_name or recording.streamer_name} - {self._[recording.quality]}"
                if recording.streamer_name == self._["live_room"] or \
                        f"[{self._['is_live']}]" in recording.display_title:
                    recording.update(
                        {
                            "streamer_name": stream_info.anchor_name,
                            "title": title,
                            "display_title": title,
                        }
                    )

        finally:
            recording.is_checking = False
            self.app.page.run_task(self.app.record_card_manager.update_card, recording)
        self.app.page.run_task(self.app.record_card_manager.update_card, recording)
        self.app.page.pubsub.send_others_on_topic("update", recording)
        return

    @staticmethod
    def start_update(recording: Recording):
        """Start the recording process."""
        if recording.is_live and not recording.is_recording:
            # Reset cumulative and last durations for a fresh start
            recording.update(
                {
                    "cumulative_duration": timedelta(),
                    "last_duration": timedelta(),
                    "start_time": datetime.now(),
                    "is_recording": True,
                }
            )
            logger.info(tr("console.started_recording", "Started recording for {}").format(recording.title))

    def stop_recording(self, recording: Recording, manually_stopped: bool = True):
        """Stop the recording process."""
        recording.is_live = False
        if recording.is_recording:

            recording.stopping_in_progress = True

            logger.info(f"Trying to stop recorder for {recording.rec_id}, title: {recording.title}")
            logger.debug(f"Active recorders: {list(self.active_recorders.keys())}")

            recording.detection_time = None
            if recording.rec_id in self.active_recorders:
                recorder = self.active_recorders[recording.rec_id]
                logger.debug(f"Found recorder instance - id: {id(recorder)}")
                recorder.request_stop()
                logger.info(f"Requested stop for recorder: {recording.rec_id}")
            else:
                logger.warning(f"No active recorder found for {recording.rec_id}, cannot request stop")
                recording.force_stop = True
                logger.info(f"Set force_stop=True for recording: {recording.rec_id}")

            if recording.start_time is not None:
                elapsed = datetime.now() - recording.start_time
                # Add the elapsed time to the cumulative duration.
                recording.cumulative_duration += elapsed
                # Update the last recorded duration.
                recording.last_duration = recording.cumulative_duration
            recording.start_time = None
            recording.is_recording = False
            recording.manually_stopped = manually_stopped
            recording.status_info = RecordingStatus.NOT_RECORDING
            logger.info(f"Stopped recording for {recording.title}")

            self.app.page.run_task(self.persist_recordings)

    def get_duration(self, recording: Recording):
        """Get the duration of the current recording session in a formatted string."""
        if recording.is_recording and recording.start_time is not None:
            elapsed = datetime.now() - recording.start_time
            # If recording, add the current session time.
            total_duration = recording.cumulative_duration + elapsed
            return self._["recorded"] + " " + str(total_duration).split(".")[0]
        else:
            # If stopped, show the last recorded total duration.
            total_duration = recording.last_duration
            return str(total_duration).split(".")[0]

    async def delete_recording_cards(self, recordings: list[Recording]):
        self.app.page.run_task(self.app.record_card_manager.remove_recording_card, recordings)
        self.app.page.pubsub.send_others_on_topic('delete', recordings)
        await self.remove_recordings(recordings)

        # update the filter area of the recording list page
        if hasattr(self.app, 'current_page') and hasattr(self.app.current_page, 'content_area'):
            if len(self.app.current_page.content_area.controls) > 1:
                self.app.current_page.content_area.controls[1] = self.app.current_page.create_filter_area()
                self.app.current_page.content_area.update()

    async def check_free_space(self, output_dir: str | None = None):
        disk_space_limit = float(self.settings.user_config.get("recording_space_threshold") or 0)
        output_dir = output_dir or self.settings.get_video_save_path()
        if utils.check_disk_capacity(output_dir) < disk_space_limit:
            self.app.recording_enabled = False
            logger.error(
                f"Disk space remaining is below {disk_space_limit} GB. Recording function disabled"
            )
            self.app.page.run_task(
                self.app.snack_bar.show_snack_bar,
                self._["not_disk_space_tip"],
                duration=86400,
                show_close_icon=True
            )

        else:
            self.app.recording_enabled = True

    @staticmethod
    async def get_scheduled_time_range(scheduled_start_time, monitor_hours) -> list | None:
        scheduled_time_range_list = []
        if not scheduled_start_time:
            return scheduled_time_range_list
            
        for index, start_time in enumerate(str(scheduled_start_time).split(',')):
            try:
                hours_list = str(monitor_hours or "").split(',')
                hours = hours_list[index] if index < len(hours_list) else "5"
                if start_time and hours:
                    end_time = utils.add_hours_to_time(start_time, float(hours or 5))
                    scheduled_time_range = f"{start_time}~{end_time}"
                    scheduled_time_range_list.append(scheduled_time_range)
            except Exception:
                pass
        return scheduled_time_range_list

    @staticmethod
    async def _reset_stopping_flag(recording: Recording):
        recording.stopping_in_progress = False
        logger.debug(f"Reset stopping_in_progress flag for recording: {recording.rec_id}")
