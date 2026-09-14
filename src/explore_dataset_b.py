"""
Exploration of Dataset B (Production Data to Analyze)
"""
import os
import sys
import glob
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd

DATASET_B_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_b"

def explore_dataset_b():
    print("=" * 70)
    print("EXPLORING DATASET B (15 SESSIONS)")
    print("=" * 70)
    
    sessions = sorted([
        d for d in glob.glob(os.path.join(DATASET_B_PATH, "ses_*"))
        if os.path.isdir(d)
    ])
    print(f"Total sessions found: {len(sessions)}")
    
    all_events_count = 0
    all_apps = {}
    all_window_titles = {}
    all_urls = {}
    session_summaries = []
    
    for ses in sessions:
        ses_id = os.path.basename(ses)
        chunk_dirs = sorted(glob.glob(os.path.join(ses, "chunk_*")))
        ses_events = []
        for cd in chunk_dirs:
            ef = os.path.join(cd, "events.jsonl")
            if os.path.exists(ef):
                with open(ef, "r", encoding="utf-8") as f:
                    for l in f:
                        if l.strip():
                            ses_events.append(json.loads(l))
                            
        ses_events.sort(key=lambda x: x["timestamp_ms"])
        all_events_count += len(ses_events)
        
        # Calculate session duration
        start_ms = ses_events[0]["timestamp_ms"] if ses_events else 0
        end_ms = ses_events[-1]["timestamp_ms"] if ses_events else 0
        dur_min = (end_ms - start_ms) / 60000.0 if start_ms and end_ms else 0.0
        
        apps = set()
        for e in ses_events:
            ctx = e.get("context") or {}
            act = ctx.get("active_app") or {}
            app_name = act.get("app_name")
            win_title = act.get("window_title")
            tab = ctx.get("active_browser_tab") or {}
            url = tab.get("url")
            
            if app_name:
                all_apps[app_name] = all_apps.get(app_name, 0) + 1
                apps.add(app_name)
            if win_title:
                all_window_titles[win_title] = all_window_titles.get(win_title, 0) + 1
            if url:
                all_urls[url] = all_urls.get(url, 0) + 1
                
        session_summaries.append({
            "session_id": ses_id,
            "chunks": len(chunk_dirs),
            "events": len(ses_events),
            "duration_min": round(dur_min, 1),
            "apps": list(apps)
        })
        
    df_sum = pd.DataFrame(session_summaries)
    print("\n--- Session Overview ---")
    print(df_sum.to_string(index=False))
    
    print(f"\nTotal Events in Dataset B: {all_events_count}")
    
    print("\n--- Top Active Applications in Dataset B ---")
    for app, cnt in sorted(all_apps.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {app:30s}: {cnt} events")
        
    print("\n--- Top Window Titles in Dataset B ---")
    for title, cnt in sorted(all_window_titles.items(), key=lambda x: x[1], reverse=True)[:25]:
        print(f"  {title:50s}: {cnt} events")
        
    print("\n--- Top URLs in Dataset B ---")
    for url, cnt in sorted(all_urls.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {url:50s}: {cnt} events")

if __name__ == "__main__":
    explore_dataset_b()
