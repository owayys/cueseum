import json
import sys

import yaml
from cues.models import cue_slug
from cues.prompts import render
from transformers import AutoTokenizer

from cueseum import cuesets
from cueseum.paths import experiment_dir
from cueseum.problems import read_jsonl

E = experiment_dir("e01_cue_tree")
cfg = yaml.safe_load((E / "config.yaml").read_text())
cues = {k: v for k, v in cuesets.load(sys.argv[1]).items() if v}
for c in cfg["extra_cues"]:
    if c not in cues.values():
        cues[cue_slug(c)] = c
cuesets.save(E / "data" / "tree_cues.json", cues)
tok = AutoTokenizer.from_pretrained(cfg["model_hub"], revision=cfg["model_revision"])
prompt = render(cfg["prompt"], read_jsonl(E / "data" / "tree_problems.jsonl")[0]["problem"])
report = cuesets.token_report(tok, prompt, cues)
(E / "data" / "tree_cues_tokens.json").write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n")
print(json.dumps({"cues": len(cues), "merges": [r["cue"] for r in report.values() if r["merges"]]}, ensure_ascii=False))
