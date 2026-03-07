from app.models.recording.recording_status_model import CardStateType, RecordingStatus

class RecordingStateLogic:
    ERROR_STATUSES = [RecordingStatus.RECORDING_ERROR, RecordingStatus.LIVE_STATUS_CHECK_ERROR]
    
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
