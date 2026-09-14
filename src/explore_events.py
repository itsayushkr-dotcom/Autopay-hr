"""
Deep dive into raw events around ground truth boundaries.
"""
import os
import sys
import glob
import json
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_A_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a"

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str)

def explore_session_events(ses_id="ses_20260630-121953-LAPTOP-R36BQBTE"):
    ses_dir = os.path.join(DATASET_A_PATH, ses_id)
    gt_file = os.path.join(ses_dir, "gt.jsonl")
    
    # 1. Read GT events
    gt_events = []
    with open(gt_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                gt_events.append(json.loads(line))
                
    gt_starts = [e for e in gt_events if e.get("event") == "process_started"]
    print(f"Session {ses_id} has {len(gt_starts)} process_started events in GT.")
    
    # 2. Read all events from all chunks
    chunk_dirs = sorted(glob.glob(os.path.join(ses_dir, "chunk_*")))
    all_events = []
    for cd in chunk_dirs:
        ev_file = os.path.join(cd, "events.jsonl")
        if os.path.exists(ev_file):
            with open(ev_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        all_events.append(json.loads(line))
                        
    # Sort events by timestamp_ms
    all_events.sort(key=lambda x: x["timestamp_ms"])
    print(f"Total raw events loaded: {len(all_events)}")
    
    # Event type frequency
    types = {}
    for e in all_events:
        t = e.get("event_type")
        types[t] = types.get(t, 0) + 1
    print("\n--- Event Type Distribution ---")
    for t, c in sorted(types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {t}: {c}")
        
    # Look at the first 3 process transitions in GT and find raw events within +/- 2 seconds
    print("\n--- Inspecting Raw Events Around First 3 GT Process Starts ---")
    for idx, gt in enumerate(gt_starts[:3]):
        gt_ts = parse_iso(gt["ts_utc"])
        proc_code = gt.get("process_code")
        proc_name = gt.get("process_name")
        case_id = gt.get("case_id")
        print(f"\n>> GT Boundary #{idx+1}: {proc_code} ({proc_name}) Case: {case_id} at {gt_ts.isoformat()}")
        
        gt_ms = int(gt_ts.timestamp() * 1000)
        # Find events within [gt_ms - 2000, gt_ms + 2000]
        window_events = [e for e in all_events if abs(e["timestamp_ms"] - gt_ms) <= 2500]
        print(f"   Found {len(window_events)} raw events within +/- 2.5 seconds:")
        for we in window_events:
            dt = (we["timestamp_ms"] - gt_ms) / 1000.0
            ev_type = we.get("event_type")
            ctx = we.get("context") or {}
            active_app = (ctx.get("active_app") or {}).get("app_name")
            win_title = (ctx.get("active_app") or {}).get("window_title")
            payload = we.get("payload") or {}
            extra = ""
            if ev_type == "app_switch":
                extra = f"to {payload.get('new_app', {}).get('app_name')} | Title: {payload.get('new_app', {}).get('window_title')}"
            elif ev_type == "browser_navigation":
                extra = f"url: {payload.get('url')}"
            elif ev_type == "browser_click":
                el = payload.get("element") or {}
                extra = f"text: {el.get('text', '')[:30]} tag: {el.get('tag')} id: {el.get('id')}"
            elif ev_type == "clipboard_change":
                extra = f"clip: {payload.get('text_preview', '')[:30]}"
            print(f"     [{dt:+.2f}s] {ev_type} (App: {active_app}) {extra}")

if __name__ == "__main__":
    explore_session_events()
