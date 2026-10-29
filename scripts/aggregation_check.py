"""Does the ScholarQA-CS2 ranking depend on how the four sub-scores are combined?

Uses only the public per-system means (asta-bench-results). The official score is the mean of
ingredient_recall, answer_precision, citation_precision, citation_recall. Each alternative below
is another reasonable way to combine the same four numbers; system outputs and judgments are unchanged.
"""
import csv, itertools
from statistics import mean

C = ['ingredient_recall', 'answer_precision', 'citation_precision', 'citation_recall']
rows = list(csv.DictReader(open('results/sqa_scores.csv')))
for r in rows:
    for k in C + ['global_avg']:
        r[k] = float(r[k])
    r['name'] = f"{r['agent']} ({r['model']})"
assert all(abs(mean(r[k] for k in C) - r['global_avg']) < 1e-6 for r in rows), 'official != mean of 4'

def hmean(xs): return len(xs) / sum(1 / max(x, 1e-9) for x in xs)
schemes = {
    'official: mean of 4': lambda r: mean(r[k] for k in C),
    'content only (ingredient recall, answer precision)': lambda r: mean(r[k] for k in C[:2]),
    'citations only (citation precision, recall)': lambda r: mean(r[k] for k in C[2:]),
    'content 2/3, citations 1/3': lambda r: (2 * mean(r[k] for k in C[:2]) + mean(r[k] for k in C[2:])) / 3,
    'harmonic mean of 4': lambda r: hmean([r[k] for k in C]),
}
for k in C:
    schemes[f'drop {k}'] = (lambda kk: lambda r: mean(r[x] for x in C if x != kk))(k)

def ranking(f): return sorted(rows, key=lambda r: -f(r))
def kendall(a, b):
    pa = {r['name']: i for i, r in enumerate(a)}; pb = {r['name']: i for i, r in enumerate(b)}
    n = list(pa); c = d = 0
    for x, y in itertools.combinations(n, 2):
        s = (pa[x] - pa[y]) * (pb[x] - pb[y]); c += s > 0; d += s < 0
    return (c - d) / (c + d)

off = ranking(schemes['official: mean of 4'])
top10 = {r['name'] for r in off[:10]}
print(f'{len(rows)} systems\n')
for name, f in schemes.items():
    rk = ranking(f)
    pos = {r['name']: i for i, r in enumerate(rk)}
    flips = sum(1 for x, y in itertools.combinations([r['name'] for r in off[:10]], 2)
                if pos[x] > pos[y])
    print(f'{name}\n  winner: {rk[0]["name"]}  | Kendall tau vs official {kendall(off, rk):.3f}'
          f' | top-10 pairs reversed {flips}/45 | top-10 set changed {len(top10 - {r["name"] for r in rk[:10]})}')
print('\nOfficial top 12 and their rank under content-only / citations-only:')
co = {r['name']: i + 1 for i, r in enumerate(ranking(schemes['content only (ingredient recall, answer precision)']))}
ci = {r['name']: i + 1 for i, r in enumerate(ranking(schemes['citations only (citation precision, recall)']))}
for i, r in enumerate(off[:12], 1):
    print(f"{i:2d}. {r['global_avg']*100:5.1f}  {r['name'][:60]:60s} content #{co[r['name']]:<3d} citations #{ci[r['name']]}"
          f"   [{' '.join(f'{r[k]*100:.0f}' for k in C)}]")
