"""
Optimized Segmentation Engine (V3 - Midpoint Interpolation & Continuous Flow)
"""
import os
import sys
import glob
import json
from datetime import datetime, timezone
import pandas as pd
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str)

def format_iso_utc(epoch_sec):
    dt = datetime.fromtimestamp(epoch_sec, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def extract_event_features(event):
    ts_sec = event["timestamp_ms"] / 1000.0
    ev_type = event.get("event_type", "")
    
    ctx = event.get("context") or {}
    act_app = ctx.get("active_app") or {}
    app_name = act_app.get("app_name") or ""
    win_title = act_app.get("window_title") or ""
    
    tab = ctx.get("active_browser_tab") or {}
    url = tab.get("url") or ""
    
    route = None
    if url and "#/" in url:
        route = url.split("#/")[1].split("?")[0].split("/")[0].strip()
        if not route or route == "dashboard":
            route = None
            
    clean_title = win_title
    for suffix in [
        " - Google Chrome", " - Profile 1 - Microsoft​ Edge", " - Microsoft​ Edge",
        " [Compatibility Mode]", "  -  Compatibility Mode", " - Compatibility Mode",
        " - Word", " - Excel", " - Notepad"
    ]:
        clean_title = clean_title.replace(suffix, "")
    clean_title = clean_title.strip()
    
    is_noise_app = app_name in [
        "procmine-desktop-agent", "OpenWith", "WindowsTerminal", "ms-teams", "prl_cc", "NVIDIA Overlay"
    ] or "WindowsTerminal" in app_name
    
    return {
        "timestamp_sec": ts_sec,
        "event_type": ev_type,
        "app_name": app_name,
        "raw_title": win_title,
        "clean_title": clean_title,
        "url": url,
        "route": route,
        "is_noise_app": is_noise_app,
        "payload": event.get("payload") or {}
    }

def segment_session(session_events, min_segment_dur=12.0, idle_split_sec=5.0, max_idle_gap=30.0):
    if not session_events:
        return []
        
    session_events = sorted(session_events, key=lambda x: x["timestamp_ms"])
    
    valid_events = []
    for e in session_events:
        ev_type = e.get("event_type")
        if ev_type in ["session_start", "session_end", "upload_started", "upload_completed", "upload_failed"]:
            continue
        feat = extract_event_features(e)
        valid_events.append(feat)
        
    if not valid_events:
        return []
        
    # List of candidate split points: (split_time_sec, event_index, reason, weight)
    candidates = []
    prev = valid_events[0]
    
    for idx in range(1, len(valid_events)):
        curr = valid_events[idx]
        dt = curr["timestamp_sec"] - prev["timestamp_sec"]
        
        # Rule 1: Browser Route Change
        if curr["route"] and prev["route"] and curr["route"] != prev["route"]:
            split_time = curr["timestamp_sec"]
            candidates.append((split_time, idx, f"route_change:{prev['route']}->{curr['route']}", 1.0))
        # Rule 2: Office Document major switch
        elif curr["app_name"] in ["Microsoft Word", "Microsoft Excel", "Word", "Excel"] and \
             prev["app_name"] in ["Microsoft Word", "Microsoft Excel", "Word", "Excel"]:
            if curr["clean_title"] and prev["clean_title"] and curr["clean_title"] != prev["clean_title"]:
                if "Opening" not in curr["clean_title"] and "Opening" not in prev["clean_title"]:
                    split_time = curr["timestamp_sec"]
                    candidates.append((split_time, idx, f"doc_change:{prev['clean_title']}->{curr['clean_title']}", 0.9))
        # Rule 3: Idle pause > idle_split_sec (split at midpoint of the pause)
        elif dt >= idle_split_sec and not curr["is_noise_app"]:
            split_time = (prev["timestamp_sec"] + curr["timestamp_sec"]) / 2.0
            candidates.append((split_time, idx, f"idle_gap:{dt:.1f}s", 0.7))
            
        prev = curr
        
    # Non-maximum suppression: enforce minimum segment duration
    selected_splits = [valid_events[0]["timestamp_sec"]]
    split_event_indices = [0]
    
    for split_time, c_idx, reason, weight in candidates:
        if split_time - selected_splits[-1] >= min_segment_dur:
            selected_splits.append(split_time)
            split_event_indices.append(c_idx)
            
    selected_splits.append(valid_events[-1]["timestamp_sec"])
    split_event_indices.append(len(valid_events))
    
    # Construct final segments
    segments = []
    for i in range(len(selected_splits) - 1):
        s_time = selected_splits[i]
        e_time = selected_splits[i+1]
        
        s_idx = split_event_indices[i]
        e_idx = split_event_indices[i+1] - 1
        seg_events = valid_events[s_idx:e_idx+1]
        
        work_events = [e for e in seg_events if not e["is_noise_app"]]
        if not work_events:
            work_events = seg_events
            
        # Determine dominant process label
        route_counts = {}
        title_counts = {}
        for e in work_events:
            if e["route"]:
                route_counts[e["route"]] = route_counts.get(e["route"], 0) + 1
            if e["clean_title"] and e["clean_title"] not in [
                "HR人事給与システム", "財務会計システム", "受発注在庫管理システム", "Opening"
            ]:
                title_counts[e["clean_title"]] = title_counts.get(e["clean_title"], 0) + 1
                
        if route_counts:
            label = max(route_counts.items(), key=lambda x: x[1])[0]
        elif title_counts:
            label = max(title_counts.items(), key=lambda x: x[1])[0]
        else:
            label = work_events[0]["app_name"] or "routine_operation"
            
        clean_label = label.lower().replace(" ", "_").replace("-", "_").replace(".", "_")
        dur = e_time - s_time
        
        if dur >= min_segment_dur:
            segments.append({
                "start_sec": s_time,
                "end_sec": e_time,
                "start_iso": format_iso_utc(s_time),
                "end_iso": format_iso_utc(e_time),
                "label": clean_label,
                "duration_sec": round(dur, 2),
                "event_count": len(work_events)
            })
            
    return segments

if __name__ == "__main__":
    print("Optimized Segmentation Engine V3 Ready.")
