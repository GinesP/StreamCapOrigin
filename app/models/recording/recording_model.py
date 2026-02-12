from datetime import timedelta


class Recording:
    def __init__(
        self,
        rec_id,
        url,
        streamer_name,
        record_format,
        quality,
        segment_record,
        segment_time,
        monitor_status,
        scheduled_recording,
        scheduled_start_time,
        monitor_hours,
        recording_dir,
        enabled_message_push,
        only_notify_no_record,
        flv_use_direct_download,
        live_check_count=0,
        live_found_count=0,
        priority_score=0.0,
        added_at=None,
        last_active_at=None,
        historical_intervals=None,
        last_seen_live=None,
        consistency_score=0.0
    ):
        """
        Initialize a recording object.

        :param rec_id: Unique identifier for the recording task.
        :param url: URL address of the live stream.
        :param streamer_name: Name of the streamer.
        :param record_format: Format of the recorded file, e.g., 'mp4', 'ts', 'mkv'.
        :param quality: Quality of the recorded video, e.g., 'OD', 'UHD', 'HD'.
        :param segment_record: Whether to enable segmented recording.
        :param segment_time: Time interval (in seconds) for segmented recording if enabled.
        :param monitor_status: Monitoring status, whether the live room is being monitored.
        :param scheduled_recording: Whether to enable scheduled recording.
        :param scheduled_start_time: Scheduled start time for recording (string format like '18:30:00').
        :param monitor_hours: Number of hours to monitor from the scheduled recording start time, e.g., 3.
        :param recording_dir: Directory path where the recorded files will be saved.
        :param enabled_message_push: Whether to enable message push.
        :param only_notify_no_record: Whether to only notify when no record is made.
        :param flv_use_direct_download: Whether to use direct downloader to cache FLV stream.
        """

        self.rec_id = rec_id
        self.url = url
        self.quality = quality
        self.record_format = record_format
        self.monitor_status = monitor_status
        self.segment_record = segment_record
        self.segment_time = segment_time
        self.streamer_name = streamer_name
        self.scheduled_recording = scheduled_recording
        self.scheduled_start_time = scheduled_start_time
        self.monitor_hours = monitor_hours
        self.recording_dir = recording_dir
        self.enabled_message_push = enabled_message_push
        self.only_notify_no_record = only_notify_no_record
        self.flv_use_direct_download = flv_use_direct_download
        self.live_check_count = live_check_count
        self.live_found_count = live_found_count
        self.priority_score = priority_score or (live_found_count / live_check_count if live_check_count > 0 else 0.0)
        self.added_at = added_at
        self.last_active_at = last_active_at

        # Intelligence fields
        self.historical_intervals = historical_intervals or {}  # Format: {"0": [8, 9, 20], "1": ...} (day: [hours])
        self.last_seen_live = last_seen_live  # ISO format string
        self.consistency_score = consistency_score
        
        self.scheduled_time_range = None
        self.title = f"{streamer_name} - {self.quality}"
        self.speed = "X KB/s"
        self.is_live = False
        self.is_recording = False
        self.start_time = None
        self.manually_stopped = False
        self.force_stop = False
        self.stopping_in_progress = False
        self.stop_requested = False
        self.platform = None
        self.platform_key = None
        self.notified_live_start = False
        self.notified_live_end = False

        self.cumulative_duration = timedelta()  # Accumulated recording time
        self.last_duration = timedelta()  # Save the total time of the last recording
        self.display_title = self.title
        self.selected = False
        self.is_checking = False
        self.showed_checking_status = False
        self.status_info = None
        self.live_title = None
        self.detection_time = None
        self.loop_time_seconds = None
        self.use_proxy = None
        self.record_url = None
        self.preview_url = None

    def to_dict(self):
        """Convert the Recording instance to a dictionary for saving."""
        return {
            "rec_id": self.rec_id,
            "url": self.url,
            "streamer_name": self.streamer_name,
            "record_format": self.record_format,
            "quality": self.quality,
            "segment_record": self.segment_record,
            "segment_time": self.segment_time,
            "monitor_status": self.monitor_status,
            "scheduled_recording": self.scheduled_recording,
            "scheduled_start_time": self.scheduled_start_time,
            "monitor_hours": self.monitor_hours,
            "recording_dir": self.recording_dir,
            "enabled_message_push": self.enabled_message_push,
            "platform": self.platform,
            "platform_key": self.platform_key,
            "only_notify_no_record": self.only_notify_no_record,
            "flv_use_direct_download": self.flv_use_direct_download,
            "live_check_count": self.live_check_count,
            "live_found_count": self.live_found_count,
            "priority_score": self.priority_score,
            "added_at": self.added_at,
            "last_active_at": self.last_active_at,
            "historical_intervals": self.historical_intervals,
            "last_seen_live": self.last_seen_live,
            "consistency_score": self.consistency_score
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Recording instance from a dictionary."""
        recording = cls(
            rec_id=data.get("rec_id"),
            url=data.get("url"),
            streamer_name=data.get("streamer_name"),
            record_format=data.get("record_format"),
            quality=data.get("quality"),
            segment_record=data.get("segment_record"),
            segment_time=data.get("segment_time"),
            monitor_status=data.get("monitor_status"),
            scheduled_recording=data.get("scheduled_recording"),
            scheduled_start_time=data.get("scheduled_start_time"),
            monitor_hours=data.get("monitor_hours"),
            recording_dir=data.get("recording_dir"),
            enabled_message_push=data.get("enabled_message_push"),
            only_notify_no_record=data.get("only_notify_no_record"),
            flv_use_direct_download=data.get("flv_use_direct_download"),
            live_check_count=data.get("live_check_count", 0),
            live_found_count=data.get("live_found_count", 0),
            priority_score=data.get("priority_score", 0.0),
            added_at=data.get("added_at"),
            last_active_at=data.get("last_active_at"),
            historical_intervals=data.get("historical_intervals"),
            last_seen_live=data.get("last_seen_live"),
            consistency_score=data.get("consistency_score", 0.0)
        )
        recording.title = data.get("title", recording.title)
        recording.display_title = data.get("display_title", recording.title)
        recording.last_duration_str = data.get("last_duration")
        recording.platform = data.get("platform")
        recording.platform_key = data.get("platform_key")
        if recording.last_duration_str is not None:
            recording.last_duration = timedelta(seconds=float(recording.last_duration_str))
        return recording

    def increment_live_counts(self, is_live: bool, alpha_active: float = 0.1, alpha_offline: float = 0.005):
        """
        Update priority score using Multi-Dimensional EMA.
        Includes recency decay for long-term inactivity and tracks scheduling patterns.
        """
        from datetime import datetime
        now = datetime.now()

        # 1. Update historical patterns (Scheduling Intelligence)
        if is_live:
            day_str = str(now.weekday())
            hour = now.hour
            if day_str not in self.historical_intervals:
                self.historical_intervals[day_str] = []
            if hour not in self.historical_intervals[day_str]:
                self.historical_intervals[day_str].append(hour)
                # Keep only last 5 entries per day to detect shifts in schedule
                if len(self.historical_intervals[day_str]) > 5:
                    self.historical_intervals[day_str].pop(0)

            self.last_seen_live = now.isoformat()

        # 1.1 Calculate Consistency (Density of schedule)
        if self.historical_intervals:
            # Ratio of total recorded slots vs max possible slots (5 per active day)
            total_slots = sum(len(hours) for hours in self.historical_intervals.values())
            num_days = len(self.historical_intervals)
            # Normalized score: how "full" are their usual 5-slot windows
            self.consistency_score = total_slots / (num_days * 5.0)

        # 2. Base EMA logic
        alpha = alpha_active if is_live else alpha_offline
        current_val = 1.0 if is_live else 0.0
        self.priority_score = (self.priority_score * (1 - alpha)) + (current_val * alpha)

        # 3. Recency Decay (Intelligence)
        # If not seen live for > 30 days, accelerate decay
        if self.last_seen_live:
            last_seen = datetime.fromisoformat(self.last_seen_live)
            days_inactive = (now - last_seen).days
            if days_inactive > 30:
                # Apply 1% extra decay per day over 30
                decay_days = min(days_inactive - 30, 60) # Cap extra decay
                extra_decay = 0.99 ** decay_days
                self.priority_score *= extra_decay

        # Update legacy counts
        self.live_check_count += 1
        if is_live:
            self.live_found_count += 1
            
        if self.live_check_count > 100:
            self.live_check_count //= 2
            self.live_found_count //= 2

    def update_title(self, quality_info, prefix=None):
        """Helper method to update the title."""
        self.title = f"{self.streamer_name} - {quality_info}"
        self.display_title = f"{prefix or ''}{self.title}"

    def update(self, updated_info: dict):
        """Update the recording object with new information."""
        for attr, value in updated_info.items():
            if hasattr(self, attr):
                setattr(self, attr, value)
