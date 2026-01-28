import random
import os
import sys

# Add project root to sys.path to import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.recording.recording_model import Recording

def get_priority_score(rec):
    return getattr(rec, 'priority_score', 0.0)

def test_decay_logic():
    print("--- Testing Decay Logic (EMA) ---")
    rec = Recording(
        rec_id="test", url="test.com", streamer_name="TestStreamer",
        record_format="mp4", quality="OD", segment_record=False,
        segment_time=3600, monitor_status=True, scheduled_recording=False,
        scheduled_start_time="00:00:00", monitor_hours=24, recording_dir=".",
        enabled_message_push=False, only_notify_no_record=False, flv_use_direct_download=False
    )

    # Initial score should be 0
    assert rec.priority_score == 0.0

    # Simulate 100 non-live checks
    print("Simulating 100 non-live checks...")
    for _ in range(100):
        rec.increment_live_counts(is_live=False)
    
    # Score should still be 0 (or very close to it)
    print(f"Stats after 100 checks: {rec.live_check_count} legacy checks, score: {get_priority_score(rec):.4f}")
    assert rec.priority_score == 0.0
    assert rec.live_check_count == 100

    # The 101st check should trigger legacy decay
    print("\nTriggering legacy decay (101st check)...")
    rec.increment_live_counts(is_live=False)
    print(f"Stats after 101st check: {rec.live_check_count} legacy checks, score: {get_priority_score(rec):.4f}")
    assert rec.live_check_count == 50

    # Now simulate the streamer becoming active
    print("\nStreamer becomes active! Simulating 10 live checks...")
    for _ in range(10):
        rec.increment_live_counts(is_live=True)
    
    final_score = get_priority_score(rec)
    print(f"Final stats: {rec.live_check_count} checks, score: {final_score:.4f}")
    
    # With alpha = 0.1, after 10 live checks starting from 0:
    # score = 1 - (1-0.1)^10 = 1 - 0.348 = 0.651
    print(f"EMA Score after 10 live checks: {final_score:.4f} (Expected ~0.65)")
    assert 0.6 < final_score < 0.7

def test_sorting_with_decay():
    print("\n--- Testing Sorting with Decay ---")
    # A has been very active but recently skipped a few
    a = Recording("a", "url", "Stream_A", "mp4", "OD", False, 3600, True, False, "00:00", 24, ".", False, False, False, live_check_count=180, live_found_count=150)
    
    # B was dead for a long time but just "woke up"
    # Old counts: 200 checks, 0 found -> decayed to 100/0 -> recently 50/50 -> total 150/50
    b = Recording("b", "url", "Stream_B", "mp4", "OD", False, 3600, True, False, "00:00", 24, ".", False, False, False, live_check_count=150, live_found_count=50)

    # C is new
    c = Recording("c", "url", "Stream_C", "mp4", "OD", False, 3600, True, False, "00:00", 24, ".", False, False, False, live_check_count=10, live_found_count=5)

    recs = [a, b, c]
    sorted_recs = sorted(recs, key=lambda r: get_priority_score(r), reverse=True)
    
    print("Sorted list:")
    for r in sorted_recs:
        print(f"  {r.streamer_name}: {get_priority_score(r):.4f} ({r.live_check_count}/{r.live_found_count})")

    assert sorted_recs[0].streamer_name == "Stream_A"
    assert sorted_recs[1].streamer_name == "Stream_C"
    assert sorted_recs[2].streamer_name == "Stream_B"

if __name__ == "__main__":
    try:
        test_decay_logic()
        test_sorting_with_decay()
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"\nTest failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
