import random

class MockRecording:
    def __init__(self, name, live_check_count, live_found_count):
        self.streamer_name = name
        self.live_check_count = live_check_count
        self.live_found_count = live_found_count

    def __repr__(self):
        score = self.live_found_count / self.live_check_count if self.live_check_count > 0 else 0
        return f"{self.streamer_name} (ch:{self.live_check_count}, fd:{self.live_found_count}, score:{score:.2f})"

def get_priority_score(rec):
    if rec.live_check_count == 0:
        return 0
    return rec.live_found_count / rec.live_check_count

def test_sorting():
    recordings = [
        MockRecording("Stream_A_HighFreq", 100, 80),  # 0.8
        MockRecording("Stream_B_LowFreq", 100, 10),   # 0.1
        MockRecording("Stream_C_MidFreq", 100, 50),   # 0.5
        MockRecording("Stream_D_New", 0, 0),          # 0.0
        MockRecording("Stream_E_MidFreq2", 100, 50),  # 0.5
    ]

    print("Initial list:")
    for r in recordings:
        print(f"  {r}")

    # The sorting logic from RecordingManager
    sorted_recs = sorted(
        recordings,
        key=lambda r: (get_priority_score(r), random.random()),
        reverse=True
    )

    print("\nSorted list (Prioritized):")
    for r in sorted_recs:
        print(f"  {r}")

    # Basic assertions
    assert sorted_recs[0].streamer_name == "Stream_A_HighFreq"
    assert sorted_recs[-1].streamer_name == "Stream_D_New"
    
    # Check that mid-freq are before low-freq
    mid_freq_names = [r.streamer_name for r in sorted_recs if "MidFreq" in r.streamer_name]
    low_freq_index = next(i for i, r in enumerate(sorted_recs) if r.streamer_name == "Stream_B_LowFreq")
    for name in mid_freq_names:
        mid_index = next(i for i, r in enumerate(sorted_recs) if r.streamer_name == name)
        assert mid_index < low_freq_index

    # Final visual check for ties (MidFreq vs MidFreq2 should be random order but both above LowFreq)
    print("\nTest passed successfully!")

if __name__ == "__main__":
    test_sorting()
