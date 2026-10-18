# e02: Do cues from a larger model transfer to a smaller sibling?

**Status: paused (2026-10-18) before the confirmatory test.** H1 and H3 are unanswered. H4 is done, and the pilot descriptives are in. No §6 row applies yet.

## Why it is paused
H1 needs the full Phase 2 run: 500 MATH-500 problems × 3 cues × 32 rollouts at 31,744 tokens. On the RTX PRO 4500 (32 GB), the KV cache holds about 155k tokens, so at most about 4.7 full-length sequences decode at once. Measured steady throughput was **334 tok/s**, which projects to about $44 for Phase 2 alone, against the packet's $25 cap. The pilot's own projection ($51) had warned of this. Phase 2 was started with a cost checkpoint and stopped once the measured rate made the overrun clear. The partial first cell was lost, because upstream writes a cell only when its whole batch completes. The packet's 16-rollout fallback projects to about $30 with the Phase 4 screen, still over the cap.

## What we have
**Pilot** (50 problems × 4 rollouts at 31,744 tokens; preliminary, not confirmatory):

| cue | pass@1 | no answer | cap rate | mean tokens |
|---|---|---|---|---|
| ` Alright,` | 0.860 | 0.025 | 0.010 | 1,960 |
| ` To determine` | 0.760 | 0.025 | 0.010 | 802 |
| no cue | 0.565 | 0.065 | 0.045 | 1,734 |

The no-cue rate is close to the paper's 54.9%. The ordering matches e01.

**H4 (descriptive, done):** opening probability over the 100 probe problems (`results/cue_probabilities.json`).

| | Qwen3-4B | Qwen3-14B |
|---|---|---|
| ` Alright,` mean opening prob | 0.0018 | 0.040 (22×) |
| median ranks (first token, second token) | 49, 1 | 7, 1 |
| survives upstream's beam on | 0% (removed by `top_first` on 99%) | 85% |
| rank among the model's beam candidates | not a candidate | 10 of 32 |

The 4B's search never proposes ` Alright,`: its first token typically ranks 49th, and the beam keeps 12. For the 14B it's a shortlisted, mid-list opening, not "at or near the top". The replay reproduces all 31 of upstream's 4B beam openings, within 0.0032 mass and 0.04 problem fraction, which is close but not within rounding. The likely cause, unverified, is bf16 numerics on a different GPU.

**Pilot descriptives (exploratory, `results/pilot_descriptives.json`):**
- Truncating to 4k/8k/16k leaves every cue's pilot pass@1 unchanged. All correct answers are boxed within the first 4,096 tokens.
- Checking phrases appear in 68% of ` Alright,` responses, 4% for ` To determine` and 4.5% for no cue.

These hint at H2 but cannot test it.

## To resume
- **H1 (Phase 2):** needs a higher budget or a faster setup. A larger-memory GPU (for example an A100 80 GB or H100) raises how many sequences decode at once. A ~20-min benchmark (~$1) would give a measured projection before committing. Phase 2's commands are in `scripts/run.sh`.
- **H3 (Phase 4, the screen with ` Alright,` added):** estimated at about $4–6 on the RTX PRO 4500 (unmeasured).
- **H2:** comes free from Phase 2's rollouts (`cueseum.rescore`).

## Cost so far
**$3.97**: pilot and setup $0.81, the lost Phase 2 attempt $2.9 (including restarts), Phase 3 $0.10.

## Caveats (from the packet)
One family (Qwen3), one direction (14B → 4B), one prompt, math only, temperature 0.6. The pilot is far too small for H1. Rollouts come from the fork with CUDA graphs on, so the sampling distribution is the same as upstream's but the rollouts are not token-identical.

## Next
Ideas outside this packet's scope go here.
- Upstream writes each cell only when its whole batch finishes. Splitting a 31k-token run into smaller `--problem-count` shards would make checkpoints cheap and losses bounded.
