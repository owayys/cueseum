# e02 log

## Pod (2026-10-17)
- RunPod `i3ai1fw2qax9mh`: secure cloud, EU-RO-1, 1× RTX PRO 4500 Blackwell (32 GB). Driver 595.91.07, CUDA 13.2, which is newer than e01's 580.126.09 / 13.0. Image `runpod/base:1.0.2-ubuntu2204`, 20 GB container disk, 100 GB `/workspace` (network FS). $0.72/hr. Created 17:55:38Z.
- Repo rsynced from local `main` `1c9ad7a`, plus this branch's uncommitted e02 scripts.
- `scripts/logged.sh`, `snapshot.sh` and `pull.sh` are copies of e01's with the experiment name changed, since experiments don't import from each other.
- Setup 17:57:20–18:05:06Z (7.8 min): upstream `setup_env.sh` run unmodified into `/root/env`, with `UV_CACHE_DIR=/workspace/uv-cache`. Upstream's 30 tests pass; torch 2.11.0+cu130, vllm 0.26.0, cuda available. `uv pip install -e .` added only cueseum's analysis dependencies (matplotlib, scipy, scikit-learn and their deps). cueseum's 22 tests pass. Snapshot: `env/20261017T180619Z/`.

## Phase 0: smoke test (18:06–18:11Z)
- `none` and ` Alright,` on 5 MATH-500 problems × 2 rollouts, 2,048 tokens, rc=0. vLLM init 178 s. pass@1 0.7 / 1.0 (workflow check only).
- The cue heads every stored completion (10/10 per cue). `load_cells` reads 20 rows with all 8 columns.
- The smoke step was first run by hand with the same flags as `run.sh`, then re-run (cached) when `run.sh` launched the pilot.

## Phase 1: pilot (18:11–18:58Z, 0.77 h incl. a cached smoke rerun)
- Run through `run.sh`: the smoke step reran from cache (vLLM init 57 s, no new rollouts), then the pilot. 50 problems × 3 cues × 4 rollouts, 31,744 tokens. rc=0.

| cue | pass@1 | no answer | cap rate | mean tokens |
|---|---|---|---|---|
| ` Alright,` | 0.860 | 0.025 | 0.010 | 1,960 |
| ` To determine` | 0.760 | 0.025 | 0.010 | 802 |
| no cue | 0.565 | 0.065 | 0.045 | 1,734 |

- Gates:
  - Cap rate: max 4.5%, within the 10% limit. **Pass.**
  - Extraction errors: 0.0%, within the 2% limit. **Pass.**
  - Projected Phases 2–4 cost: `pilot_report.py` says **$51.41**, above the $25 cap. **Fail as written.**
- The projection divides by the pilot's average throughput (333 tok/s). That average is dominated by each cue's tail: in vLLM's log, about 170 of 200 rollouts per cue finished within about 22 s at ~2,350 tok/s, and the remaining ~20 min per cue went on a few long generations. So the projection is likely a large overestimate for 8,000-sequence batches. A rough alternative: ~72M tokens at 2,000–2,800 tok/s plus 6 tails of ~20 min ≈ 9–12 h for Phase 2, and ~3 h for the screen, ≈ $9–11 in total. That estimate is unverified.
- Per §5 the run was stopped and reported. Options given to the user: (1) start Phase 2 with a checkpoint after the first cue's cell, (2) cut to 16 rollouts, (3) escalate to the supervisor. **User decision (2026-10-17): stop here and resume later.**
- Pod `i3ai1fw2qax9mh` stopped at 19:04Z after a checksum-verified pull. Its 100 GB volume is kept at $0.028/hr. **Spend so far: $0.81** (balance $46.35 → $45.54).

## Resume (2026-10-18)
- **User decision:** run Phase 2 with a cost checkpoint after the first cell. If the measured projection for Phases 2–4 exceeds $25, stop.
- `pod start i3ai1fw2qax9mh` failed: "not enough free GPUs on the host machine" (the stopped pod's GPU had been reassigned). Created pod `ozfde68yculngd` (same spec: RTX PRO 4500, EU-RO-1, 100 GB volume) at 07:08:29Z. Driver 580.159.04 / CUDA 13.0, which differs from the pilot pod's 595.91.07 / 13.2. The software stack is identical. The old pod was deleted at the user's request at about 07:20Z; its outputs were all local and checksum-verified.
- Setup 07:09:28–07:13:54Z (4.4 min). Upstream's 30 tests and cueseum's 22 tests pass. Snapshot `env/20261018T071432Z/`.

## Phase 2: main run (started 07:14:43Z)
- `scripts/phase2.sh` = `run.sh` with the smoke and pilot steps removed, generated on the pod by `sed`. Those steps were done on the previous pod, and rerunning them from cache still costs vLLM init. Batch 1 (`eval_b1`), then batch 2 (`eval_b2`, `--rollout-index-offset 16 --suffix _b2`).
- vLLM: KV cache 21.33 GiB = 155,296 tokens. "Maximum concurrency for 32,768 tokens per request: 4.74x." Engine init 185 s.
- **Checkpoint triggered before the first cell finished.** At 10:38Z (3 h 08 min in), the no-cue cell of batch 1 was at 3,536/8,000 rollouts, with vLLM reporting 334 output tok/s and an estimated 7 h 43 min remaining. The GPU was at 100% and the log shows no preemptions. **The pilot's 333 tok/s was the steady state, not a tail artifact**: throughput at 31k context is limited by KV-cache capacity, which caps how many sequences decode concurrently. My pilot-time explanation was wrong, and the pilot report's $51 projection was about right.
- Measured projection on this GPU: about 72M tokens at about 334 tok/s ≈ 60 h ≈ $44 for Phase 2 alone. The packet's 16-rollout fallback is ≈ 30 h ≈ $22, plus the screen ≈ $8, so still over $25.
- Stopped at 10:39Z per the user's checkpoint rule (tmux session killed, vLLM processes gone, GPU memory freed). No cell was written: upstream writes a cell only when its whole batch finishes, so the partial cell (~$2.3 of compute) is lost. Log pulled and checksum-verified. Pod `ozfde68yculngd` stopped at 10:40Z (volume $0.028/hr).
- **e02 spend so far: $3.73** (balance $46.35 → $42.61).
