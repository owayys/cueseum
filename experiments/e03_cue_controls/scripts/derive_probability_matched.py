import json
import random
import sys

import numpy as np
import torch
import yaml
from cues.evaluate import problems_path, read_jsonl
from cues.prompts import PROMPTS
from transformers import AutoModelForCausalLM, AutoTokenizer

from cueseum import cueprob
from cueseum.paths import experiment_dir

E = experiment_dir("e03_cue_controls")
cfg = yaml.safe_load((E / "config.yaml").read_text())
pm, out = cfg["probability_matched"], sys.argv[1]
tok = AutoTokenizer.from_pretrained(cfg["model_hub"], revision=cfg["model_revision"])
model = AutoModelForCausalLM.from_pretrained(cfg["model_hub"], revision=cfg["model_revision"], dtype=torch.bfloat16,
                                             device_map="auto").eval()
next_probs = cueprob.hf_next_probs(model)
probe = cfg["reasoning_style"]["probe"]
problems = read_jsonl(problems_path(probe["benchmark"]))[:probe["problems"]]
mean = np.mean([next_probs(tok(PROMPTS[cfg["prompt"]].format(q=p["problem"]))["input_ids"]) for p in problems], axis=0)
anchor = tok.encode(cfg["target"], add_special_tokens=False)[0]
lo, hi = pm["band"][0] * mean[anchor], pm["band"][1] * mean[anchor]
excluded = {w.lower() for w in pm["exclude_words"]}
candidates = []
for t in range(len(tok)):
    s = tok.decode([t])
    if t < len(mean) and lo <= mean[t] <= hi and s.startswith(" ") and s[1:].isalpha() and s[1:].lower() not in excluded:
        candidates.append((t, s, float(mean[t])))
picked = random.Random(pm["draw_seed"]).sample(candidates, pm["take"])
rank = lambda t: int((mean > mean[t]).sum()) + 1
json.dump({"cues": [s for _, s, _ in picked], "anchor": {"token": tok.decode([anchor]), "mean_prob": float(mean[anchor]), "rank": rank(anchor)},
           "band": [float(lo), float(hi)], "candidates": [{"token": s, "mean_prob": p, "rank": rank(t)} for t, s, p in candidates],
           "picked": [{"token": s, "mean_prob": p, "rank": rank(t)} for t, s, p in picked],
           "model": cfg["model_hub"], "revision": cfg["model_revision"]}, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({"anchor_prob": float(mean[anchor]), "anchor_rank": rank(anchor), "n_candidates": len(candidates),
                  "picked": [(s, round(p, 5), rank(t)) for t, s, p in picked]}, ensure_ascii=False))
