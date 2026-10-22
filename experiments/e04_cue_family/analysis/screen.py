import json
import sys
from pathlib import Path

import yaml

from cueseum.paths import commit, experiment_dir, upstream_commit
from cueseum.rollouts import load_cells
from cueseum.stats import bootstrap_ci

E = experiment_dir("e04_cue_family")
cfg = yaml.safe_load((E / "config.yaml").read_text())
key, root, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
spec = cfg["models"][key]
groups = json.loads((E / "data" / f"cues_{key}.json").read_text())["groups"]
for f in root.rglob("rollouts_p*.jsonl"):
    model = json.loads(f.open().readline())["experiment"]["model"]
    assert model == {"hub": spec["hub"], "revision": spec["revision"]}, (f, model)
df = load_cells(root)
acc = df.groupby(["problem_key", "cue"]).correct.mean().unstack()
assert acc.shape == (cfg["screen_problems"], 1 + sum(map(len, groups.values()))), acc.shape
assert (df.groupby(["cue", "problem_key"]).rollout_index.nunique() == cfg["n_rollouts"]).all()
target, rows = cfg["target"], {}
for group, cues in groups.items():
    for c in cues:
        if c == target:
            continue
        m, lo, hi = bootstrap_ci((acc[target] - acc[c]).to_numpy(), n=cfg["bootstrap"], seed=0)
        family = group[0] in "BCD"
        rows[c] = {"group": group, "acc": float(acc[c].mean()), "diff": m, "lo": lo, "hi": hi, "in_family": family,
                   "forward": family and lo < cfg["screen_forward_lower_bound"]}
by = df.assign(cue=df.cue.where(df.cue != "", "none")).groupby("cue")
res = {"model": key, "problems": len(acc), "target_acc": float(acc[target].mean()), "no_cue_acc": float(acc[""].mean()),
       "controls": rows, "forwarded": [c for c, r in rows.items() if r["forward"]],
       "per_cue": {c: {"cap_rate": float(g.hit_token_cap.mean()), "mean_tokens": float(g.output_tokens.mean()),
                       "no_answer": float(1 - g.committed.mean())} for c, g in by},
       "provenance": {"cueseum_commit": commit(), "upstream_commit": upstream_commit(), "model": spec["hub"],
                      "revision": spec["revision"], "prompt": cfg["prompt"], "temperature": cfg["temperature"], "top_p": cfg["top_p"],
                      "max_new_tokens": cfg["max_new_tokens"], "n_rollouts": cfg["n_rollouts"], "seed": cfg["seed"],
                      "bootstrap": cfg["bootstrap"], "bootstrap_seed": 0, "forward_rule": f"lo < {cfg['screen_forward_lower_bound']}"}}
out.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n")
print(f"{key}: target {res['target_acc']:.3f} | no cue {res['no_cue_acc']:.3f}")
for c, r in sorted(rows.items(), key=lambda kv: kv[1]["diff"]):
    print(f"  {c!r:16s} {r['group']:22s} acc {r['acc']:.3f}  Alright-minus {r['diff']:+.3f} [{r['lo']:+.3f}, {r['hi']:+.3f}]  {'FORWARD' if r['forward'] else ''}")
