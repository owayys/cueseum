# e01 log

## Environment (2026-10-17)
- Host: Intel Iris Xe only, no NVIDIA GPU, 3.4 GB free disk. Upstream `setup_env.sh` needs CUDA 13 and ~25 GB, so it was not run.
- CPU-only venv for library tests and Phase 1: `uv venv --python 3.11`, `pip install --no-deps -e third_party/cues -e .`. Versions: math-verify 0.9.0 (upstream pin), numpy 2.4.6, pandas 3.0.6, pyarrow 26.0.0, matplotlib 3.11.2, pyyaml 6.0.3, pytest 9.1.1 (scipy 1.17.1 installed, unused). Not used for any rollouts.
- Phases 0, 2, 3, 4 and 6 are blocked until a GPU with ≥24 GB is available (§4).

## Phase 1: problem set (2026-10-17, CPU, 0 GPU-hours)
- Source: 7,495 rows. Dropped 2 rows with `level: null`.
- Probe exclusion: all 300 rows of `math_train_probe.jsonl` match math_train by whitespace-normalized text, and all 300 are excluded. The beam uses only rows 0–99 and the screen rows 0–29, so excluding all 300 is conservative.
- Packet deviation: after exclusion the smallest subject × level cell has 40 rows, not ≥41. It still covers the 12 needed.
- Sampled 12 per cell with seed 0 → 420 problems. Every cell has 12. 0 overlap with the probe set or MATH-500.
- Normalized problem texts are unique in the source and in the 420, so no duplicate can land in both CV folds.
- Pilot: 1 per cell (seed 0) drawn from the 420 → 35.
- Output is deterministic: two runs give identical sha256 (`tree_problems.jsonl` 426f7785…, `tree_problems_pilot.jsonl` e1c40a7b…).

## Upstream fork (2026-10-17, before any GPU run)
- Submodule now points at `owayys/cues` @ `339de49`, one commit on top of `cd9caab`: `enforce_eager=False` in `cues/evaluate.py` (CUDA graphs on, for throughput). Approved by the user. Sampling settings are unchanged; rollouts are not token-identical to upstream's. All GPU phases use this commit.

## Persistence (2026-10-17)
- Every GPU-phase command runs through `scripts/logged.sh <phase> <step> cmd…`, which appends its console output to `$CUESEUM_RUNS/e01_cue_tree/<phase>/logs/<step>.log`.
- `scripts/snapshot.sh` records nvidia-smi, uname, installed packages, git state and selected env vars under `env/<UTC timestamp>/`. It never dumps the full env: pods inject `RUNPOD_API_KEY`.
- `scripts/pull.sh <user@host> <port> [remote_runs]` rsyncs the pod's `e01_cue_tree/` into local `runs/` after every phase. It never deletes anything locally.

## Pod (2026-10-17)
- RunPod `u7wq77zgsgdq5m`: secure cloud, EU-RO-1, 1× RTX PRO 4500 Blackwell (32 GB, driver 580.126.09, CUDA 13.0), image `runpod/base:1.0.2-ubuntu2204`, 20 GB container disk, 60 GB `/workspace` (network FS: rsync needs `--no-owner --no-group`, and uv can't hardlink, so it copies). $0.72/hr GPU, $0.731/hr all-in. Created 08:37:12Z.
- The repo was rsynced from local at `0e64f6b` (the repo is private, so no GitHub token went onto the pod).
- `setup_env.sh` was run unmodified into `/root/env` (container disk), with `UV_CACHE_DIR=/workspace/uv-cache` (15 GB, persistent). It took 7.5 min. Upstream's 30 tests passed, and it reports torch 2.11.0+cu130, vllm 0.26.0, cuda available. `uv pip install -e .` added only matplotlib and its deps. Upstream's pins give numpy 2.3.5, pandas 3.0.5, pyarrow 25.0.1 (local CPU venv: 2.4.6, 3.0.6, 26.0.0). cueseum's 16 tests pass on the pod. Snapshot: `env/20261017T084908Z/`.

## Phase 0: smoke test (08:49–08:55Z)
- `cues demo --model qwen4b`: rc=0. pass@1 is 0.8 with no cue and 0.6 with ` To determine` (5 MATH-500 problems × 1 rollout; workflow check only).
- vLLM engine init takes 228 s per process, 113 s of it CUDA-graph capture (the cost of `enforce_eager=False`). The DeepGEMM `CUDA_HOME` warning is harmless, since that optional kernel is skipped.
- Rollout records carry all 8 required fields. `load_cells` reads 10 rows. The one no-answer rollout has `committed=False` and a null `answer_key`.

## Phase 2: cue list (08:56–08:58Z)
- `cues search --beam-only`: 31 openings, 20 nominees. Upstream's `nominees.json` includes `"none": ""`, which `build_cues.py` drops.
- Of the packet's extras, ` Let's` and ` First,` were already nominees. Added ` Okay,`, ` Alright,`, ` \n\nOkay`, for **23 cues** plus `--cues none`. Names are upstream `cue_slug`s, so they match the cell directories.
- `token_report` (model tokenizer, rendered `boxed` prompt ending `Solution:`): no cue merges with the prompt. Ids are in `data/tree_cues_tokens.json`. Two beam cues end in a bare space (` `, ` Step `). They are kept as upstream's beam returned them.
- Spend at 08:56Z: $0.18 (account balance $50.00 → $49.82).

## Phase 3: pilot (08:58:51–09:29:36Z, 0.51 GPU-h)
- 35 problems × 24 cues (23 plus none) × 8 rollouts = 6,720 records. rc=0.
- Engine init 75 s (graph compile cached from Phase 0). Generation 0.49 h, 3.45M output tokens, 1,951 tok/s.
- Gates (`analysis/pilot_report.py`):
  - **Projection:** full run 5.92 GPU-h ≈ $4.33 at $0.731/hr (12 × generation time + one init). That is a ceiling: the full run batches 3,360 sequences per cue against the pilot's 280.
  - **Cap rate:** max 9.6% (` Alright,`). All others ≤ 5%.
  - **Extraction errors:** 0.18% (has `\boxed` but no parsed answer).
  - **Sanity:** ` To determine` 0.782 vs no-cue 0.629. Highest pilot accuracy: ` Alright,` 0.800. Lowest: ` Let $` 0.493.
- All gates pass, so the full run was launched immediately, without reusing pilot cells (they are a separate benchmark file).
- Spend at 09:30Z: $0.60 (balance $49.40).

## Phase 4: full run (started 09:30:21Z)
