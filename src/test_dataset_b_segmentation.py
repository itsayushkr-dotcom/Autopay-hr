"""
Test Segmentation Engine on Dataset B Sample
"""
import os
import sys
import glob
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.append('src')
from segmentation_engine import segment_session

DATASET_B_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_b"

def test_dataset_b_sample():
    sample_ses = os.path.join(DATASET_B_PATH, "ses_20260701-183232-LAPTOP-76QMG9DE")
    ses_id = os.path.basename(sample_ses)
    
    events = []
    for cd in sorted(glob.glob(os.path.join(sample_ses, "chunk_*"))):
        ef = os.path.join(cd, "events.jsonl")
        if os.path.exists(ef):
            with open(ef, "r", encoding="utf-8") as f:
                for l in f:
                    if l.strip(): events.append(json.loads(l))
    events.sort(key=lambda x: x["timestamp_ms"])
    
    print(f"Loaded {len(events)} events for {ses_id}")
    
    segments = segment_session(events, min_segment_dur=12.0, idle_split_sec=5.0)
    print(f"Generated {len(segments)} segments for {ses_id}:\n")
    
    for s in segments:
        output_format = {
            "session_id": ses_id,
            "start": s["start_iso"],
            "end": s["end_iso"],
            "label": s["label"]
        }
        print(json.dumps(output_format, ensure_ascii=False))

if __name__ == "__main__":
    test_dataset_b_sample()
