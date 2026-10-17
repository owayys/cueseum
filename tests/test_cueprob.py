import collections

import numpy as np

from cueseum import cueprob

V = 30


def fake(ids):
    rng = np.random.default_rng(abs(hash(tuple(ids))) % 2**32)
    p = rng.dirichlet(np.full(V, 0.3))
    return p


def upstream_mass(problems, depth=2, top_first=12, top_second=4, beam_width=40):
    presence, mass = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    for ids in problems:
        beams = [(list(ids), 1.0, ())]
        for step in range(depth):
            scored = []
            for b, p, opening in beams:
                probs = fake(b)
                top = np.argsort(-probs, kind="stable")[:top_first if step == 0 else top_second]
                scored += [(b + [int(t)], p * float(probs[t]), opening + (int(t),)) for t in top]
            scored.sort(key=lambda x: -x[1])
            beams = scored[:beam_width]
            for _, p, opening in beams:
                presence[step + 1][opening] += 1
                mass[step + 1][opening] += p
    return {o: (mass[d][o] / len(problems), presence[d][o] / len(problems)) for d in presence for o in presence[d]}


def test_measure_matches_upstream_beam():
    problems = [[1, i, 2] for i in range(12)]
    ref = upstream_mass(problems)
    common = max(ref, key=lambda o: ref[o][1] * (len(o) == 2))
    rare = next(o for o in ref if len(o) == 2 and ref[o][1] < 1)
    cues = {"common": list(common), "rare": list(rare), "single": [common[0]]}
    agg = cueprob.aggregate([cueprob.measure(fake, ids, cues) for ids in problems])
    for name, o in (("common", common), ("rare", rare), ("single", (common[0],))):
        assert np.isclose(agg[name]["mean_beam_mass"], ref[o][0])
        assert np.isclose(agg[name]["problem_fraction"], ref[o][1])
    assert agg["rare"]["mean_prob"] > agg["rare"]["mean_beam_mass"]


def test_prob_ranks_and_filters():
    ids = [1, 2, 3]
    p0 = fake(ids)
    worst = int(np.argmin(p0))
    t1 = int(np.argmax(p0))
    p1 = fake(ids + [t1])
    t2 = int(np.argsort(-p1)[5])
    r = cueprob.measure(fake, ids, {"far": [worst], "pair": [t1, t2]})
    assert r["far"]["ranks"] == [V] and r["far"]["removed_by"] == "top_first"
    assert np.isclose(r["pair"]["prob"], p0[t1] * p1[t2])
    assert r["pair"]["ranks"] == [1, 6] and r["pair"]["removed_by"] == "top_second" and r["pair"]["beam_mass"] == 0
