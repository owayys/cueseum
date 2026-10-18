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
- The Phase 2 pod `ozfde68yculngd` was deleted at the user's request after a checksum-verified pull.

## Phase 3: cue probability, H4 (2026-10-18)
- `scripts/cue_probability.py <model> <out> [other_model.json]`:
  - loads the model as upstream `cues/beam.py` does (bf16, `device_map="auto"`, `tok(prompt)` ids);
  - replays the beam on each of the 100 probe problems via `cueseum.cueprob` (depth 2, top_first 12, top_second 4, width 40) and keeps every next-token distribution in a per-problem cache;
  - measures the cue set on both models: the packet's ` Alright,`, ` To determine` and ` To`, the 4B's top 5 (` To`, ` We`, ` Let`, ` The`, ` To find`; recorded in config from e01's beam and reproduced here), and the 14B's own top 5.

  The 14B ran first, so its top 5 could be passed to the 4B run.
- Pod `gasfs5e8rrt9ju`: 1× A40 48 GB, secure, EU-SE-1, $0.59/hr, driver 580.159.03 / CUDA 13.0. It was chosen over the RTX PRO 4500 because the 14B fits in 48 GB without CPU offload, and it is cheaper per hour. Setup took 2.2 min, and all tests pass (snapshot `env/20261018T143724Z/`). The 14B ran 14:37–14:40Z (download ~1 min) and the 4B 14:40–14:42Z, both rc=0. Pulled, checksum-verified, and the pod deleted at 14:43Z. Phase 3 cost about $0.10.
- **Results** (`results/cue_probabilities.json`):
  - ` Alright,` on the 4B: mean prob 0.0018. Median first-token rank 49 (the beam keeps the top 12). Removed by `top_first` on 99% of problems and `beam_width` on 1%. In the beam on 0%, so never a candidate.
  - ` Alright,` on the 14B: mean prob 0.040 (22×). Median ranks [7, 1]. In the beam on 85%. 10th of the 14B's 32 candidates, so inside the top-20 shortlist but not at the top. The 14B's top 5 are ` To`, ` To find`, ` The`, ` We`, ` To solve`.
  - ` To determine`: 4B 0.024 (candidate 16, removed by `top_second` on 20%); 14B 0.053 (candidate 8).
- **Cross-check vs upstream's beam** (e01 `beam.json`, same model, prompt and probes, on the RTX PRO 4500):
  - all 31 upstream openings reproduced, plus 2 borderline extras (` Since $`, ` \nStep`);
  - max |mass diff| 0.0032, and max |problem-fraction diff| 0.04.
  
  So it is close but **not within rounding**, as the packet expected. The likely cause, unverified, is bf16 numerics differing across GPU architectures (Ampere vs Blackwell), which shifts openings near the cut-offs.
- **e02 spend so far: $3.97** (balance $46.35 → $42.38).

## Pilot descriptives (exploratory, 2026-10-18, local CPU)
- `analysis/pilot_descriptives.py` runs on the pilot's 600 rollouts. It is **not** a hypothesis test, because Phase 2 never completed. It truncates each completion with `cueseum.rescore` (Qwen3-4B tokenizer, `transformers==5.15.0` installed locally, tokenizer only) at 4k/8k/16k/31,744 and rescores with upstream's grader, and it counts checking phrases (`let me check|double-check|verify|\bwait\b`, case-insensitive).
- pass@1 is **unchanged at every budget**: ` Alright,` 0.860, ` To determine` 0.760, no cue 0.565. Only 22 rollouts exceed 4,096 tokens, 13 of them capped at 31,744 and all wrong. The single long correct one (` Alright,`) had boxed its answer within its first 4,096 tokens.
- Rescoring at the full budget matches the stored grades on 600/600, with 0 timeouts.
- Checking phrases appear in 68.0% of ` Alright,` responses, 4.0% for ` To determine` and 4.5% for no cue.
