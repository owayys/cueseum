import json
from pathlib import Path

import pandas as pd
from cues.agree import answer_key
from cues.prompts import GRADING

COLUMNS = ["cue", "problem_key", "rollout_index", "correct", "committed", "hit_token_cap", "output_tokens", "answer_key"]


def load_cells(root):
    rows = []
    for f in sorted(Path(root).rglob("rollouts_p*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            style = GRADING[r["prompt"]]
            if style != r["experiment"]["grading"]:
                raise ValueError(f"{f}: grading {r['experiment']['grading']!r} != GRADING[{r['prompt']!r}]")
            key = answer_key(r["completion"], style)
            rows.append({**{c: r[c] for c in COLUMNS[:-1]}, "answer_key": None if key is None else str(key)})
    return pd.DataFrame(rows, columns=COLUMNS)


def save(df, path):
    df.to_parquet(path, index=False)


def load(path):
    return pd.read_parquet(path)
