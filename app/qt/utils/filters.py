from app.models.recording.recording_status_model import RecordingStatus

class RecordingFilters:
    @staticmethod
    def is_error(recording) -> bool:
        # ERROR_STATUSES from RecordingCardState
        error_statuses = [RecordingStatus.RECORDING_ERROR, RecordingStatus.LIVE_STATUS_CHECK_ERROR]
        return recording.status_info in error_statuses
    
    @staticmethod
    def is_live(recording) -> bool:
        return (recording.is_live 
                and recording.monitor_status 
                and not recording.is_recording
                and not RecordingFilters.is_error(recording)
                and recording.status_info != RecordingStatus.NOT_IN_SCHEDULED_CHECK)
    
    @staticmethod
    def is_offline(recording) -> bool:
        return (not recording.is_live
                and recording.monitor_status
                and not RecordingFilters.is_error(recording)
                and recording.status_info != RecordingStatus.NOT_IN_SCHEDULED_CHECK)
    
    @staticmethod
    def is_stopped(recording) -> bool:
        return (not recording.monitor_status
                or recording.status_info == RecordingStatus.NOT_IN_SCHEDULED_CHECK)

    @classmethod
    def matches_status(cls, recording, filter_type) -> bool:
        if filter_type == "all": return True
        if filter_type == "recording": return recording.is_recording
        if filter_type == "living": return cls.is_live(recording)
        if filter_type == "error": return cls.is_error(recording)
        if filter_type == "offline": return cls.is_offline(recording)
        if filter_type == "stopped": return cls.is_stopped(recording)
        return True

    @classmethod
    def matches_platform(cls, recording, platform_key) -> bool:
        return platform_key == "all" or recording.platform_key == platform_key

    @classmethod
    def matches_search(cls, recording, query) -> bool:
        if not query: return True
        q = query.lower()
        return (q in recording.streamer_name.lower() or 
                (getattr(recording, 'live_title', '') or '').lower().find(q) != -1 or
                q in recording.url.lower())
