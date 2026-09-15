"""
Deep-dive inspection of payroll_items workflow in Dataset B
"""
import os
import sys
import glob
import json

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_B_PATH = r"G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_b"

def inspect_payroll_workflow():
    # Pick session ses_20260701-183232-LAPTOP-76QMG9DE
    ses_dir = os.path.join(DATASET_B_PATH, "ses_20260701-183232-LAPTOP-76QMG9DE")
    
    events = []
    for cd in sorted(glob.glob(os.path.join(ses_dir, "chunk_*"))):
        ef = os.path.join(cd, "events.jsonl")
        if os.path.exists(ef):
            with open(ef, "r", encoding="utf-8") as f:
                for l in f:
                    if l.strip(): events.append(json.loads(l))
    events.sort(key=lambda x: x["timestamp_ms"])
    
    # Filter for first payroll_items block (18:32:40 to 18:34:05)
    # 18:32:40 UTC epoch
    st_ms = 1782930760000 # around 18:32:40
    en_ms = 1782930845000 # around 18:34:05
    
    p_events = [e for e in events if st_ms <= e["timestamp_ms"] <= en_ms]
    print(f"Inspecting payroll_items execution: {len(p_events)} events found\n")
    
    for e in p_events:
        t_sec = (e["timestamp_ms"] - st_ms) / 1000.0
        ev_type = e.get("event_type")
        ctx = e.get("context") or {}
        act = ctx.get("active_app") or {}
        tab = ctx.get("active_browser_tab") or {}
        ext_text = (ctx.get("extracted_text") or {}).get("text") or ""
        pld = e.get("payload") or {}
        
        info = []
        if ev_type == "browser_click":
            el = pld.get("element") or {}
            info.append(f"Click <{el.get('tag')}> text='{el.get('text', '')[:20]}' id='{el.get('id')}'")
        elif ev_type == "clipboard_change":
            info.append(f"Clip: '{pld.get('text_preview', '')[:30]}'")
        elif ev_type == "keystroke":
            info.append(f"Key: '{pld.get('key')}' char: '{pld.get('character')}'")
        elif ev_type == "shortcut":
            info.append(f"Shortcut: '{pld.get('key_combination')}'")
        elif ev_type == "app_switch":
            info.append(f"Switch to: {pld.get('new_app', {}).get('app_name')} - {pld.get('new_app', {}).get('window_title')[:30]}")
            
        if ext_text:
            info.append(f"ExtText: {repr(ext_text.strip()[:60])}")
            
        if info:
            print(f"[{t_sec:5.1f}s] {ev_type:18s} | {act.get('app_name'):15s} | {' | '.join(info)}")

if __name__ == "__main__":
    inspect_payroll_workflow()
