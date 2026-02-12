from datetime import datetime
from ...models.recording.recording_model import Recording

class HistoryManager:
    @staticmethod
    def get_likelihood_score(recording: Recording) -> float:
        """
        Calculates a score between 0.0 and 1.0 representing how likely 
        the streamer is to be live right now based on historical data.
        """
        if not recording.historical_intervals:
            return 0.5  # Neutral score if no data
            
        now = datetime.now()
        day_str = str(now.weekday())
        current_hour = now.hour
        
        if day_str not in recording.historical_intervals:
            return 0.2  # Low score if they never stream on this day
            
        active_hours = recording.historical_intervals[day_str]
        
        # Check if they are currently within a known active hour
        if current_hour in active_hours:
            return 1.0
            
        # Check if they usually start soon (within next 1 hour)
        next_hour = (current_hour + 1) % 24
        if next_hour in active_hours:
            # High likelihood as they approach their usual start time
            minute_progress = now.minute / 60.0
            return 0.5 + (0.4 * minute_progress) # Ramps up from 0.5 to 0.9
            
        return 0.1  # Low likelihood if far from typical hours

    @staticmethod
    def get_adjusted_interval(recording: Recording, base_interval: int) -> int:
        """
        Returns an adjusted check interval based on the likelihood score.
        """
        likelihood = HistoryManager.get_likelihood_score(recording)
        
        if likelihood >= 0.9:
            return 60  # Check every minute in high-probability windows
        elif likelihood >= 0.5:
            return base_interval // 2  # Double the frequency
        elif likelihood <= 0.2:
            return base_interval * 2  # Half the frequency
            
        return base_interval
