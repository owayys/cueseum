import json

import pandas as pd

from cueseum import rollouts


def record(cue, key, index, completion, correct):
    return {"problem_key": key, "rollout_index": index, "cue": cue, "label": "m", "prompt": "boxed",
            "experiment": {"grading": "boxed", "cue": cue}, "committed": "boxed" in completion,
            "correct": correct, "hit_token_cap": False, "finish_reason": "stop", "output_tokens": 10,
            "max_tokens_used": 4096, "completion": completion}


def write_cell(root, slug, records):
    cell = root / "m" / "boxed" / "bench" / slug
    cell.mkdir(parents=True)
    (cell / "rollouts_p00000.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))


def test_load_cells(tmp_path):
    write_cell(tmp_path, "none", [record("", "p1", 0, r"so \boxed{\frac{1}{2}}", True),
                                  record("", "p1", 1, "no answer", False)])
    write_cell(tmp_path, "to", [record(" To", "p1", 0, r" To get \boxed{0.5}", True)])
    df = rollouts.load_cells(tmp_path)
    assert list(df.columns) == rollouts.COLUMNS
    assert len(df) == 3
    keys = df.set_index(["cue", "rollout_index"])["answer_key"]
    assert keys[("", 0)] == keys[(" To", 0)] == "0.5"
    assert pd.isna(keys[("", 1)])
    rollouts.save(df, tmp_path / "s.parquet")
    assert rollouts.load(tmp_path / "s.parquet").equals(df)
