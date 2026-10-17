import json
from collections import Counter

import yaml

from cueseum.paths import ROOT, experiment_dir
from cueseum.problems import read_jsonl, stratified_sample, write_jsonl

E = experiment_dir("e01_cue_tree")
cfg = yaml.safe_load((E / "config.yaml").read_text())["problems"]
rows = [r for r in read_jsonl(ROOT / cfg["source"]) if r["level"] is not None]
probe = [p["problem"] for p in read_jsonl(ROOT / cfg["exclude"])]
fields = ["problem_key", "problem", "gt", "capability", "level"]
full = [{k: r[k] for k in fields} for r in stratified_sample(rows, cfg["by"], cfg["n_per_cell"], cfg["seed"], probe)]
pilot = stratified_sample(full, cfg["by"], cfg["pilot_per_cell"], cfg["seed"])
write_jsonl(E / "data" / "tree_problems.jsonl", full)
write_jsonl(E / "data" / "tree_problems_pilot.jsonl", pilot)
print(json.dumps({"full": len(full), "pilot": len(pilot),
                  "cells": dict(Counter(f"{r['capability']}/{r['level']}" for r in full))}))
