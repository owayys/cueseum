import json
import random
from collections import defaultdict
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def normalize(text):
    return " ".join(text.split())


def stratified_sample(rows, by, n_per_cell, seed, exclude_texts=()):
    excluded = {normalize(t) for t in exclude_texts}
    cells = defaultdict(list)
    for r in rows:
        if normalize(r["problem"]) not in excluded:
            cells[tuple(r[k] for k in by)].append(r)
    rng = random.Random(seed)
    out = []
    for key in sorted(cells):
        if len(cells[key]) < n_per_cell:
            raise ValueError(f"cell {key} has {len(cells[key])} rows, need {n_per_cell}")
        out += rng.sample(cells[key], n_per_cell)
    return out
