import json
from pathlib import Path

import pandas as pd
from cues.agree import answer_key
from cues.grading import extract
from cues.prompts import GRADING

from cueseum.parallel import timed_map

COLUMNS = ["cue", "problem_key", "rollout_index", "correct", "committed", "hit_token_cap", "output_tokens", "answer_key"]


def _key(args):
    key = answer_key(*args)
    return None if key is None else str(key)


def _timeout_key(item):
    text, style = item
    return "timeout:" + extract(text[-2000:], style)[:80]


def answer_keys(items, timeout=10, max_timeout_share=0.01):
    return timed_map(_key, items, _timeout_key, timeout, max_timeout_share=max_timeout_share)


def load_cells(root, timeout=10):
    rows, items = [], []
    for f in sorted(Path(root).rglob("rollouts_p*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            style = GRADING[r["prompt"]]
            if style != r["experiment"]["grading"]:
                raise ValueError(f"{f}: grading {r['experiment']['grading']!r} != GRADING[{r['prompt']!r}]")
            rows.append({c: r[c] for c in COLUMNS[:-1]})
            items.append((r["completion"], style))
    df = pd.DataFrame(rows, columns=COLUMNS[:-1])
    df["answer_key"] = answer_keys(items, timeout)
    return df[COLUMNS]


def save(df, path):
    df.to_parquet(path, index=False)


def load(path):
    return pd.read_parquet(path)
