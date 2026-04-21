from app.models.recording.recording_status_model import CardStateType, RecordingStatus

class RecordingStateLogic:
    ERROR_STATUSES = [RecordingStatus.RECORDING_ERROR, RecordingStatus.LIVE_STATUS_CHECK_ERROR]
    ACTIVE_RECORDING_STATUSES = [RecordingStatus.RECORDING, RecordingStatus.PREPARING_RECORDING]
    
    @staticmethod
    def get_card_state(recording) -> CardStateType:
        if recording.is_recording:
            return CardStateType.RECORDING
        elif recording.status_info in RecordingStateLogic.ERROR_STATUSES:
            return CardStateType.ERROR
        elif getattr(recording, "is_checking", False):
            return CardStateType.CHECKING
        elif recording.is_live and recording.monitor_status and not recording.is_recording:
            return CardStateType.LIVE
        elif (not recording.is_live and recording.monitor_status and
              recording.status_info != RecordingStatus.NOT_IN_SCHEDULED_CHECK):
            return CardStateType.OFFLINE
        elif (not recording.monitor_status or 
              recording.status_info == RecordingStatus.NOT_IN_SCHEDULED_CHECK):
            return CardStateType.STOPPED
        return CardStateType.UNKNOWN

    @classmethod
    def is_actively_recording(cls, recording) -> bool:
        return bool(
            getattr(recording, "is_recording", False)
            or getattr(recording, "status_info", None) in cls.ACTIVE_RECORDING_STATUSES
        )

    @classmethod
    def should_show_duration(cls, recording) -> bool:
        return cls.is_actively_recording(recording)

    @classmethod
    def should_show_live_title(cls, recording) -> bool:
        return cls.is_actively_recording(recording) and bool(getattr(recording, "live_title", None))

    @classmethod
    def has_active_session(cls, recording) -> bool:
        return cls.is_actively_recording(recording) or bool(getattr(recording, "monitor_status", False))

    @classmethod
    def should_show_stop_monitoring_action(cls, recording) -> bool:
        return bool(
            getattr(recording, "monitor_status", False)
            and cls.is_actively_recording(recording)
        )
