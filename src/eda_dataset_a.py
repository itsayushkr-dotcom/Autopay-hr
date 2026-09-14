"""
Exploratory Data Analysis (EDA) of Dataset A
Analyzes Ground Truth (gt_manifest.json, gt.jsonl) and Operation Logs (events.jsonl).
"""
import os
import sys
import glob
import json
from datetime import datetime

# Ensure utf-8 stdout on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np

DATASET_A_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a"

def parse_iso(ts_str):
    if not ts_str:
        return None
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.fromisoformat(ts_str)

def analyze_ground_truth():
    print("=" * 70)
    print("ANALYZING DATASET A: GROUND TRUTH SUMMARY (gt_manifest.json)")
    print("=" * 70)
    
    session_dirs = sorted([
        d for d in glob.glob(os.path.join(DATASET_A_PATH, "ses_*"))
        if os.path.isdir(d)
    ])
    print(f"Total sessions in Dataset A: {len(session_dirs)}")
    
    all_executions = []
    process_families = {}
    session_stats = []
    
    for ses in session_dirs:
        ses_id = os.path.basename(ses)
        gt_manifest_file = os.path.join(ses, "gt_manifest.json")
        if not os.path.exists(gt_manifest_file):
            continue
            
        with open(gt_manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        ses_info = manifest.get("session", {})
        processes = manifest.get("processes", [])
        noise_blocks = manifest.get("noise_blocks", [])
        
        ses_start = parse_iso(ses_info.get("start_ts"))
        ses_end = parse_iso(ses_info.get("end_ts"))
        ses_duration_sec = (ses_end - ses_start).total_seconds() if ses_start and ses_end else None
        
        exec_count = 0
        for p in processes:
            p_code = p.get("code")
            p_family = p.get("family_name")
            p_domain = p.get("domain")
            process_families[p_code] = (p_family, p_domain)
            
            for ex in p.get("executions", []):
                st = parse_iso(ex.get("start_ts"))
                en = parse_iso(ex.get("end_ts"))
                dur = (en - st).total_seconds() if st and en else None
                all_executions.append({
                    "session_id": ses_id,
                    "code": p_code,
                    "family_name": p_family,
                    "domain": p_domain,
                    "case_id": ex.get("case_id"),
                    "start_ts": st,
                    "end_ts": en,
                    "duration_sec": dur,
                    "apps": ",".join(ex.get("apps", [])),
                    "variant": ex.get("variant"),
                    "phase": ex.get("phase"),
                    "continues_from_prev": ex.get("continues_from_prev"),
                    "continues_to_next": ex.get("continues_to_next"),
                })
                exec_count += 1
                
        session_stats.append({
            "session_id": ses_id,
            "duration_min": ses_duration_sec / 60.0 if ses_duration_sec else None,
            "exec_count": exec_count,
            "noise_count": len(noise_blocks),
        })
        
    df_exec = pd.DataFrame(all_executions)
    df_ses = pd.DataFrame(session_stats)
    
    print(f"\nTotal Executions parsed: {len(df_exec)}")
    print("\n--- Process Families Discovered ---")
    for code, (fam, dom) in sorted(process_families.items()):
        cnt = len(df_exec[df_exec['code'] == code])
        print(f"Code [{code}]: {fam} (Domain: {dom}) -> {cnt} executions")
        
    print("\n--- Execution Duration Statistics (seconds) ---")
    dur_stats = df_exec["duration_sec"].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9, 0.95])
    print(dur_stats.round(2))
    
    print("\n--- Duration Stats by Process Family (seconds) ---")
    proc_grp = df_exec.groupby(["code", "family_name"])["duration_sec"].agg(
        count="count",
        min="min",
        median="median",
        mean="mean",
        max="max"
    ).round(1)
    print(proc_grp)
    
    print("\n--- Session Statistics ---")
    print(df_ses.describe().round(2))

    # Calculate gap between consecutive executions within each session
    print("\n--- Gaps Between Consecutive Executions (Inter-task Idle/Transition Time) ---")
    gaps = []
    for ses_id, grp in df_exec.groupby("session_id"):
        grp_sorted = grp.sort_values("start_ts")
        prev_end = None
        for _, row in grp_sorted.iterrows():
            if prev_end is not None and row["start_ts"] is not None:
                gap = (row["start_ts"] - prev_end).total_seconds()
                gaps.append(gap)
            prev_end = row["end_ts"]
            
    df_gaps = pd.Series(gaps)
    print(df_gaps.describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9]).round(2))
    
    return df_exec, df_ses

if __name__ == "__main__":
    analyze_ground_truth()
