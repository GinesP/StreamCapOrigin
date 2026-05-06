import argparse
import json
import os
import sys
from pathlib import Path


def resolve_repo_root():
    return Path(__file__).resolve().parent.parent


REPO_ROOT = resolve_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.core.config.config_manager import ConfigManager
from app.core.recording.predictor_metrics import PredictorMetricsStore


def main(argv=None):
    parser = argparse.ArgumentParser(description="Predictor metrics JSONL summary report")
    parser.add_argument("--lookback-hours", type=int, default=72)
    parser.add_argument("--user-data-dir", default=os.environ.get("STREAMCAP_USER_DATA_DIR"))
    args = parser.parse_args(argv)

    config_manager = ConfigManager(str(REPO_ROOT), user_data_path=args.user_data_dir)
    metrics_path = Path(config_manager.config_path) / "predictor_metrics.jsonl"
    store = PredictorMetricsStore(metrics_path)
    summary = store.summarize(lookback_hours=args.lookback_hours)

    print(f"metrics_file={metrics_path}")
    print("notes=offline_checks_* are monitoring heuristics, not confirmed false positives/misses")
    print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
