"""
Analyze what happens between two executions of the SAME process (Case 1 -> Case 2)
"""
import sys, json, os, glob
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DATASET_A_PATH = r'G:\.shortcut-targets-by-id\1WSBZQxOODKFDzYBkIik5g90NWKS7Gwl0\AI Engineer\dataset_a'

# Let's inspect a session where process A appears multiple times
ses_dir = os.path.join(DATASET_A_PATH, 'ses_20260630-121953-LAPTOP-R36BQBTE')
with open(os.path.join(ses_dir, 'gt_manifest.json'), 'r', encoding='utf-8') as f:
    gt_man = json.load(f)

# Find executions of process A
p_a = next(p for p in gt_man['processes'] if p['code'] == 'A')
execs_a = [e for e in p_a['executions'] if e.get('start_ts') and e.get('end_ts')]

print(f"Process A has {len(execs_a)} executions in this session:")
for ex in execs_a[:4]:
    print(f"  Case: {ex['case_id']}, Start: {ex['start_ts']}, End: {ex['end_ts']}")

# Load all events
events = []
for cd in sorted(glob.glob(os.path.join(ses_dir, 'chunk_*'))):
    ef = os.path.join(cd, 'events.jsonl')
    if os.path.exists(ef):
        with open(ef, 'r', encoding='utf-8') as f:
            for l in f:
                if l.strip(): events.append(json.loads(l))
events.sort(key=lambda x: x['timestamp_ms'])

# Let's look at Case 1 (12:23:22 to 12:23:46) and Case 2 (12:26:32 to 12:26:55)
# Wait, were they consecutive or separated by other processes?
# Let's check chronological order of all executions in session
all_execs = []
for p in gt_man['processes']:
    for ex in p['executions']:
        if ex.get('start_ts') and ex.get('end_ts'):
            all_execs.append((datetime.fromisoformat(ex['start_ts']), datetime.fromisoformat(ex['end_ts']), p['code'], ex['case_id']))
all_execs.sort(key=lambda x: x[0])

print("\n--- Consecutive Executions in this session ---")
for i in range(len(all_execs)-1):
    ex1 = all_execs[i]
    ex2 = all_execs[i+1]
    gap = (ex2[0] - ex1[1]).total_seconds()
    is_same = ex1[2] == ex2[2]
    if is_same or gap > 2.0:
        print(f"Ex #{i+1} [{ex1[2]} - {ex1[3]}] -> Ex #{i+2} [{ex2[2]} - {ex2[3]}] | Same Proc: {is_same} | Gap: {gap:.2f}s")
