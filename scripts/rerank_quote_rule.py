"""Rank the 35 submissions by the official ScholarQA-CS2 score and by the score without the
missing-quote half-credit rule. Input: quote_rule.csv from quote_rule.py.
Citation precision without the rule = official precision + (recomputed no-quote - recomputed official),
so any gap between my precision recomputation and the official one cancels out."""
import csv
R = list(csv.DictReader(open('results/quote_rule.csv')))
for r in R:
    for k in list(r):
        try: r[k] = float(r[k])
        except ValueError: pass
    r['official'] = (r['ingredient_recall'] + r['answer_precision'] + r['cit_rec'] + r['cit_prec']) / 4
    prec_nq = r['cit_prec'] + (r['cit_prec_noquote'] - r['cit_prec_recomputed'])
    r['noquote'] = (r['ingredient_recall'] + r['answer_precision'] + r['cit_rec_noquote'] + prec_nq) / 4
off = sorted(R, key=lambda r: -r['official']); nq = sorted(R, key=lambda r: -r['noquote'])
po = {r['dir']: i + 1 for i, r in enumerate(off)}; pn = {r['dir']: i + 1 for i, r in enumerate(nq)}
print('rank official -> without quote rule | official -> new score | share of claims at half credit')
for r in nq[:12] + [x for x in nq[12:] if abs(po[x['dir']] - pn[x['dir']]) >= 3]:
    print(f"#{po[r['dir']]:>2} -> #{pn[r['dir']]:<2}  {r['official']*100:5.1f} -> {r['noquote']*100:5.1f}  "
          f"half {r['share_half_credit']*100:4.1f}%  {r['agent']} ({r['dir'][:45]})")

# Score is linear in the half-credit penalty w (official w = 0.5, no rule w = 0).
print('\nRank of systems with many title-only claims as the penalty w changes (official w = 0.5):')
ws = [0, 0.05, 0.1, 0.25, 0.5]
for name in ('Perplexity', 'You.com'):
    r = next(x for x in R if name in x['agent'])
    ranks = []
    for w in ws:
        sc = {x['dir']: x['noquote'] - (x['noquote'] - x['official']) * (w / 0.5) for x in R}
        ranks.append(sorted(sc, key=lambda d: -sc[d]).index(r['dir']) + 1)
    print(f"  {r['agent']}: " + ', '.join(f'w={w}: #{k}' for w, k in zip(ws, ranks)))
