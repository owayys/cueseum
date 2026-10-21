import random

import yaml
from cues.evaluate import problems_path, read_jsonl

from cueseum.paths import experiment_dir
from cueseum.problems import write_jsonl

E = experiment_dir("e04_cue_family")
cfg = yaml.safe_load((E / "config.yaml").read_text())
rows = read_jsonl(problems_path(cfg["benchmark"]))[cfg["exclude_first"]:]
random.Random(cfg["split_seed"]).shuffle(rows)
screen, confirm = rows[:cfg["screen_problems"]], rows[cfg["screen_problems"]:cfg["screen_problems"] + cfg["confirm_problems"]]
write_jsonl(E / "data" / "screen.jsonl", screen)
write_jsonl(E / "data" / "confirm.jsonl", confirm)
print(len(screen), len(confirm), len({r["problem_key"] for r in screen} & {r["problem_key"] for r in confirm}))
