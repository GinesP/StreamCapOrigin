import random
import os
import sys

# Add project root to sys.path to import models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.recording.recording_model import Recording

def get_priority_score(rec):
    if rec.live_check_count == 0:
        return 0
    return rec.live_found_count / rec.live_check_count

def test_decay_logic():
    print("--- Testing Decay Logic ---")
    rec = Recording(
        rec_id="test", url="test.com", streamer_name="TestStreamer",
        record_format="mp4", quality="OD", segment_record=False,
        segment_time=3600, monitor_status=True, scheduled_recording=False,
        scheduled_start_time="00:00:00", monitor_hours=24, recording_dir=".",
        enabled_message_push=False, only_notify_no_record=False, flv_use_direct_download=False
    )

    # Simulate 200 non-live checks
    print("Simulating 200 non-live checks...")
    for _ in range(200):
        rec.increment_live_counts(is_live=False)
    
    print(f"Stats after 200 checks: {rec.live_check_count} checks, {rec.live_found_count} found, score: {get_priority_score(rec):.4f}")
    assert rec.live_check_count == 200
    assert rec.live_found_count == 0

    # The 201st check should trigger decay
    print("\nTriggering decay (201st check)...")
    rec.increment_live_counts(is_live=False)
    print(f"Stats after 201st check (decayed): {rec.live_check_count} checks, {rec.live_found_count} found, score: {get_priority_score(rec):.4f}")
    # 201 // 2 = 100
    assert rec.live_check_count == 100
    assert rec.live_found_count == 0

    # Now simulate the streamer becoming active
    print("\nStreamer becomes active! Simulating 50 live checks...")
    for _ in range(50):
        rec.increment_live_counts(is_live=True)
    
    final_score = get_priority_score(rec)
    print(f"Final stats: {rec.live_check_count} checks, {rec.live_found_count} found, score: {final_score:.4f}")
    
    # Without decay, they would have had 251 checks and 50 found (score 0.199)
    # With decay, they have 150 checks and 50 found (score 0.333)
    print(f"With decay, the score is more responsive to recent activity (0.33 vs ~0.20)")
    assert final_score > 0.3 # Should be ~0.33

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
