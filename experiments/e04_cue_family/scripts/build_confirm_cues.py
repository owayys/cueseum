import json

from cues.models import cue_slug

from cueseum.paths import experiment_dir

E = experiment_dir("e04_cue_family")
for m in ("qwen0.6b", "qwen1.7b", "qwen8b"):
    s = json.loads((E / "results" / f"screen_{m}.json").read_text())
    path = E / "data" / f"confirm_cues_{m}.json"
    if s["forwarded"]:
        cues = [" Alright,", *s["forwarded"]]
        path.write_text(json.dumps({cue_slug(c): c for c in cues}, indent=1, ensure_ascii=False) + "\n")
        print(m, cues)
    elif path.exists():
        path.unlink()
