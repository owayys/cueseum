import json
import multiprocessing as mp
from pathlib import Path

import pandas as pd
from cues.agree import answer_key
from cues.grading import extract
from cues.prompts import GRADING

COLUMNS = ["cue", "problem_key", "rollout_index", "correct", "committed", "hit_token_cap", "output_tokens", "answer_key"]


def _key(args):
    key = answer_key(*args)
    return None if key is None else str(key)


def answer_keys(items, timeout=10, max_timeout_share=0.01):
    keys, stalled = [], 0
    while len(keys) < len(items):
        pool = mp.get_context("fork").Pool(1)
        jobs = pool.imap(_key, items[len(keys):])
        try:
            while len(keys) < len(items):
                keys.append(jobs.next(timeout))
        except mp.TimeoutError:
            text, style = items[len(keys)]
            keys.append("timeout:" + extract(text[-2000:], style)[:80])
            stalled += 1
            if stalled > max(1, max_timeout_share * len(items)):
                raise RuntimeError(f"{stalled} answer-key parses timed out")
        finally:
            pool.terminate()
    return keys


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
