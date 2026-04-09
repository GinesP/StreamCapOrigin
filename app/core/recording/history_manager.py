import random
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
        Returns an adjusted check interval based on the likelihood score and priority score.
        Applies a 15% jitter to prevent thundering herd / predictable bot patterns.
        """
        # 1. Deep Sleep Check (Anti-Bot & Resource Optimization)
        # If the channel is practically dead (priority score near 0)
        # Wait at least 1 hour (3600 seconds) between checks
        if getattr(recording, 'priority_score', 0.0) < 0.01 and recording.live_check_count > 10:
            target_interval = 3600
        else:
            # 2. Regular Likelihood Adjustment
            likelihood = HistoryManager.get_likelihood_score(recording)
            
            if likelihood >= 0.9:
                target_interval = 60  # Check every minute in high-probability windows
            elif likelihood >= 0.5:
                target_interval = base_interval // 2  # Double the frequency
            elif likelihood <= 0.2:
                target_interval = base_interval * 2  # Half the frequency
            else:
                target_interval = base_interval

        # 3. Apply 15% Jitter (Anti-Bot Pattern Randomization)
        # Calculates a random value between 85% and 115% of the target interval
        jitter_min = int(target_interval * 0.85)
        jitter_max = int(target_interval * 1.15)
        
        # Ensure we don't go below a sensible minimum (e.g., 45 seconds)
        jitter_min = max(45, jitter_min)
        jitter_max = max(jitter_min + 5, jitter_max)
        
        return random.randint(jitter_min, jitter_max)
