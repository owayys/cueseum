import json
import sys
from pathlib import Path

import numpy as np
import yaml

from cueseum.paths import commit, experiment_dir, upstream_commit
from cueseum.rollouts import load_cells, save
from cueseum.stats import bootstrap_ci

E = experiment_dir("e04_cue_family")
cfg = yaml.safe_load((E / "config.yaml").read_text())
key, runs, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
spec, B, alpha, target = cfg["models"][key], cfg["bootstrap"], cfg["alpha"], cfg["target"]
groups = json.loads((E / "data" / f"cues_{key}.json").read_text())["groups"]
forwarded = json.loads((E / "results" / f"screen_{key}.json").read_text())["forwarded"]


def table(root, n):
    for f in root.rglob("rollouts_p*.jsonl"):
        assert json.loads(f.open().readline())["experiment"]["model"] == {"hub": spec["hub"], "revision": spec["revision"]}, f
    df = load_cells(root)
    assert (df.groupby(["cue", "problem_key"]).rollout_index.nunique() == cfg["n_rollouts"]).all()
    acc = df.groupby(["problem_key", "cue"]).correct.mean().unstack()
    assert len(acc) == n, len(acc)
    return df, acc


sdf, screen = table(runs / "screen" / key, cfg["screen_problems"])
save(sdf, out / f"scores_screen_{key}.parquet")
confirm = None
if forwarded:
    cdf, confirm = table(runs / "confirm" / key, cfg["confirm_problems"])
    save(cdf, out / f"scores_confirm_{key}.parquet")
tests = {}
for c in (c for g, cs in groups.items() if g[0] in "BCD" for c in cs):
    acc = confirm if c in forwarded else screen
    d = (acc[target] - acc[c]).to_numpy()
    boot = d[np.random.default_rng(0).integers(0, len(d), (B, len(d)))].mean(axis=1)
    p = max(2 * min((boot <= 0).mean(), (boot >= 0).mean()), 1 / (B + 1))
    tests[c] = {"data": "confirm" if c in forwarded else "screen", "n": len(d), "diff": float(d.mean()), "p": float(p), "boot": boot}
for i, c in enumerate(sorted(tests, key=lambda k: tests[k]["p"])):
    a = alpha / (len(tests) - i)
    lo, hi = np.quantile(tests[c].pop("boot"), [a / 2, 1 - a / 2])
    tests[c] |= {"holm_level": 1 - a, "lo": float(lo), "hi": float(hi), "below": bool(lo > 0)}
rows = {"B_other_model_cues": "other families' cues do as well", "C_reasoning_style": "reasoning-style effect",
        "D_probability_matched": "rare/equal-probability opener effect"}
decision = [rows[g] for g, cs in groups.items() if g in rows and any(not tests[c]["below"] for c in cs)] \
    or ["specific to ' Alright,': above every control in B, C and D"]
per_cue = {}
for c in screen.columns:
    m, lo, hi = bootstrap_ci(screen[c].to_numpy(), n=B, seed=0)
    per_cue[c or "none"] = {"screen_pass1": m, "lo": lo, "hi": hi}
res = {"model": key, "decision": decision, "forwarded": forwarded, "tests": tests, "per_cue_screen": per_cue,
       "provenance": {"cueseum_commit": commit(), "upstream_commit": upstream_commit(), "model": spec["hub"], "revision": spec["revision"],
                      "prompt": cfg["prompt"], "temperature": cfg["temperature"], "top_p": cfg["top_p"],
                      "max_new_tokens": cfg["max_new_tokens"], "n_rollouts": cfg["n_rollouts"], "sampling_seed": cfg["seed"],
                      "bootstrap": B, "bootstrap_seed": 0, "alpha": alpha, "correction": "Holm within size"}}
(out / f"summary_{key}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(key, decision)
for c, t in sorted(tests.items(), key=lambda kv: kv[1]["diff"]):
    print(f"  {c!r:16s} [{t['data']:7s} n={t['n']}] {t['diff']:+.3f} Holm[{t['lo']:+.3f}, {t['hi']:+.3f}] @{t['holm_level']:.4f} {'below' if t['below'] else 'NOT below'}")
