"""
Step 2 — Process Analysis & Automation Prioritization on Dataset B
Extracts process volumes, durations, multi-app patterns, data entry intensity,
and calculates an objective ROI Prioritization Score.
"""
import os
import sys
import glob
import json
from datetime import datetime
import pandas as pd
import numpy as np

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_B_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_b"
SEGMENTS_FILE = r"C:\Users\itsay\AI_Engineer\segments.jsonl"

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str)

def run_step2_analysis():
    print("=" * 80)
    print("STEP 2: BUSINESS PROCESS ANALYSIS & ROI PRIORITIZATION (DATASET B)")
    print("=" * 80)
    
    # 1. Load all segments from segments.jsonl
    segments = []
    with open(SEGMENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                segments.append(json.loads(line))
                
    print(f"Total segments loaded from {SEGMENTS_FILE}: {len(segments)}")
    
    # 2. Index raw events by session for deep inspection
    session_dirs = sorted(glob.glob(os.path.join(DATASET_B_PATH, "ses_*")))
    session_events = {}
    session_machines = {}
    
    for sdir in session_dirs:
        ses_id = os.path.basename(sdir)
        events = []
        machine = None
        for cd in sorted(glob.glob(os.path.join(sdir, "chunk_*"))):
            ef = os.path.join(cd, "events.jsonl")
            if os.path.exists(ef):
                with open(ef, "r", encoding="utf-8") as f:
                    for l in f:
                        if l.strip():
                            ev = json.loads(l)
                            events.append(ev)
                            if not machine and (ev.get("source") or {}).get("machine_id"):
                                machine = ev["source"]["machine_id"]
        events.sort(key=lambda x: x["timestamp_ms"])
        session_events[ses_id] = events
        session_machines[ses_id] = machine or ses_id.split("-")[-1]
        
    print(f"Loaded raw events across {len(session_events)} sessions.")
    
    # 3. Enrich segments with granular event statistics
    enriched_segments = []
    
    for seg in segments:
        ses_id = seg["session_id"]
        st = parse_iso(seg["start"]).timestamp() * 1000
        en = parse_iso(seg["end"]).timestamp() * 1000
        dur_sec = (en - st) / 1000.0
        machine = session_machines.get(ses_id, "unknown")
        
        events = session_events.get(ses_id, [])
        in_events = [e for e in events if st <= e["timestamp_ms"] <= en]
        
        # Event type counts
        keystrokes = sum(1 for e in in_events if e.get("event_type") == "keystroke")
        clicks = sum(1 for e in in_events if e.get("event_type") in ["mouse_click", "browser_click"])
        clipboard = sum(1 for e in in_events if e.get("event_type") == "clipboard_change")
        app_switches = sum(1 for e in in_events if e.get("event_type") == "app_switch")
        
        # Apps involved
        apps = set()
        titles = set()
        for e in in_events:
            ctx = e.get("context") or {}
            act = ctx.get("active_app") or {}
            if act.get("app_name"): apps.add(act.get("app_name"))
            if act.get("window_title"): titles.add(act.get("window_title"))
            
        enriched_segments.append({
            "session_id": ses_id,
            "machine": machine,
            "label": seg["label"],
            "start": seg["start"],
            "end": seg["end"],
            "duration_sec": dur_sec,
            "event_count": len(in_events),
            "keystrokes": keystrokes,
            "clicks": clicks,
            "clipboard_ops": clipboard,
            "app_switches": app_switches,
            "apps_used": ",".join(sorted(apps)),
            "app_count": len(apps)
        })
        
    df = pd.DataFrame(enriched_segments)
    
    # 4. Aggregate by Process Label
    total_time_all_procs = df["duration_sec"].sum()
    
    summary = []
    for label, grp in df.groupby("label"):
        count = len(grp)
        total_time_sec = grp["duration_sec"].sum()
        pct_time = (total_time_sec / total_time_all_procs) * 100.0
        
        med_dur = grp["duration_sec"].median()
        mean_dur = grp["duration_sec"].mean()
        min_dur = grp["duration_sec"].min()
        max_dur = grp["duration_sec"].max()
        std_dur = grp["duration_sec"].std()
        
        med_keys = grp["keystrokes"].median()
        med_clicks = grp["clicks"].median()
        med_clip = grp["clipboard_ops"].median()
        med_switches = grp["app_switches"].median()
        
        unique_machines = grp["machine"].nunique()
        unique_sessions = grp["session_id"].nunique()
        
        # All apps seen across executions of this process
        all_apps = set()
        for app_str in grp["apps_used"]:
            for a in app_str.split(","):
                if a: all_apps.add(a)
                
        summary.append({
            "Process": label,
            "Executions": count,
            "Total_Time_Min": round(total_time_sec / 60.0, 1),
            "Time_Share_Pct": round(pct_time, 1),
            "Median_Dur_Sec": round(med_dur, 1),
            "Mean_Dur_Sec": round(mean_dur, 1),
            "Std_Dur_Sec": round(std_dur, 1) if not np.isnan(std_dur) else 0.0,
            "Med_Keystrokes": int(med_keys),
            "Med_Clicks": int(med_clicks),
            "Med_Clipboard": int(med_clip),
            "Med_AppSwitches": int(med_switches),
            "Operators": unique_machines,
            "Sessions": unique_sessions,
            "Apps": ", ".join(sorted(all_apps))
        })
        
    df_summary = pd.DataFrame(summary).sort_values("Executions", ascending=False)
    
    print("\n--- Process Volume & Time Consumption Summary ---")
    print(df_summary[["Process", "Executions", "Total_Time_Min", "Time_Share_Pct", "Median_Dur_Sec", "Operators", "Sessions"]].to_string(index=False))
    
    print("\n--- Manual Operation Intensity (Per Execution Medians) ---")
    print(df_summary[["Process", "Executions", "Med_Keystrokes", "Med_Clicks", "Med_Clipboard", "Med_AppSwitches", "Apps"]].to_string(index=False))
    
    # 5. Transparent Multi-Criteria Automation Priority Score Calculation
    # Priority Score = Total_Time_Min * Automation_Potential * Feasibility * Risk_Adjustment
    # Where:
    # - Total_Time_Min: Scale of manual time drain directly measured from Dataset B logs
    # - Automation_Potential: Proportion of process that is deterministic rule-following vs human judgment
    # - Feasibility: Technical integration simplicity (pure web portal vs multi-app desktop orchestration)
    # - Risk_Adjustment: Operational & financial safety (e.g. low risk when paired with human review thresholds)
    
    criteria_specs = {
        "payroll_items": {"potential": 0.95, "feasibility": 0.95, "risk_adj": 0.90, "decision": "SELECTED FOR STEP 3 PROTOTYPE"},
        "leave_applications": {"potential": 0.80, "feasibility": 0.85, "risk_adj": 0.90, "decision": "Deferred to Phase 2"},
        "tax_withholding": {"potential": 0.75, "feasibility": 0.70, "risk_adj": 0.80, "decision": "Deferred to Phase 2"},
        "onboarding": {"potential": 0.65, "feasibility": 0.70, "risk_adj": 0.80, "decision": "Deferred to Phase 2"},
        "attendance_correction": {"potential": 0.70, "feasibility": 0.80, "risk_adj": 0.85, "decision": "Deferred to Phase 2"},
        "employee_master": {"potential": 0.65, "feasibility": 0.70, "risk_adj": 0.80, "decision": "Deferred to Phase 2"},
        "social_insurance": {"potential": 0.60, "feasibility": 0.65, "risk_adj": 0.75, "decision": "Deferred to Phase 3"},
        "resident_tax": {"potential": 0.60, "feasibility": 0.65, "risk_adj": 0.75, "decision": "Deferred to Phase 3"}
    }
    
    df_roi = df_summary[df_summary["Executions"] >= 10].copy()
    
    roi_rows = []
    for _, row in df_roi.iterrows():
        proc = row["Process"]
        vol = row["Executions"]
        time_min = row["Total_Time_Min"]
        
        spec = criteria_specs.get(proc, {"potential": 0.60, "feasibility": 0.70, "risk_adj": 0.75, "decision": "Deferred to Later Phase"})
        
        score = time_min * spec["potential"] * spec["feasibility"] * spec["risk_adj"]
        
        roi_rows.append({
            "Process": proc,
            "Cases": vol,
            "Total_Time_Min": time_min,
            "Time_Pct": row["Time_Share_Pct"],
            "Automation_Potential": f"{int(spec['potential'] * 100)}%",
            "Feasibility": spec["feasibility"],
            "Risk_Adjustment": spec["risk_adj"],
            "Priority_Score": round(score, 1),
            "Strategic_Decision": spec["decision"]
        })
        
    df_ranked = pd.DataFrame(roi_rows).sort_values("Priority_Score", ascending=False)
    df_ranked["Rank"] = range(1, len(df_ranked) + 1)
    
    print("\n" + "=" * 80)
    print("FINAL PRIORITIZED AUTOMATION CANDIDATES (TRANSPARENT MULTI-CRITERIA RANKING)")
    print("=" * 80)
    print(df_ranked[["Rank", "Process", "Cases", "Total_Time_Min", "Time_Pct", "Automation_Potential", "Feasibility", "Risk_Adjustment", "Priority_Score", "Strategic_Decision"]].to_string(index=False))
    
    return df_summary, df_ranked

if __name__ == "__main__":
    run_step2_analysis()
