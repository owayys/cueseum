import json
import sys
from pathlib import Path

import numpy as np
import yaml

from cueseum.paths import commit, experiment_dir, upstream_commit
from cueseum.rollouts import load_cells, save
from cueseum.stats import bootstrap_ci

E = experiment_dir("e03_cue_controls")
cfg = yaml.safe_load((E / "config.yaml").read_text())
groups = json.loads((E / "data" / "cues.json").read_text())["groups"]
root, out = Path(sys.argv[1]), Path(sys.argv[2])
df = load_cells(root)
save(df, out / "scores.parquet")
acc = df.groupby(["problem_key", "cue"]).correct.mean().unstack()
target, B, alpha = cfg["target"], cfg["bootstrap"], cfg["alpha"]
idx = np.random.default_rng(0).integers(0, len(acc), (B, len(acc)))
family = [c for g, cs in groups.items() if g[0] in "BCD" for c in cs]
tests = {}
for c in family:
    d = (acc[target] - acc[c]).to_numpy()
    boot = d[idx].mean(axis=1)
    p = max(2 * min((boot <= 0).mean(), (boot >= 0).mean()), 1 / (B + 1))
    tests[c] = {"diff": float(d.mean()), "p": float(p), "boot": boot}
for i, c in enumerate(sorted(tests, key=lambda k: tests[k]["p"])):
    a = alpha / (len(tests) - i)
    lo, hi = np.quantile(tests[c].pop("boot"), [a / 2, 1 - a / 2])
    tests[c] |= {"holm_level": 1 - a, "lo": float(lo), "hi": float(hi), "below": bool(lo > 0)}
group_of = {c: g for g, cs in groups.items() for c in cs}
per_cue = {}
for c in acc.columns:
    m, lo, hi = bootstrap_ci(acc[c].to_numpy(), n=B, seed=0)
    g = df[df.cue == c]
    per_cue[c or "none"] = {"group": group_of.get(c, "E_reference"), "pass1": m, "lo": lo, "hi": hi,
                            "cap_rate": float(g.hit_token_cap.mean()), "no_answer": float(1 - g.committed.mean()),
                            "mean_tokens": float(g.output_tokens.mean())}
not_below = {g: [c for c in cs if not tests[c]["below"]] for g, cs in groups.items() if g[0] in "BCD"}
rows = {"B_other_model_cues": "other families' cues transfer as well (not sibling-specific)",
        "C_reasoning_style": "reasoning-style effect", "D_probability_matched": "rare-opener effect"}
decision = [rows[g] for g, cs in not_below.items() if cs] or ["specific to ' Alright,': above every control in B, C and D"]
ref = {}
for c in groups["E_reference"] + [""]:
    m, lo, hi = bootstrap_ci((acc[target] - acc[c]).to_numpy(), n=B, seed=0)
    ref[c or "none"] = {"diff": m, "lo": lo, "hi": hi}
res = {"stage": "screen only (no control forwarded; confirm stage skipped by rule)", "problems": len(acc),
       "decision": decision, "tests": tests, "reference_comparisons_not_in_family": ref, "per_cue": per_cue,
       "provenance": {"cueseum_commit": commit(), "upstream_commit": upstream_commit(), "model": cfg["model_hub"],
                      "revision": cfg["model_revision"], "prompt": cfg["prompt"], "temperature": cfg["temperature"],
                      "top_p": cfg["top_p"], "max_new_tokens": cfg["max_new_tokens"], "n_rollouts": cfg["n_rollouts"],
                      "sampling_seed": cfg["seed"], "bootstrap": B, "bootstrap_seed": 0, "alpha": alpha, "correction": "Holm"}}
(out / "summary.json").write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({"decision": decision, "tests": {c: {k: round(v, 4) if isinstance(v, float) else v for k, v in t.items()} for c, t in tests.items()}}, indent=1, ensure_ascii=False))
