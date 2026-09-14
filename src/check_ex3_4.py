import sys, json, os, glob
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_A_PATH = r'G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a'
ses_dir = os.path.join(DATASET_A_PATH, 'ses_20260630-121953-LAPTOP-R36BQBTE')

chunk_dirs = sorted(glob.glob(os.path.join(ses_dir, "chunk_*")))
events = []
for cd in chunk_dirs:
    ef = os.path.join(cd, "events.jsonl")
    if os.path.exists(ef):
        with open(ef, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip(): events.append(json.loads(l))
events.sort(key=lambda x: x['timestamp_ms'])

# Execution 3: 12:22:25.682 to 12:23:22.089
# Execution 4: 12:23:22.090 to 12:23:46.001
st_ms = datetime.fromisoformat("2026-06-30T12:22:25.682+00:00").timestamp() * 1000
en_ms = datetime.fromisoformat("2026-06-30T12:23:46.001+00:00").timestamp() * 1000

sub_events = [e for e in events if st_ms <= e['timestamp_ms'] <= en_ms]
print(f"Events between Ex 3 start and Ex 4 end: {len(sub_events)}")

boundary_ms = datetime.fromisoformat("2026-06-30T12:23:22.090+00:00").timestamp() * 1000

for e in sub_events:
    ts_sec = e['timestamp_ms'] / 1000.0
    dt_boundary = (e['timestamp_ms'] - boundary_ms) / 1000.0
    ev_type = e.get('event_type')
    ctx = e.get('context') or {}
    act = ctx.get('active_app') or {}
    tab = ctx.get('active_browser_tab') or {}
    ext_text = (ctx.get('extracted_text') or {}).get('text') or ''
    payload = e.get('payload') or {}
    
    extra = []
    if tab.get('url'): extra.append(f"URL: {tab.get('url')}")
    if tab.get('title'): extra.append(f"TabTitle: {tab.get('title')}")
    if ev_type == 'browser_click':
        el = payload.get('element') or {}
        extra.append(f"Click: <{el.get('tag')}> {el.get('text', '')[:20]}")
    if ev_type == 'clipboard_change':
        extra.append(f"Clip: {payload.get('text_preview', '')[:20]}")
    if ext_text:
        # Show first 40 chars of extracted text
        extra.append(f"ExtText: {ext_text.strip()[:40]}")
        
    print(f"[{dt_boundary:+.2f}s] {ev_type:20s} | {act.get('app_name')} | {' | '.join(extra)}")
