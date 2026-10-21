import collections
import json
import sys

import torch
import yaml
from cues.evaluate import problems_path, read_jsonl
from cues.prompts import PROMPTS
from transformers import AutoModelForCausalLM, AutoTokenizer

from cueseum.paths import experiment_dir

E = experiment_dir("e03_cue_controls")
cfg = yaml.safe_load((E / "config.yaml").read_text())
rs, out = cfg["reasoning_style"], sys.argv[1]
tok = AutoTokenizer.from_pretrained(rs["hub"], revision=rs["revision"], padding_side="left")
model = AutoModelForCausalLM.from_pretrained(rs["hub"], revision=rs["revision"], dtype=torch.bfloat16, device_map="auto").eval()
problems = read_jsonl(problems_path(rs["probe"]["benchmark"]))[:rs["probe"]["problems"]]
texts = [tok.apply_chat_template([{"role": "user", "content": PROMPTS["chat"].format(q=p["problem"])}], tokenize=False,
                                 add_generation_prompt=True) for p in problems]
torch.manual_seed(cfg["seed"])
words, samples = collections.Counter(), []
for i in range(0, len(texts), 25):
    batch = tok(texts[i:i + 25], return_tensors="pt", padding=True).to(model.device)
    gen = model.generate(**batch, do_sample=True, temperature=cfg["temperature"], top_p=cfg["top_p"],
                         max_new_tokens=rs["probe"]["max_new_tokens"], num_return_sequences=rs["probe"]["samples"])
    for g in tok.batch_decode(gen[:, batch["input_ids"].shape[1]:], skip_special_tokens=False):
        body = g.split("<think>", 1)[-1].lstrip()
        samples.append(g)
        if body.split():
            words[body.split()[0]] += 1
taken = {cfg["target"], *cfg["groups"]["other_model_cues"], *cfg["groups"]["reference"]}
cues = [c for c in (" " + w for w, _ in words.most_common()) if c not in taken][:rs["take"]]
json.dump({"cues": cues, "first_words": words.most_common(), "n_samples": len(samples), "examples": samples[:8],
           "model": rs["hub"], "revision": rs["revision"]}, open(out, "w"), indent=1, ensure_ascii=False)
print(json.dumps({"cues": cues, "top_first_words": words.most_common(10), "n": len(samples)}, ensure_ascii=False))
