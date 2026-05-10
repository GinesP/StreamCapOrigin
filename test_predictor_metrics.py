import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from pathlib import Path

from app.core.recording.predictor_metrics import MetricsSummary, PredictorMetricsStore
from scripts import predictor_metrics_report


class PredictorMetricsStoreTests(unittest.TestCase):
    def test_record_event_appends_jsonl_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = PredictorMetricsStore(Path(temp_dir) / "predictor_metrics.jsonl")

            store.record_event("check_dispatched", {"rec_id": "r-1", "loop_time_seconds": 60})
            store.record_event("check_result", {"rec_id": "r-1", "is_live": False})

            lines = store.file_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            first_row = json.loads(lines[0])
            second_row = json.loads(lines[1])
            self.assertEqual(first_row["event"], "check_dispatched")
            self.assertEqual(second_row["event"], "check_result")

    def test_summary_uses_honest_naming_and_expected_counts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = PredictorMetricsStore(Path(temp_dir) / "predictor_metrics.jsonl")
            store.file_path.write_text(
                "\n".join(
                    [
                        json.dumps({
                            "timestamp": "2026-05-03T09:00:00",
                            "event": "check_result",
                            "payload": {"rec_id": "rec-1", "is_live": False, "loop_time_seconds": 300},
                        }),
                        json.dumps({
                            "timestamp": "2026-05-03T09:03:00",
                            "event": "check_result",
                            "payload": {
                                "rec_id": "rec-1",
                                "is_live": True,
                                "loop_time_seconds": 300,
                                "detection_latency_seconds": 180,
                            },
                        }),
                        json.dumps({
                            "timestamp": "2026-05-03T09:30:00",
                            "event": "check_result",
                            "payload": {"rec_id": "rec-2", "is_live": False, "loop_time_seconds": 180},
                        }),
                    ]
                ) + "\n",
                encoding="utf-8",
            )

            summary = store.summarize(lookback_hours=99999, near_live_minutes=15)

            self.assertEqual(summary.total_checks, 3)
            self.assertEqual(summary.live_detections, 1)
            self.assertEqual(summary.non_live_results, 2)
            self.assertEqual(summary.offline_checks_with_near_live_followup, 1)
            self.assertEqual(summary.offline_checks_without_near_live_followup, 1)
            self.assertEqual(summary.live_detections_after_offline_check, 1)
            self.assertEqual(summary.avg_detection_latency_seconds, 180.0)
            self.assertEqual(summary.avg_lead_minutes_vs_interval, 2.0)
            self.assertEqual(
                summary.to_dict()["offline_checks_without_near_live_followup"],
                1,
            )

    def test_metrics_summary_to_dict_has_expected_keys(self):
        summary = MetricsSummary(
            total_checks=1,
            live_detections=1,
            non_live_results=0,
            offline_checks_without_near_live_followup=0,
            offline_checks_with_near_live_followup=0,
            live_detections_after_offline_check=0,
            avg_detection_latency_seconds=None,
            avg_lead_minutes_vs_interval=None,
        )

        self.assertEqual(
            summary.to_dict(),
            {
                "total_checks": 1,
                "live_detections": 1,
                "non_live_results": 0,
                "offline_checks_without_near_live_followup": 0,
                "offline_checks_with_near_live_followup": 0,
                "live_detections_after_offline_check": 0,
                "avg_detection_latency_seconds": None,
                "avg_lead_minutes_vs_interval": None,
                "latency_p50": None,
                "latency_p95": None,
                "latency_p99": None,
                "dispatch_p50": None,
                "dispatch_p95": None,
                "dispatch_fast": 0,
                "dispatch_medium": 0,
                "dispatch_slow": 0,
                "lives_fast": 0,
                "lives_medium": 0,
                "lives_slow": 0,
                "avg_likelihood_at_dispatch": None,
                "avg_likelihood_fast": None,
                "avg_likelihood_medium": None,
                "avg_likelihood_slow": None,
                "lh_fast_p50": None,
                "lh_medium_p50": None,
                "lh_slow_p50": None,
                "lh_slow_min": None,
                "lh_slow_max": None,
                "note_lead_is_interval_artifact": True,
            },
        )


class PredictorMetricsReportTests(unittest.TestCase):
    def test_report_prints_metrics_file_note_and_summary_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            metrics_store = PredictorMetricsStore(Path(temp_dir) / "config" / "predictor_metrics.jsonl")
            metrics_store.record_event("check_dispatched", {"rec_id": "r-1", "loop_time_seconds": 60})
            metrics_store.record_event("check_result", {"rec_id": "r-1", "is_live": False})

            output = io.StringIO()
            with redirect_stdout(output):
                predictor_metrics_report.main([
                    "--user-data-dir",
                    temp_dir,
                    "--lookback-hours",
                    "24",
                ])

            rendered = output.getvalue()
            self.assertIn("metrics_file=", rendered)
            self.assertIn(
                "notes=offline_checks_* are monitoring heuristics, not confirmed false positives/misses",
                rendered,
            )
            self.assertIn("total_checks", rendered)
            self.assertIn("offline_checks_without_near_live_followup", rendered)

    def test_resolve_repo_root_points_to_project_root(self):
        root = predictor_metrics_report.resolve_repo_root()
        self.assertTrue((root / "app").exists())


if __name__ == "__main__":
    unittest.main()
