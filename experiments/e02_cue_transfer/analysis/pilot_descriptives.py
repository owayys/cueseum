import json
import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from cues.evaluate import problems_path, read_jsonl
from cues.prompts import GRADING
from transformers import AutoTokenizer

from cueseum.paths import commit, experiment_dir, upstream_commit
from cueseum.rescore import rescore

E = experiment_dir("e02_cue_transfer")
CFG = yaml.safe_load((E / "config.yaml").read_text())
CHECKING = re.compile(r"let me check|double-check|verify|\bwait\b", re.I)
root, out = Path(sys.argv[1]), Path(sys.argv[2])
gt = {p["problem_key"]: p["gt"] for p in read_jsonl(problems_path(CFG["benchmark"]))}
rows = [json.loads(line) for f in sorted(root.rglob("rollouts_p*.jsonl")) for line in f.read_text().splitlines()]
tok = AutoTokenizer.from_pretrained(CFG["model_hub"], revision=CFG["model_revision"])
budgets = CFG["truncation_budgets"]
scores = rescore(tok, [(gt[r["problem_key"]], r["completion"], GRADING[r["prompt"]]) for r in rows], budgets)
df = pd.DataFrame({"cue": [repr(r["cue"]) if r["cue"] else "no cue" for r in rows], "correct": [r["correct"] for r in rows],
                   "checking": [bool(CHECKING.search(r["completion"])) for r in rows]})
for b, col in zip(budgets, zip(*scores)):
    df[f"acc_{b}"] = [v is True for v in col]
agree = float((df[f"acc_{budgets[-1]}"] == df.correct).mean())
table = df.groupby("cue").mean(numeric_only=True).round(3)
res = {"label": "exploratory: pilot only (50 problems x 4 rollouts), no hypothesis tests",
       "records": len(df), "full_budget_rescore_agrees_with_stored": agree,
       "timeouts": sum(v == "timeout" for s in scores for v in s), "by_cue": table.to_dict(orient="index"),
       "provenance": {"cueseum_commit": commit(), "upstream_commit": upstream_commit(), "tokenizer": CFG["model_hub"],
                      "revision": CFG["model_revision"], "budgets": budgets, "checking_regex": CHECKING.pattern}}
out.write_text(json.dumps(res, indent=1) + "\n")
print(table.to_string())
print(json.dumps({k: res[k] for k in ("records", "full_budget_rescore_agrees_with_stored", "timeouts")}))
