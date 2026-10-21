import collections
import random


def first_words(texts, after="<think>"):
    words = collections.Counter()
    for t in texts:
        body = t.split(after, 1)[-1].split()
        if body:
            words[body[0]] += 1
    return words


def reasoning_cues(words, taken, take):
    return [c for c in (" " + w for w, _ in words.most_common()) if c not in taken][:take]


def band_candidates(mean, anchor, band, decode, exclude):
    lo, hi = band[0] * mean[anchor], band[1] * mean[anchor]
    excluded = {w.lower() for w in exclude}
    out = []
    for t in range(len(mean)):
        s = decode(t)
        if lo <= mean[t] <= hi and s.startswith(" ") and s[1:].isalpha() and s[1:].lower() not in excluded:
            out.append((t, s, float(mean[t])))
    return out, (float(lo), float(hi))


def draw(candidates, take, seed):
    return random.Random(seed).sample(candidates, take)
