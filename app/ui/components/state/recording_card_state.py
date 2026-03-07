import flet as ft

from ....models.recording.recording_model import Recording
from ....models.recording.recording_status_model import CardStateType, RecordingStatus


class RecordingCardState:
    
    ERROR_STATUSES = [RecordingStatus.RECORDING_ERROR, RecordingStatus.LIVE_STATUS_CHECK_ERROR]
    
    @staticmethod
    def get_card_state(recording: Recording) -> CardStateType:
        from ....core.recording.recording_state_logic import RecordingStateLogic
        return RecordingStateLogic.get_card_state(recording)
    
    @staticmethod
    def get_border_color(recording: Recording) -> ft.Colors:
        state = RecordingCardState.get_card_state(recording)
        color_map = {
            CardStateType.RECORDING: "#2ECC71",
            CardStateType.ERROR: "#F39C12",
            CardStateType.LIVE: "#E74C3C",
            CardStateType.OFFLINE: "#95A5A6",
            CardStateType.STOPPED: "#34495E",
            CardStateType.CHECKING: "#9B59B6",
        }
        return color_map.get(state, ft.Colors.TRANSPARENT)
    
    @staticmethod
    def get_status_label_config(recording: Recording, language_dict: dict) -> dict:
        state = RecordingCardState.get_card_state(recording)
        
        configs = {
            CardStateType.RECORDING: {
                "text": language_dict.get("recording"),
                "bgcolor": "#2ECC71",
                "text_color": ft.Colors.WHITE,
            },
            CardStateType.ERROR: {
                "text": language_dict.get("recording_error"),
                "bgcolor": "#F39C12",
                "text_color": ft.Colors.WHITE,
            },
            CardStateType.LIVE: {
                "text": language_dict.get("live_broadcasting"),
                "bgcolor": "#E74C3C",
                "text_color": ft.Colors.WHITE,
            },
            CardStateType.OFFLINE: {
                "text": language_dict.get("offline"),
                "bgcolor": "#95A5A6",
                "text_color": ft.Colors.WHITE,
            },
            CardStateType.STOPPED: {
                "text": language_dict.get("no_monitor"),
                "bgcolor": "#34495E",
                "text_color": ft.Colors.WHITE,
            },
            CardStateType.CHECKING: {
                "text": language_dict.get("checking"),
                "bgcolor": "#9B59B6",
                "text_color": ft.Colors.WHITE,
            },
        }
        
        return configs.get(state, {})
    
    @staticmethod
    def get_display_title(recording: Recording, language_dict: dict) -> str:
        if recording.is_live and getattr(recording, "live_title", None):
            title = f"{recording.streamer_name} - {recording.live_title}"
        else:
            title = recording.streamer_name
            
        return title
    
    @staticmethod
    def get_title_weight(recording: Recording) -> ft.FontWeight:
        return ft.FontWeight.BOLD if recording.is_recording or recording.is_live or recording.is_checking else None
    
    @staticmethod
    def get_recording_icon(recording: Recording) -> ft.Icons:
        return ft.Icons.STOP_CIRCLE if recording.is_recording else ft.Icons.PLAY_CIRCLE
    
    @staticmethod
    def get_monitor_icon(recording: Recording) -> ft.Icons:
        return ft.Icons.VISIBILITY if recording.monitor_status else ft.Icons.VISIBILITY_OFF
