import collections
import json
import sys

import torch
import yaml
from cues import models as M
from cues.evaluate import problems_path, read_jsonl
from cues.prompts import PROMPTS
from transformers import AutoModelForCausalLM, AutoTokenizer

from cueseum import cueprob, cuesets
from cueseum.paths import commit, experiment_dir, upstream_commit

E = experiment_dir("e02_cue_transfer")
CFG = yaml.safe_load((E / "config.yaml").read_text())
FILTERS = {"top_first": 12, "top_second": 4, "beam_width": 40}
key, out = sys.argv[1], sys.argv[2]
extra = json.load(open(sys.argv[3]))["own_top"] if len(sys.argv) > 3 else []
entry = CFG.get("exploratory_scaling", {}).get(key) or M.resolve(key)
tok = AutoTokenizer.from_pretrained(entry["hub"], revision=entry["revision"], trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(entry["hub"], revision=entry["revision"], dtype=torch.bfloat16,
                                             device_map="auto", trust_remote_code=True).eval()
next_probs = cueprob.hf_next_probs(model)
probe = CFG["probe"]
problems = read_jsonl(problems_path(probe["benchmark"]))[:probe["problems"]]
prompts = [PROMPTS[CFG["prompt"]].format(q=p["problem"]) for p in problems]
ids = [tok(p)["input_ids"] for p in prompts]

def cached():
    store = {}
    return lambda ids: store[tuple(ids)] if tuple(ids) in store else store.setdefault(tuple(ids), next_probs(ids))


caches, presence, mass = [], collections.Counter(), collections.Counter()
for pid in ids:
    caches.append(cached())
    for level in cueprob.beam(caches[-1], pid, 2, **FILTERS):
        for opening, p in level.items():
            name = "".join(tok.decode([t]) for t in opening)
            presence[name] += 1
            mass[name] += p
n = len(problems)
candidates = sorted(({"prefix": o, "problem_fraction": presence[o] / n, "mean_beam_mass": mass[o] / n}
                     for o in presence if presence[o] >= 0.5 * n), key=lambda c: -c["mean_beam_mass"])
own_top = [c["prefix"] for c in candidates[:probe["top_beam"]]]
cues = list(dict.fromkeys(probe["cues"] + probe["top5_4b_from_e01_beam"] + own_top + extra))
report = cuesets.token_report(tok, prompts[0], {c: c for c in cues})
assert not any(r["merges"] for r in report.values()), "a cue merges with the prompt"
cue_ids = {c: report[c]["ids"] for c in cues}
per_problem = [cueprob.measure(cache, pid, cue_ids, **FILTERS) for cache, pid in zip(caches, ids)]
agg = cueprob.aggregate(per_problem)
for c in cues:
    agg[c]["rank_by_mean_prob"] = 1 + sum(agg[d]["mean_prob"] > agg[c]["mean_prob"] for d in cues)
    agg[c]["candidate_rank"] = next((i + 1 for i, x in enumerate(candidates) if x["prefix"] == c), None)
    agg[c]["token_ids"] = cue_ids[c]
json.dump({"model": key, "hub": entry["hub"], "revision": entry["revision"], "prompt": CFG["prompt"],
           "probe": probe["benchmark"], "problems": n, "beam": {"depth": 2, **FILTERS, "min_problem_fraction": 0.5},
           "own_top": own_top, "candidates": candidates, "cues": agg,
           "per_problem": [{c: {k: v for k, v in r[c].items()} for c in cues} for r in per_problem],
           "provenance": {"cueseum_commit": commit(), "upstream_commit": upstream_commit()}},
          open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({"model": key, "own_top": own_top, "candidates": len(candidates),
                  "cues": {c: {k: agg[c][k] for k in ("mean_prob", "mean_beam_mass", "median_ranks", "problem_fraction",
                                                      "candidate_rank", "removed_by")} for c in cues}}, indent=1, ensure_ascii=False))
