"""Re-score ScholarQA-CS2 citations without the missing-quote half-credit rule.

Reads the saved judge outputs in each submission's .eval file (allenai/asta-bench-submissions) and recomputes
citation recall and precision exactly as astabench/evals/sqa/citation_eval.py does, then once more with the
0.5 penalty for title-only (no quote) citations removed. Judge decisions are reused; nothing is re-judged.

Official formulas (citation_eval.py):
  recall    = (n_attributable - 0.5 * n_half_credit_claims) / (n_attributable + n_extrapolatory)
  precision = mean over claims of (s - 0.5 * p) / (s + e)
Sentences in citation groups with no citations count as extrapolatory but are not sent to the judge, so they
are missing from the logs; their number is recovered from the reported recall.

Usage: python scripts/quote_rule.py data/submissions results/quote_rule.csv
"""
import csv
import glob
import json
import os
import sys
import zipfile
from statistics import mean

subs, out_csv = sys.argv[1], sys.argv[2]
rows = []
for ev in sorted(glob.glob(os.path.join(subs, '1.0.0-dev1/test/*/*.eval'))):
    d = os.path.dirname(ev)
    sub = json.load(open(os.path.join(d, 'submission.json'))) if os.path.exists(os.path.join(d, 'submission.json')) else {}
    z = zipfile.ZipFile(ev)
    names = [n for n in z.namelist() if n.startswith('samples/')]
    per = []
    for n in names:
        s = json.loads(z.read(n))
        sc = s['scores'].get('aggregate_scorer') or next(iter(s['scores'].values()))
        v = sc['value']
        A = H = E_judged = 0
        prec_off, prec_new = [], []
        for m in (sc.get('metadata') or {}).get('score_meta') or []:
            if not m or 'claims' not in m.get('prompt_logs', {}):
                continue
            pl = m['prompt_logs']
            for claims_e, half_e in zip(pl['claims'], pl['half_credit']):
                claims = claims_e['data']['claims']
                half = set(half_e['data']['half_credit'])
                for c in claims:
                    sup = [x.strip('[]') for x in c.get('supporting', [])]
                    non = c.get('non_supporting', [])
                    ok = bool(c.get('is_fully_supported') and c.get('supporting'))
                    p = len([x for x in sup if x in half])
                    A += ok
                    E_judged += not ok
                    H += ok and len(sup) == p
                    if sup or non:
                        prec_off.append((len(sup) - 0.5 * p) / (len(sup) + len(non)))
                        prec_new.append(len(sup) / (len(sup) + len(non)))
        rec = v.get('citation_recall', 0)
        total = (A - 0.5 * H) / rec if rec > 0 else A + E_judged
        E_uncited = max(total - A - E_judged, 0)
        rec_recomp = (A - 0.5 * H) / total if total else 0
        rec_new = A / total if total else 0
        per.append(dict(
            ingredient_recall=v.get('ingredient_recall', 0), answer_precision=v.get('answer_precision', 0),
            cit_rec=rec, cit_prec=v.get('citation_precision', 0),
            cit_rec_recomputed=rec_recomp, cit_prec_recomputed=mean(prec_off) if prec_off else 0,
            cit_rec_noquote=rec_new, cit_prec_noquote=mean(prec_new) if prec_new else 0,
            claims=total, half_credit_claims=H, attributable=A, unsupported_judged=E_judged,
            uncited_sentences=E_uncited))
    agg = {k: mean(p[k] for p in per) for k in per[0]}
    tot = sum(p['claims'] for p in per)
    rows.append(dict(
        dir=os.path.basename(d), agent=sub.get('agent_name', ''), n=len(per), **agg,
        share_half_credit=sum(p['half_credit_claims'] for p in per) / tot if tot else 0,
        share_uncited=sum(p['uncited_sentences'] for p in per) / tot if tot else 0,
        share_unsupported=sum(p['unsupported_judged'] for p in per) / tot if tot else 0))
    print(rows[-1]['agent'], rows[-1]['dir'][:50], len(per), flush=True)

with open(out_csv, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
