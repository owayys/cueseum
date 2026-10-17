import numpy as np


def hf_next_probs(model):
    import torch

    def next_probs(ids):
        with torch.no_grad():
            x = torch.tensor([ids], device=model.device)
            return torch.softmax(model(input_ids=x).logits[0, -1].float(), -1).cpu().numpy()
    return next_probs


def _cached(next_probs):
    cache = {}

    def get(ids):
        key = tuple(ids)
        if key not in cache:
            cache[key] = next_probs(ids)
        return cache[key]
    return get


def beam(next_probs, prompt_ids, depth, top_first=12, top_second=4, beam_width=40):
    beams, kept = [((), 1.0)], []
    for step in range(depth):
        scored = []
        for opening, p in beams:
            probs = next_probs(list(prompt_ids) + list(opening))
            k = top_first if step == 0 else top_second
            for t in np.argsort(-probs, kind="stable")[:k]:
                scored.append((opening + (int(t),), p * float(probs[t])))
        scored.sort(key=lambda x: -x[1])
        beams = scored[:beam_width]
        kept.append(dict(beams))
    return kept


def measure(next_probs, prompt_ids, cue_ids, top_first=12, top_second=4, beam_width=40):
    next_probs = _cached(next_probs)
    kept = beam(next_probs, prompt_ids, max(map(len, cue_ids.values())), top_first, top_second, beam_width)
    out = {}
    for name, ids in cue_ids.items():
        p, ranks = 1.0, []
        for i, t in enumerate(ids):
            probs = next_probs(list(prompt_ids) + list(ids[:i]))
            ranks.append(int((probs > probs[t]).sum()) + 1)
            p *= float(probs[t])
        level = kept[len(ids) - 1]
        if tuple(ids) in level:
            removed = None
        elif ranks[0] > top_first:
            removed = "top_first"
        elif any(r > top_second for r in ranks[1:]):
            removed = "top_second"
        else:
            removed = "beam_width"
        out[name] = {"prob": p, "ranks": ranks, "beam_mass": level.get(tuple(ids), 0.0), "removed_by": removed}
    return out


def aggregate(per_problem, min_problem_fraction=0.5):
    out = {}
    for name in per_problem[0]:
        rows = [r[name] for r in per_problem]
        n, present = len(rows), sum(r["removed_by"] is None for r in rows)
        out[name] = {
            "mean_prob": float(np.mean([r["prob"] for r in rows])),
            "mean_beam_mass": float(np.mean([r["beam_mass"] for r in rows])),
            "median_ranks": [float(x) for x in np.median([r["ranks"] for r in rows], axis=0)],
            "problem_fraction": present / n,
            "passes_min_fraction": present >= min_problem_fraction * n,
            "removed_by": {k: sum(r["removed_by"] == k for r in rows) / n for k in ("top_first", "top_second", "beam_width")},
        }
    return out
