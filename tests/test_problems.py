import pytest

from cueseum import problems

ROWS = [{"problem": f"p {s} {l} {i}", "s": s, "l": l} for s in "ab" for l in (1, 2) for i in range(5)]


def test_stratified_sample_counts_and_determinism():
    out = problems.stratified_sample(ROWS, ["s", "l"], 3, seed=0)
    assert len(out) == 12
    assert all(sum(r["s"] == s and r["l"] == l for r in out) == 3 for s in "ab" for l in (1, 2))
    assert out == problems.stratified_sample(ROWS, ["s", "l"], 3, seed=0)


def test_stratified_sample_excludes_normalized_text():
    out = problems.stratified_sample(ROWS, ["s", "l"], 4, seed=0, exclude_texts=["p  a 1\n0"])
    assert "p a 1 0" not in {r["problem"] for r in out}


def test_stratified_sample_short_cell():
    with pytest.raises(ValueError):
        problems.stratified_sample(ROWS, ["s", "l"], 6, seed=0)


def test_jsonl_roundtrip(tmp_path):
    problems.write_jsonl(tmp_path / "x.jsonl", ROWS)
    assert problems.read_jsonl(tmp_path / "x.jsonl") == ROWS
