import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "third_party" / "cues"


def runs(experiment, *parts):
    return Path(os.environ["CUESEUM_RUNS"], experiment, *parts)


def experiment_dir(experiment):
    return ROOT / "experiments" / experiment


def commit(repo=ROOT):
    return subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def upstream_commit():
    return commit(UPSTREAM)
