import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, cues):
    Path(path).write_text(json.dumps(cues, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def token_report(tokenizer, prompt, cues):
    base = tokenizer.encode(prompt, add_special_tokens=False)
    report = {}
    for name, cue in cues.items():
        ids = tokenizer.encode(prompt + cue, add_special_tokens=False)
        k = 0
        while k < min(len(base), len(ids)) and base[k] == ids[k]:
            k += 1
        report[name] = {"cue": cue, "ids": ids[k:], "merges": k < len(base)}
    return report
