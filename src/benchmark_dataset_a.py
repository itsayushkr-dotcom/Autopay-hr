"""
Benchmark Segmentation Engine against Dataset A Ground Truth
"""
import os
import sys
import glob
import json
from datetime import datetime
import numpy as np
import pandas as pd

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from segmentation_engine import segment_session, extract_event_features
from evaluate_segmentation import evaluate_session_boundaries

DATASET_A_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a"

def run_benchmark(num_sessions=10, min_segment_dur=8.0, idle_split_sec=4.5):
    sessions = sorted([
        d for d in glob.glob(os.path.join(DATASET_A_PATH, "ses_*"))
        if os.path.isdir(d)
    ])[:num_sessions]
    
    print("=" * 70)
    print(f"BENCHMARKING SEGMENTATION ENGINE ON {len(sessions)} SESSIONS (DATASET A)")
    print(f"Parameters: min_segment_dur={min_segment_dur}s, idle_split_sec={idle_split_sec}s")
    print("=" * 70)
    
    results = []
    
    for ses in sessions:
        ses_id = os.path.basename(ses)
        gt_man_file = os.path.join(ses, "gt_manifest.json")
        if not os.path.exists(gt_man_file):
            continue
            
        with open(gt_man_file, "r", encoding="utf-8") as f:
            gt_man = json.load(f)
            
        # Parse GT executions
        gt_segments = []
        for p in gt_man.get("processes", []):
            for ex in p.get("executions", []):
                st = ex.get("start_ts")
                en = ex.get("end_ts")
                if st and en:
                    s_sec = datetime.fromisoformat(st).timestamp()
                    e_sec = datetime.fromisoformat(en).timestamp()
                    gt_segments.append((s_sec, e_sec, p.get("code")))
        gt_segments.sort(key=lambda x: x[0])
        
        # Load raw events
        events = []
        for cd in sorted(glob.glob(os.path.join(ses, "chunk_*"))):
            ef = os.path.join(cd, "events.jsonl")
            if os.path.exists(ef):
                with open(ef, "r", encoding="utf-8") as f:
                    for l in f:
                        if l.strip(): events.append(json.loads(l))
                        
        if not events:
            continue
            
        # Run segmentation
        preds = segment_session(events, min_segment_dur=min_segment_dur, idle_split_sec=idle_split_sec)
        pred_tuples = [(p["start_sec"], p["end_sec"], p["label"]) for p in preds]
        
        # Evaluate
        eval_5s = evaluate_session_boundaries(pred_tuples, gt_segments, tolerance_sec=5.0)
        eval_10s = evaluate_session_boundaries(pred_tuples, gt_segments, tolerance_sec=10.0)
        
        results.append({
            "session_id": ses_id,
            "gt_count": len(gt_segments),
            "pred_count": len(preds),
            "start_f1_5s": eval_5s["start_f1"],
            "start_f1_10s": eval_10s["start_f1"],
            "mean_iou": eval_5s["mean_iou"],
            "median_iou": eval_5s["median_iou"]
        })
        
    df = pd.DataFrame(results)
    print("\n--- Per-Session Results ---")
    print(df[["session_id", "gt_count", "pred_count", "start_f1_5s", "start_f1_10s", "mean_iou", "median_iou"]].to_string(index=False))
    
    print("\n--- Overall Benchmark Summary ---")
    print(f"Mean GT Count:     {df['gt_count'].mean():.1f}")
    print(f"Mean Pred Count:   {df['pred_count'].mean():.1f}")
    print(f"Average F1 (@5s):  {df['start_f1_5s'].mean():.3f}")
    print(f"Average F1 (@10s): {df['start_f1_10s'].mean():.3f}")
    print(f"Average Mean IoU:  {df['mean_iou'].mean():.3f}")
    print(f"Average Med IoU:   {df['median_iou'].mean():.3f}")

if __name__ == "__main__":
    run_benchmark(num_sessions=10)
