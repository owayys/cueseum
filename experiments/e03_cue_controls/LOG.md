# e03 log

## Stage 1: derive groups C and D (2026-10-21, 08:46–08:52Z)
- Problem splits (`scripts/build_problems.py`, local): MATH-500 minus the first 50, shuffled with seed 0 → `data/screen.jsonl` (100) and `data/confirm.jsonl` (350), with no overlap.
- Pod `iadotqq0kqfzlk`: 1× A40 48 GB, secure, $0.59/hr, driver 595.91.07 / CUDA 13.2. Attended; after each step I checked that the account held exactly 1 pod. Setup rc=0 (snapshot `env/20261021T084931Z/`). Pulled, checksum-verified, deleted (`not_found`, 0 pods). **Cost $0.06.**
- **Group C** (`derive_reasoning_style.py`; post-trained Qwen3-4B @ `1cfa9a7`, chat template with thinking on, upstream's chat prompt; 100 probe problems × 4 samples at temperature 0.6, top-p 0.95, 12 tokens):
  - **400/400** reasoning traces open with "Okay," (typically "Okay, so I need to…");
  - the rule ("top 3 first words") therefore yields one cue, **` Okay,`**;
  - no extra cues were invented to reach 3. It isn't a deviation; the rule simply has one result.
- **Group D** (`derive_probability_matched.py`; 4B base, mean first-token probability over the 100 probe problems):
  - ` Alright` has mean probability 0.00185 and is the 43rd most likely first token by mean probability (per-problem median rank 49, from e02);
  - the band [0.5×, 2×] holds **23** candidate tokens (leading space, alphabetic, not in the exclusion list);
  - `random.Random(0).sample` picked **` Every`** (0.00096, rank 55), **` Each`** (0.00284, rank 34) and **` It`** (0.00253, rank 36);
  - the band also contains word fragments (` Ob`, ` Comb`, ` Distrib`), which the rule allows; none were drawn.
- **Bug fixed before group D's successful run:** the first run failed because YAML read the unquoted `Yes` in `exclude_words` as a boolean. The words are now quoted (commit `58b7834`). The failed run produced no output and cost nothing extra.
- **Final cue list** (`data/cues.json`):
  - A: ` Alright,`
  - B: ` \n\nOkay`, ` \n\n`
  - C: ` Okay,`
  - D: ` Every`, ` Each`, ` It`
  - E: ` To determine`, ` To`, and no cue

  That makes 9 cues plus no cue.
- **e03 spend so far: $0.06.**

## Stage 2: screen (2026-10-21, 08:54–09:58Z)
- `analysis/screen.py` (the forwarding rule) was tested on synthetic rollouts in upstream's format before any GPU spend: a planted close control was forwarded, separated ones weren't, and reference cues were never forwarded.
- Pod `82csyqgzmops6t`: 1× A40, secure, $0.59/hr, driver 595.91.07. Attended, with the pod count checked after every step. Setup rc=0 (snapshot `env/20261021T085801Z/`). `stage2.sh` = `run.sh` without the stage-1 lines, generated on the pod by `sed`, so the stage-1 outputs weren't overwritten.
- Screen eval 08:58:17–09:58:10Z (1.0 h), rc=0: 10 cells × 100 problems × 8 rollouts at 4,096 tokens. vLLM init 53 s, about 1,730 tok/s. Pulled, checksum-verified, pod deleted (`not_found`, 0 pods). **Cost $0.63.**
- `results/screen.json`. pass@1:

| cue | pass@1 |
|---|---|
| ` Alright,` | 0.744 |
| ` To determine` | 0.684 |
| ` \n\nOkay` | 0.640 |
| ` To` | 0.603 |
| ` Okay,` | 0.580 |
| ` \n\n` | 0.522 |
| no cue | 0.500 |
| ` It` | 0.426 |
| ` Every` | 0.372 |
| ` Each` | 0.372 |

- (` Alright,` − control) 95% CI lower bounds across groups B–D range from +0.064 to +0.310, all ≥ +0.05, so **no control was forwarded**.
- ` Alright,` has the highest cap rate (13.5%) and no-answer rate (13.1%) at 4k, and the longest outputs (mean 1,613 tokens). Capped responses count as wrong, so the 4k budget biases *against* ` Alright,`. The packet's case for 4k (e02's pilot: no change from 31k) is weaker on these problems.

## Stage 3: confirm, skipped by rule
- No control met the forwarding rule, so the packet's confirm stage has nothing to run. The 350 confirm problems remain unused. Every control result is screen-only evidence, as §6 provides.
- **e03 spend so far: $0.69.**

## Stage 4: analysis and report (2026-10-21, local CPU)
- `analysis/final.py`:
  - for the 6 B–D controls: per-problem paired differences, 10,000 bootstrap resamples (seed 0), two-sided p (floored at 1/10,001), and Holm step-down with adjusted-level percentile CIs;
  - descriptive pass@1 CIs per cue;
  - reference comparisons outside the family;
  - writes `results/scores.parquet` and `results/summary.json`.
- **All six are below** after Holm (the tightest is ` \n\nOkay`, +0.104 [+0.049, +0.158] at 99.2%). **Decision: row 1, specific to ` Alright,`.** All p-values sit at the floor, so Holm's ordering among them is a tie; the tie gave the closest control the strictest level, which is the conservative case.
- REPORT.md, the README row and the `docs/findings.md` paragraph are written. **Total e03 spend: $0.69.**
