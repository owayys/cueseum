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
