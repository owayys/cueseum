from cueseum import paths


def test_runs(monkeypatch, tmp_path):
    monkeypatch.setenv("CUESEUM_RUNS", str(tmp_path))
    assert paths.runs("e01", "pilot") == tmp_path / "e01" / "pilot"


def test_commits():
    assert len(paths.commit()) == 40
    assert paths.upstream_commit() == "339de4922c063d2b33271f999a28042183bb0e89"


def test_experiment_dir():
    assert (paths.experiment_dir("e01_cue_tree") / "PACKET.md").exists()
