import sys, json, os, glob
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_A_PATH = r'G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a'
ses_dir = os.path.join(DATASET_A_PATH, 'ses_20260630-121953-LAPTOP-R36BQBTE')
chunk_dirs = sorted(glob.glob(os.path.join(ses_dir, 'chunk_*')))
events = []
for cd in chunk_dirs:
    ef = os.path.join(cd, 'events.jsonl')
    if os.path.exists(ef):
        with open(ef, 'r', encoding='utf-8') as f:
            for l in f:
                if l.strip():
                    events.append(json.loads(l))
events.sort(key=lambda x: x['timestamp_ms'])
gt_ts = datetime.fromisoformat('2026-06-30T12:22:25.682643+00:00').timestamp() * 1000
nearby = [e for e in events if abs(e['timestamp_ms'] - gt_ts) <= 20000]
print(f'Nearby events to Boundary #3 (within +/- 20s): {len(nearby)}')
for e in nearby:
    diff = (e['timestamp_ms'] - gt_ts)/1000.0
    app_info = (e.get('context') or {}).get('active_app') or {}
    print(f"  {diff:+.2f}s | {e.get('event_type')} | App: {app_info.get('app_name')} | Title: {app_info.get('window_title')}")
