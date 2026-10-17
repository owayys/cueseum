import json
import re
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from cueseum.rollouts import load_cells

root, rate, scale = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
df = load_cells(root)
boxed = []
for f in sorted(root.rglob("rollouts_p*.jsonl")):
    boxed += ["\\boxed" in json.loads(line)["completion"] for line in f.read_text().splitlines()]
df["has_boxed"] = boxed
by = df.groupby("cue", sort=False)
table = pd.DataFrame({"acc": by.correct.mean(), "no_answer": 1 - by.committed.mean(),
                      "cap_rate": by.hit_token_cap.mean(), "mean_tokens": by.output_tokens.mean()}).round(3)
log = (root / "logs" / "eval.log").read_text()
ts = lambda pat: datetime.fromisoformat(re.search(pat, log).group(1).replace("Z", "+00:00"))
start, end = ts(r"# (\S+) start"), ts(r"# (\S+) end")
init = float(re.search(r"init engine .* took ([\d.]+) s", log).group(1))
gen_h = ((end - start).total_seconds() - init) / 3600
summary = {
    "records": len(df), "problems": df.problem_key.nunique(), "cues": df.cue.nunique(),
    "extraction_errors": float((df.has_boxed & ~df.committed).mean()),
    "max_cap_rate": float(table.cap_rate.max()), "output_tokens": int(df.output_tokens.sum()),
    "wall_h": round((end - start).total_seconds() / 3600, 3), "gen_h": round(gen_h, 3),
    "tokens_per_s": round(df.output_tokens.sum() / (gen_h * 3600)),
    "projected_full_h": round(gen_h * scale + init / 3600, 2),
    "projected_full_usd": round((gen_h * scale + init / 3600) * rate, 2),
}
print(table.to_string())
print(json.dumps(summary, indent=1))
