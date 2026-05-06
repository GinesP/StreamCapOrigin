import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


def _utcnow() -> datetime:
    return datetime.utcnow()


@dataclass(frozen=True)
class MetricsSummary:
    total_checks: int
    live_detections: int
    non_live_results: int
    offline_checks_without_near_live_followup: int
    offline_checks_with_near_live_followup: int
    live_detections_after_offline_check: int
    avg_detection_latency_seconds: float | None
    avg_lead_minutes_vs_interval: float | None

    def to_dict(self) -> dict:
        return {
            "total_checks": self.total_checks,
            "live_detections": self.live_detections,
            "non_live_results": self.non_live_results,
            "offline_checks_without_near_live_followup": self.offline_checks_without_near_live_followup,
            "offline_checks_with_near_live_followup": self.offline_checks_with_near_live_followup,
            "live_detections_after_offline_check": self.live_detections_after_offline_check,
            "avg_detection_latency_seconds": self.avg_detection_latency_seconds,
            "avg_lead_minutes_vs_interval": self.avg_lead_minutes_vs_interval,
        }


class PredictorMetricsStore:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def record_event(self, event_type: str, payload: dict) -> None:
        entry = {
            "timestamp": _utcnow().isoformat(),
            "event": event_type,
            "payload": payload,
        }
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            with self.file_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def summarize(self, lookback_hours: int = 72, near_live_minutes: int = 15) -> MetricsSummary:
        horizon_start = _utcnow() - timedelta(hours=max(1, int(lookback_hours)))
        records = self._load_records_after(horizon_start)
        results = [item for item in records if item.get("event") == "check_result"]

        total_checks = len(results)
        live_detections = sum(1 for item in results if bool(item.get("payload", {}).get("is_live")))
        non_live_results = total_checks - live_detections

        by_rec: dict[str, list[dict]] = {}
        for item in results:
            rec_id = str(item.get("payload", {}).get("rec_id") or "")
            if not rec_id:
                continue
            by_rec.setdefault(rec_id, []).append(item)

        offline_checks_without_near_live_followup = 0
        offline_checks_with_near_live_followup = 0
        live_detections_after_offline_check = 0
        detection_latencies = []
        lead_minutes = []
        near_live_delta = timedelta(minutes=max(1, int(near_live_minutes)))

        for events in by_rec.values():
            ordered = sorted(events, key=lambda item: item.get("timestamp", ""))
            for idx, current in enumerate(ordered):
                payload = current.get("payload", {})
                ts = self._parse_ts(current.get("timestamp"))
                if ts is None:
                    continue

                if payload.get("is_live"):
                    if idx > 0:
                        prev = ordered[idx - 1]
                        prev_payload = prev.get("payload", {})
                        prev_ts = self._parse_ts(prev.get("timestamp"))
                        if prev_ts and not prev_payload.get("is_live"):
                            latency = (ts - prev_ts).total_seconds()
                            if latency >= 0:
                                detection_latencies.append(latency)
                                live_detections_after_offline_check += 1
                    check_interval = payload.get("loop_time_seconds")
                    detection_latency_seconds = payload.get("detection_latency_seconds")
                    if isinstance(check_interval, (int, float)) and isinstance(detection_latency_seconds, (int, float)):
                        lead = (float(check_interval) - float(detection_latency_seconds)) / 60.0
                        lead_minutes.append(lead)
                    continue

                has_near_live = False
                for future in ordered[idx + 1:]:
                    future_payload = future.get("payload", {})
                    if not future_payload.get("is_live"):
                        continue
                    future_ts = self._parse_ts(future.get("timestamp"))
                    if future_ts is None:
                        continue
                    if future_ts - ts <= near_live_delta:
                        has_near_live = True
                    break
                if has_near_live:
                    offline_checks_with_near_live_followup += 1
                else:
                    offline_checks_without_near_live_followup += 1

        return MetricsSummary(
            total_checks=total_checks,
            live_detections=live_detections,
            non_live_results=non_live_results,
            offline_checks_without_near_live_followup=offline_checks_without_near_live_followup,
            offline_checks_with_near_live_followup=offline_checks_with_near_live_followup,
            live_detections_after_offline_check=live_detections_after_offline_check,
            avg_detection_latency_seconds=(sum(detection_latencies) / len(detection_latencies)) if detection_latencies else None,
            avg_lead_minutes_vs_interval=(sum(lead_minutes) / len(lead_minutes)) if lead_minutes else None,
        )

    def _load_records_after(self, horizon_start: datetime) -> list[dict]:
        if not self.file_path.exists():
            return []
        records = []
        with self.file_path.open("r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                ts = self._parse_ts(item.get("timestamp"))
                if ts is None or ts < horizon_start:
                    continue
                records.append(item)
        return records

    @staticmethod
    def _parse_ts(value) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None
