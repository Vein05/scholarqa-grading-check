"""Pull ScholarQA-CS2 test sub-scores per system from the public asta-bench-results JSONs."""
import json, glob, csv, os
rows = []
for f in sorted(glob.glob('data/results/*.json')):
    j = json.load(open(f))
    for r in j.get('results') or []:
        if not r['task_name'].startswith('ScholarQA_CS2'):
            continue
        m = {x['name']: x['value'] for x in r['metrics']}
        s = j['submission']
        sa = json.loads(r['eval_spec']['solver_args'] or '{}')
        model = r['eval_spec']['model'] if r['eval_spec']['model'] != 'none/none' else (sa.get('completion_model') or sa.get('model') or '')
        rows.append(dict(file=os.path.basename(f), agent=s['agent_name'], model=model.split('/')[-1], user=s['username'],
                         time=s['submit_time'][:10], solver_args=r['eval_spec']['solver_args'][:80],
                         **{k.split('/')[0]: m.get(k) for k in m if k.endswith('/mean')}))
keys = list(rows[0].keys())
for r in rows:
    for k in r:
        if k not in keys: keys.append(k)
with open('results/sqa_scores.csv', 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows(rows)
print(len(rows), 'systems'); print(keys)
