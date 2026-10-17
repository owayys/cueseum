import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from cueseum.rollouts import load_cells

root, rate = Path(sys.argv[1]), float(sys.argv[2])
MAIN_ROLLOUTS, SCREEN_ROLLOUTS, SCREEN_CAP, PHASE3_H = 500 * 32, 22 * 30 * 16, 16384, 0.3
df = load_cells(root)
boxed = []
for f in sorted(root.rglob("rollouts_p*.jsonl")):
    boxed += ["\\boxed" in json.loads(line)["completion"] for line in f.read_text().splitlines()]
df["has_boxed"] = boxed
df["cue"] = df.cue.map(lambda c: repr(c) if c else "no cue")
by = df.groupby("cue")
table = pd.DataFrame({"acc": by.correct.mean(), "no_answer": 1 - by.committed.mean(), "cap_rate": by.hit_token_cap.mean(),
                      "mean_tokens": by.output_tokens.mean(), "max_tokens": by.output_tokens.max()}).round(3)
log = (root / "logs" / "eval.log").read_text()
ts = lambda pat: datetime.fromisoformat(re.search(pat, log).group(1).replace("Z", "+00:00"))
wall_h = (ts(r"# (\S+) end") - ts(r"# (\S+) start")).total_seconds() / 3600
init_h = float(re.search(r"init engine .* took ([\d.]+) s", log).group(1)) / 3600
tps = df.output_tokens.sum() / ((wall_h - init_h) * 3600)
main_h = 2 * init_h + MAIN_ROLLOUTS * table.mean_tokens.sum() / tps / 3600
screen_h = init_h + SCREEN_ROLLOUTS * df.output_tokens.clip(upper=SCREEN_CAP).mean() / tps / 3600
summary = {
    "records": len(df), "extraction_errors": float((df.has_boxed & ~df.committed).mean()),
    "max_cap_rate": float(table.cap_rate.max()), "wall_h": round(wall_h, 3), "tokens_per_s": round(tps),
    "projected_h": {"phase2": round(main_h, 2), "phase4_screen": round(screen_h, 2), "phase3": PHASE3_H},
    "projected_usd_phases_2_4": round((main_h + screen_h + PHASE3_H) * rate, 2),
}
print(table.to_string())
print(json.dumps(summary, indent=1))
