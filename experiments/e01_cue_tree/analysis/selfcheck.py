import sys
from pathlib import Path

import numpy as np
import pandas as pd

from analyze import run

SUBJECTS, CUES = [f"s{i}" for i in range(7)], {f"c{j}": f" c{j}" for j in range(23)}


def synthetic(effect, seed):
    rng = np.random.default_rng(seed)
    problems = pd.DataFrame([{"problem_key": f"{s}_{l}_{i}", "capability": s, "level": l, "gt": str(i)}
                             for s in SUBJECTS for l in range(1, 6) for i in range(12)])
    best = {s: rng.integers(0, 24) for s in SUBJECTS}
    rows = []
    for p in problems.itertuples():
        base = rng.uniform(0.2, 0.8)
        for j, cue in enumerate(["", *CUES.values()]):
            q = np.clip(base + rng.normal(0, 0.05) + effect * (j == best[p.capability]), 0, 1)
            for r in range(8):
                ok = rng.random() < q
                rows.append({"cue": cue, "problem_key": p.problem_key, "rollout_index": r, "correct": ok,
                             "committed": True, "hit_token_cap": False, "output_tokens": 1,
                             "answer_key": p.gt if ok else str(rng.integers(0, 3))})
    return pd.DataFrame(rows), problems


for name, effect in (("planted", 0.3), ("null", 0.0)):
    df, problems = synthetic(effect, 1)
    r = run(df, problems, CUES, Path(sys.argv[1]) / name)
    b = r["all"]["5b_5c"]
    print(name, r["decision"], {lv: (round(b[lv]["diff_vs_global"]["lo"], 3), round(b[lv].get("p", 1), 3)) for lv in b},
          "5a diff", {k: round(v, 3) for k, v in r["all"]["5a"]["diff"].items()},
          "5e subj p", round(r["all"]["5e_5b_5c"]["subject"]["p"], 3), flush=True)
