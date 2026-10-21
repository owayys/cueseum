import json
import sys

import numpy as np
import torch
import yaml
from cues.evaluate import problems_path, read_jsonl
from cues.prompts import PROMPTS
from transformers import AutoModelForCausalLM, AutoTokenizer

from cueseum import cuederive, cueprob
from cueseum.paths import experiment_dir

E = experiment_dir("e04_cue_family")
cfg = yaml.safe_load((E / "config.yaml").read_text())
key, out = sys.argv[1], sys.argv[2]
m, rs, pm = cfg["models"][key], cfg["reasoning_style"], cfg["probability_matched"]
problems = read_jsonl(problems_path(rs["probe"]["benchmark"]))[:rs["probe"]["problems"]]
load = lambda spec, **kw: (AutoTokenizer.from_pretrained(spec["hub"], revision=spec["revision"], **kw),
                           AutoModelForCausalLM.from_pretrained(spec["hub"], revision=spec["revision"], dtype=torch.bfloat16,
                                                                device_map="auto").eval())

tok, model = load(m["post_trained"], padding_side="left")
texts = [tok.apply_chat_template([{"role": "user", "content": PROMPTS["chat"].format(q=p["problem"])}], tokenize=False,
                                 add_generation_prompt=True) for p in problems]
torch.manual_seed(cfg["seed"])
samples = []
for i in range(0, len(texts), 25):
    batch = tok(texts[i:i + 25], return_tensors="pt", padding=True).to(model.device)
    gen = model.generate(**batch, do_sample=True, temperature=cfg["temperature"], top_p=cfg["top_p"],
                         max_new_tokens=rs["probe"]["max_new_tokens"], num_return_sequences=rs["probe"]["samples"])
    samples += tok.batch_decode(gen[:, batch["input_ids"].shape[1]:], skip_special_tokens=False)
words = cuederive.first_words(samples)
taken = {cfg["target"], cfg["cross_model_cue"], *cfg["groups"]["other_model_cues"], *cfg["groups"]["reference"], *cfg["beam_proposals"][key]}
c_cues = cuederive.reasoning_cues(words, taken, rs["take"])
del model
torch.cuda.empty_cache()

tok, model = load(m)
next_probs = cueprob.hf_next_probs(model)
mean = np.mean([next_probs(tok(PROMPTS[cfg["prompt"]].format(q=p["problem"]))["input_ids"]) for p in problems], axis=0)
anchor = tok.encode(cfg["target"], add_special_tokens=False)[0]
decode = lambda t: tok.decode([t]) if t < len(tok) else ""
cands, band = cuederive.band_candidates(mean, anchor, pm["band"], decode, pm["exclude_words"])
picked = cuederive.draw(cands, pm["take"], pm["draw_seed"])
rank = lambda t: int((mean > mean[t]).sum()) + 1
groups = {"A_target": [cfg["target"]], "B_other_model_cues": cfg["groups"]["other_model_cues"], "C_reasoning_style": c_cues,
          "D_probability_matched": [s for _, s, _ in picked],
          "E_reference": [cfg["cross_model_cue"], *[c for c in cfg["groups"]["reference"] if c != "none"]],
          "E_beam_proposals": cfg["beam_proposals"][key]}
res = {"model": key, "hub": m["hub"], "revision": m["revision"], "post_trained": m["post_trained"], "groups": groups,
       "reasoning_style": {"first_words": words.most_common(), "n_samples": len(samples), "examples": samples[:6]},
       "probability_matched": {"anchor": {"token": tok.decode([anchor]), "mean_prob": float(mean[anchor]), "rank": rank(anchor)},
                               "band": band, "n_candidates": len(cands),
                               "candidates": [{"token": s, "mean_prob": p, "rank": rank(t)} for t, s, p in cands],
                               "picked": [{"token": s, "mean_prob": p, "rank": rank(t)} for t, s, p in picked]}}
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({"model": key, "C": c_cues, "top_words": words.most_common(5), "anchor_prob": float(mean[anchor]),
                  "anchor_rank": rank(anchor), "n_band": len(cands), "D": [(s, round(p, 5), rank(t)) for t, s, p in picked]}, ensure_ascii=False))
