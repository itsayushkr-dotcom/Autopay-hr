"""
Generate segments.jsonl for Dataset B (Deliverable 1)
Runs the tuned segmentation engine across all 15 sessions of Dataset B.
"""
import os
import sys
import glob
import json
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.append('src')
from segmentation_engine import segment_session

DATASET_B_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_b"
OUTPUT_FILE = r"C:\Users\itsay\AI_Engineer\segments.jsonl"

def generate_all_segments():
    sessions = sorted([
        d for d in glob.glob(os.path.join(DATASET_B_PATH, "ses_*"))
        if os.path.isdir(d)
    ])
    print(f"Starting batch segmentation for {len(sessions)} sessions in Dataset B...")
    
    total_segments = 0
    all_output_lines = []
    session_counts = {}
    label_counts = {}
    
    for ses in sessions:
        ses_id = os.path.basename(ses)
        chunk_dirs = sorted(glob.glob(os.path.join(ses, "chunk_*")))
        
        events = []
        for cd in chunk_dirs:
            ef = os.path.join(cd, "events.jsonl")
            if os.path.exists(ef):
                with open(ef, "r", encoding="utf-8") as f:
                    for l in f:
                        if l.strip():
                            events.append(json.loads(l))
                            
        events.sort(key=lambda x: x["timestamp_ms"])
        
        # Segment session with optimized parameters
        preds = segment_session(events, min_segment_dur=12.0, idle_split_sec=5.0)
        session_counts[ses_id] = len(preds)
        total_segments += len(preds)
        
        for p in preds:
            lbl = p["label"]
            label_counts[lbl] = label_counts.get(lbl, 0) + 1
            line_obj = {
                "session_id": ses_id,
                "start": p["start_iso"],
                "end": p["end_iso"],
                "label": lbl
            }
            all_output_lines.append(json.dumps(line_obj, ensure_ascii=False))
            
    # Write to segments.jsonl
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for line in all_output_lines:
            f.write(line + "\n")
            
    print(f"\nSuccessfully generated {total_segments} segments in '{OUTPUT_FILE}'!")
    print("\n--- Segments per Session ---")
    for s, c in session_counts.items():
        print(f"  {s}: {c} segments")
        
    print("\n--- Process Label Distribution ---")
    for l, c in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {l:40s}: {c} executions")

if __name__ == "__main__":
    generate_all_segments()
