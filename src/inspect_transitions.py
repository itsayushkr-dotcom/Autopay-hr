import sys, json, os, glob
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_A_PATH = r'G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a'
ses_dir = os.path.join(DATASET_A_PATH, 'ses_20260630-121953-LAPTOP-R36BQBTE')

with open(os.path.join(ses_dir, 'gt_manifest.json'), 'r', encoding='utf-8') as f:
    gt_man = json.load(f)

execs = []
for p in gt_man.get('processes', []):
    for ex in p.get('executions', []):
        st = ex.get('start_ts')
        en = ex.get('end_ts')
        if st and en:
            execs.append({
                'code': p.get('code'),
                'family': p.get('family_name'),
                'case_id': ex.get('case_id'),
                'start_ts': datetime.fromisoformat(st),
                'end_ts': datetime.fromisoformat(en),
                'apps': ex.get('apps', [])
            })
execs.sort(key=lambda x: x['start_ts'])

chunk_dirs = sorted(glob.glob(os.path.join(ses_dir, "chunk_*")))
events = []
for cd in chunk_dirs:
    ef = os.path.join(cd, "events.jsonl")
    if os.path.exists(ef):
        with open(ef, "r", encoding="utf-8") as f:
            for l in f:
                if l.strip(): events.append(json.loads(l))
events.sort(key=lambda x: x['timestamp_ms'])

print(f"Session has {len(execs)} valid executions. Inspecting transitions between first 6 executions:\n")

for i in range(min(6, len(execs))):
    ex = execs[i]
    dur = (ex['end_ts'] - ex['start_ts']).total_seconds()
    print(f"=== Execution #{i+1}: {ex['code']} ({ex['family']}) Case: {ex['case_id']} ===")
    print(f"    Start: {ex['start_ts'].strftime('%H:%M:%S.%f')[:-3]} -> End: {ex['end_ts'].strftime('%H:%M:%S.%f')[:-3]} (Duration: {dur:.1f}s)")
    
    st_ms = ex['start_ts'].timestamp() * 1000
    en_ms = ex['end_ts'].timestamp() * 1000
    in_events = [e for e in events if st_ms <= e['timestamp_ms'] <= en_ms]
    
    titles = set()
    apps = set()
    for e in in_events:
        ctx = e.get('context') or {}
        act = ctx.get('active_app') or {}
        if act.get('app_name'): apps.add(act.get('app_name'))
        if act.get('window_title'): titles.add(act.get('window_title'))
    print(f"    Events count: {len(in_events)}")
    print(f"    Active apps: {list(apps)}")
    print(f"    Window titles: {list(titles)[:4]}")
    
    if i + 1 < len(execs):
        next_ex = execs[i+1]
        next_st_ms = next_ex['start_ts'].timestamp() * 1000
        gap = (next_ex['start_ts'] - ex['end_ts']).total_seconds()
        gap_events = [e for e in events if en_ms < e['timestamp_ms'] < next_st_ms]
        print(f"    --> Transition to next task: Gap = {gap:.3f}s, Events in gap = {len(gap_events)}")
        for ge in gap_events:
            ctx = ge.get('context') or {}
            act = ctx.get('active_app') or {}
            print(f"        Gap Event: {ge.get('event_type')} | App: {act.get('app_name')} | Title: {act.get('window_title')}")
    print()
