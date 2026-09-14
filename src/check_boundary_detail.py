import sys, json, os, glob
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_A_PATH = r'G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a'
ses_dir = os.path.join(DATASET_A_PATH, 'ses_20260630-121953-LAPTOP-R36BQBTE')

events = []
for cd in sorted(glob.glob(os.path.join(ses_dir, 'chunk_*'))):
    ef = os.path.join(cd, 'events.jsonl')
    if os.path.exists(ef):
        with open(ef, 'r', encoding='utf-8') as f:
            for l in f:
                if l.strip(): events.append(json.loads(l))
events.sort(key=lambda x: x['timestamp_ms'])

b_ms = datetime.fromisoformat('2026-06-30T12:29:26.327121+00:00').timestamp() * 1000

window = [e for e in events if abs(e['timestamp_ms'] - b_ms) <= 6000]
print(f'Events around boundary between EXP-001 and EXP-002 (total {len(window)}):')
for e in window:
    dt = (e['timestamp_ms'] - b_ms) / 1000.0
    ev = e.get('event_type')
    ctx = e.get('context') or {}
    act = ctx.get('active_app') or {}
    tab = ctx.get('active_browser_tab') or {}
    pld = e.get('payload') or {}
    ext = []
    if ev == 'browser_click':
        el = pld.get('element') or {}
        ext.append(f"Click: <{el.get('tag')}> {el.get('text', '')[:20]}")
    elif ev == 'clipboard_change':
        ext.append(f"Clip: {pld.get('text_preview', '')[:20]}")
    elif ev == 'app_switch':
        ext.append(f"NewApp: {pld.get('new_app', {}).get('app_name')}")
    elif ev == 'keystroke':
        ext.append(f"Key: {pld.get('key')}")
    elif ev == 'shortcut':
        ext.append(f"Shortcut: {pld.get('key_combination')}")
    ext_str = ' | '.join(ext)
    print(f"  [{dt:+.2f}s] {ev:20s} | App: {act.get('app_name')} | Title: {act.get('window_title')[:30]} | {ext_str}")
