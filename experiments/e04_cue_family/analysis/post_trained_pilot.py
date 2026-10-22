import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import norm

from cueseum.paths import commit, experiment_dir, upstream_commit
from cueseum.rollouts import load_cells
from cueseum.stats import bootstrap_ci

E = experiment_dir("e04_cue_family")
cfg = yaml.safe_load((E / "config.yaml").read_text())
pt = cfg["exploratory_post_trained"]
root, out = Path(sys.argv[1]), Path(sys.argv[2])
for f in root.rglob("rollouts_p*.jsonl"):
    r = json.loads(f.open().readline())
    assert r["experiment"]["model"] == pt["model"] and r["experiment"]["chat"] and r["experiment"]["no_think"], f
df = load_cells(root)
assert (df.groupby(["cue", "problem_key"]).rollout_index.nunique() == cfg["n_rollouts"]).all()
acc = df.groupby(["problem_key", "cue"]).correct.mean().unstack()
assert len(acc) == pt["pilot_problems"], len(acc)
target, comps = " Alright,", {}
for c in ["", *[x for x in pt["cues"] if x != " Alright,"]]:
    d = (acc[target] - acc[c]).to_numpy()
    m, lo, hi = bootstrap_ci(d, n=cfg["bootstrap"], seed=0)
    comps[c or "none"] = {"diff": m, "lo": lo, "hi": hi, "sd": float(d.std(ddof=1))}
s = pt["stop_if"]
stop = all(abs(v["diff"]) < s["max_abs_diff"] and -s["ci_within"] <= v["lo"] and v["hi"] <= s["ci_within"] for v in comps.values())
gaps = [abs(v["diff"]) for v in comps.values() if abs(v["diff"]) >= pt["confirm"]["min_gap"]]
g, sd = (min(gaps) if gaps else pt["confirm"]["min_gap"]), max(v["sd"] for v in comps.values())
z = norm.ppf(1 - cfg["alpha"] / (2 * pt["comparisons"])) + norm.ppf(pt["confirm"]["power"])
n = None if stop else min(math.ceil((z * sd / g) ** 2), pt["confirm"]["cap"])
by = df.assign(cue=df.cue.where(df.cue != "", "none")).groupby("cue")
res = {"label": "exploratory pilot (not pre-registered with e04)", "problems": len(acc), "comparisons_alright_minus": comps,
       "decision": "stop" if stop else "confirm", "confirm_n": n, "g": g, "sd_max": sd,
       "per_cue": {c: {"pass1": float(g_.correct.mean()), "cap_rate": float(g_.hit_token_cap.mean()), "no_answer": float(1 - g_.committed.mean()),
                       "mean_tokens": float(g_.output_tokens.mean())} for c, g_ in by},
       "provenance": {"cueseum_commit": commit(), "upstream_commit": upstream_commit(), **pt["model"], "chat": True, "no_think": True,
                      "prompt": pt["prompt"], "temperature": cfg["temperature"], "top_p": cfg["top_p"], "max_new_tokens": cfg["max_new_tokens"],
                      "n_rollouts": cfg["n_rollouts"], "seed": cfg["seed"], "bootstrap": cfg["bootstrap"]}}
out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
for c, v in res["per_cue"].items():
    print(f"{c!r:16s} pass@1 {v['pass1']:.3f} cap {v['cap_rate']:.3f} no-answer {v['no_answer']:.3f} tokens {v['mean_tokens']:.0f}")
for c, v in comps.items():
    print(f"Alright - {c!r:16s} {v['diff']:+.3f} [{v['lo']:+.3f}, {v['hi']:+.3f}] sd {v['sd']:.3f}")
print("decision:", res["decision"], "| confirm n:", n, "| g", round(g, 3), "sd", round(sd, 3))
