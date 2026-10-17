# e01 log

## Environment (2026-10-17)
- Host: Intel Iris Xe only, no NVIDIA GPU, 3.4 GB free disk. Upstream `setup_env.sh` needs CUDA 13 and ~25 GB, so it was not run.
- CPU-only venv for library tests and Phase 1: `uv venv --python 3.11`, `math-verify==0.9.0` (upstream pin), unpinned numpy/pandas/pyarrow/matplotlib/pyyaml/pytest, `pip install --no-deps -e third_party/cues -e .`. Not used for any rollouts.
- Phases 0, 2, 3, 4 and 6 are blocked until a GPU with ≥24 GB is available (§4).

## Phase 1: problem set (2026-10-17, CPU, 0 GPU-hours)
- Source: 7,495 rows. Dropped 2 rows with `level: null`.
- Probe exclusion: all 300 rows of `math_train_probe.jsonl` match math_train by whitespace-normalized text, and all 300 are excluded. The beam uses only rows 0–99 and the screen rows 0–29, so excluding all 300 is conservative.
- Packet deviation: after exclusion the smallest subject × level cell has 40 rows, not ≥41. It still covers the 12 needed.
- Sampled 12 per cell with seed 0 → 420 problems. Every cell has 12. 0 overlap with the probe set or MATH-500.
- Pilot: 1 per cell (seed 0) drawn from the 420 → 35.
- Output is deterministic: two runs give identical sha256 (`tree_problems.jsonl` 426f7785…, `tree_problems_pilot.jsonl` e1c40a7b…).
