import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from PySide6.QtWidgets import QApplication

from app.models.recording.recording_model import Recording
from app.qt.views.stats_view import QtStatsView

_app = QApplication.instance() or QApplication([])


class StatsViewAggregationTests(unittest.TestCase):
    def _make_recording(self, **kwargs):
        defaults = {
            "rec_id": "r1",
            "url": "http://example.com",
            "streamer_name": "Test",
            "record_format": "mp4",
            "quality": "HD",
            "segment_record": False,
            "segment_time": 3600,
            "monitor_status": True,
            "scheduled_recording": False,
            "scheduled_start_time": None,
            "monitor_hours": 2,
            "recording_dir": "/tmp",
            "enabled_message_push": False,
            "only_notify_no_record": False,
            "flv_use_direct_download": False,
        }
        platform_key = kwargs.pop("platform_key", None)
        defaults.update(kwargs)
        rec = Recording(**defaults)
        if platform_key:
            rec.platform_key = platform_key
        return rec

    def _make_app(self, recordings=None):
        app = MagicMock()
        app.record_manager.recordings = recordings or []
        app.record_manager.predictor_metrics = MagicMock()
        app.language_manager.language = {
            "stats_view": {
                "stats": "Stats",
                "refresh": "Refresh",
                "tab_general": "General",
                "tab_heatmap": "Heatmap",
                "tab_predictor": "Predictor",
            }
        }
        return app

    def test_aggregate_general_empty(self):
        app = self._make_app()
        view = QtStatsView(app)
        data = view._aggregate_general_data()
        self.assertEqual(data["total_streamers"], 0)
        self.assertEqual(data["total_sessions"], 0)
        self.assertEqual(data["avg_priority"], 0.0)
        self.assertEqual(data["avg_consistency"], 0.0)
        self.assertEqual(data["streamers"], [])

    def test_aggregate_general_with_sessions(self):
        now = datetime.now()
        rec1 = self._make_recording(
            rec_id="r1",
            streamer_name="Alice",
            platform_key="twitch",
            priority_score=0.8,
            consistency_score=0.9,
            is_favorite=True,
            live_sessions=[
                {"start_time": now.isoformat(), "weekday": now.weekday(), "start_hour": now.hour, "duration_minutes": 30},
                {"start_time": (now - timedelta(hours=2)).isoformat(), "weekday": (now - timedelta(hours=2)).weekday(), "start_hour": (now - timedelta(hours=2)).hour, "duration_minutes": 45},
            ],
        )
        rec2 = self._make_recording(
            rec_id="r2",
            streamer_name="Bob",
            platform_key="youtube",
            priority_score=0.4,
            consistency_score=0.5,
            live_sessions=[
                {"start_time": (now - timedelta(days=1)).isoformat(), "weekday": (now - timedelta(days=1)).weekday(), "start_hour": 10, "duration_minutes": 60},
            ],
        )
        app = self._make_app([rec1, rec2])
        view = QtStatsView(app)
        data = view._aggregate_general_data()
        self.assertEqual(data["total_streamers"], 2)
        # Only sessions within 72h count
        self.assertEqual(data["total_sessions"], 3)
        self.assertAlmostEqual(data["avg_priority"], 0.6, places=5)
        self.assertAlmostEqual(data["avg_consistency"], 0.7, places=5)
        self.assertEqual(len(data["streamers"]), 2)
        # Default sort by sessions desc
        self.assertEqual(data["streamers"][0]["name"], "Alice")

    def test_build_heatmap_data_all_streamers(self):
        now = datetime.now()
        rec1 = self._make_recording(
            rec_id="r1",
            streamer_name="Alice",
            live_sessions=[
                {"start_time": now.isoformat(), "weekday": 1, "start_hour": 14},
                {"start_time": now.isoformat(), "weekday": 1, "start_hour": 14},
            ],
        )
        rec2 = self._make_recording(
            rec_id="r2",
            streamer_name="Bob",
            live_sessions=[
                {"start_time": now.isoformat(), "weekday": 3, "start_hour": 20},
            ],
        )
        app = self._make_app([rec1, rec2])
        view = QtStatsView(app)
        data = view._build_heatmap_data(None)
        self.assertEqual(len(data), 2)
        counts = {(d[0], d[1]): d[2] for d in data}
        self.assertEqual(counts[(1, 14)], 2)
        self.assertEqual(counts[(3, 20)], 1)

    def test_build_heatmap_data_filtered_streamer(self):
        now = datetime.now()
        rec1 = self._make_recording(
            rec_id="r1",
            streamer_name="Alice",
            live_sessions=[{"start_time": now.isoformat(), "weekday": 1, "start_hour": 14}],
        )
        rec2 = self._make_recording(
            rec_id="r2",
            streamer_name="Bob",
            live_sessions=[{"start_time": now.isoformat(), "weekday": 3, "start_hour": 20}],
        )
        app = self._make_app([rec1, rec2])
        view = QtStatsView(app)
        data = view._build_heatmap_data("r1")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], (1, 14, 1))


class StatsViewCacheTests(unittest.TestCase):
    def _make_app(self, recordings=None):
        app = MagicMock()
        app.record_manager.recordings = recordings or []
        app.record_manager.predictor_metrics = MagicMock()
        app.language_manager.language = {
            "stats_view": {
                "stats": "Stats",
                "refresh": "Refresh",
                "tab_general": "General",
                "tab_heatmap": "Heatmap",
                "tab_predictor": "Predictor",
            }
        }
        return app
    def test_cache_returns_fresh_data_after_expiry(self):
        app = self._make_app()
        view = QtStatsView(app)
        view._cache["general"] = ({"total_streamers": 5}, 0.0)  # expired
        data = view._get_cached_or_compute("general", view._aggregate_general_data)
        self.assertEqual(data["total_streamers"], 0)

    def test_cache_reuses_data_within_ttl(self):
        import time
        app = self._make_app()
        view = QtStatsView(app)
        view._cache["general"] = ({"total_streamers": 5}, time.time() + 60)
        data = view._get_cached_or_compute("general", view._aggregate_general_data)
        self.assertEqual(data["total_streamers"], 5)


if __name__ == "__main__":
    unittest.main()
