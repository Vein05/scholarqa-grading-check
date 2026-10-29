"""Download the ScholarQA-CS2 submissions from allenai/asta-bench-submissions (gated: accept the terms on the
dataset page first and log in with `huggingface-cli login`). The files stay local; the dataset terms forbid
redistribution. About 2.5 GB."""
from huggingface_hub import snapshot_download

snapshot_download(
    "allenai/asta-bench-submissions", repo_type="dataset", local_dir="data/submissions",
    allow_patterns=["1.0.0-dev1/test/*sqa*", "1.0.0-dev1/test/*/*sqa*",
                    "1.0.0-dev1/test/*/eval_config.json", "1.0.0-dev1/test/*/submission.json"],
    max_workers=8)
