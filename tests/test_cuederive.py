import numpy as np

from cueseum import cuederive


def test_first_words_and_reasoning_cues():
    w = cuederive.first_words(["<think>\nOkay, so", "<think>\nOkay, so", "<think>\nAlright, let", "<think>\n"])
    assert w == {"Okay,": 2, "Alright,": 1}
    assert cuederive.reasoning_cues(w, {" Alright,"}, 3) == [" Okay,"]


def test_band_candidates_and_draw():
    vocab = [" Alright", " Every", " Each", " so", " Ok", "x", " 12", " It"]
    mean = np.array([0.010, 0.006, 0.019, 0.010, 0.010, 0.010, 0.010, 0.030])
    cands, band = cuederive.band_candidates(mean, 0, [0.5, 2.0], vocab.__getitem__, ["Ok", "Alright"])
    assert [s for _, s, _ in cands] == [" Every", " Each", " so"]
    assert band == (0.005, 0.02)
    assert cuederive.draw(cands, 2, 0) == cuederive.draw(cands, 2, 0)
