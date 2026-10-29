#!/usr/bin/env bash
# Download the public AstaBench test results (allenai/asta-bench-results, not gated) into data/results/.
set -euo pipefail
mkdir -p data/results
curl -s "https://huggingface.co/api/datasets/allenai/asta-bench-results/tree/main/1.0.0/test" \
  | python3 -c "import json,sys;print('\n'.join(x['path'] for x in json.load(sys.stdin) if x['path'].endswith('.json')))" \
  | while read -r p; do
      f="data/results/$(basename "$p")"
      [ -s "$f" ] || curl -sL -o "$f" "https://huggingface.co/datasets/allenai/asta-bench-results/resolve/main/$p"
    done
ls data/results | wc -l
