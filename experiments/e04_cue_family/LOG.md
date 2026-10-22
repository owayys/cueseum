# e04 log

## Stage 1: derive per-size controls (2026-10-21, 12:19–12:38Z)
- Problem splits: `scripts/build_problems.py` (e03's rule) produces `data/screen.jsonl` and `data/confirm.jsonl`, **byte-identical to e03's**.
- The derivation logic moved into the library as `cueseum.cuederive` (#28), since e04 is its second user. e03's scripts are untouched.
- Pod `pdbet6e86c5heu`: 1× A40, secure, $0.59/hr, driver 595.91.07, 80 GB volume. Attended, with the pod count checked after every step. Setup rc=0 (snapshot `env/20261021T122307Z/`). Pulled, checksum-verified, deleted (`not_found`, 0 pods). **Cost $0.17.**
- **Bug:** the first 0.6B run hung for about 10 min, pegged on the CPU with the GPU idle. `derive_cues.py`'s decode helper called `len(tok)` once per token: 28.5 ms × 152k ≈ 1.2 h per model. e03 computed it once. Killed the run, fixed it (`dfb54e3`; the fixed loop takes 0.4 s), re-ran. The killed run saved nothing.

| size | C (reasoning first word) | ` Alright` mean first-token prob, rank | band candidates | D (seeded draw) |
|---|---|---|---|---|
| 0.6B | ` Okay,` (400/400) | 0.070, rank 4 | 4 | ` Since`, ` We`, ` The` |
| 1.7B | ` Okay,` (400/400) | 0.0057, rank 19 | 11 | ` When`, ` Consider`, ` A` |
| 8B | ` Okay,` (400/400) | 0.0003, rank 120 | 87 | ` Below`, ` Half`, ` Re` |

- **Notes:**
  - **0.6B:** ` Alright` is its 4th most likely first token, so its "probability-matched" controls are *common* openers; group D there tests equal probability, not rarity. Its D draw included ` We` and ` The`, which were also its beam proposals (context group E), so they were dropped from E to avoid counting them twice. That leaves no beam proposals for the 0.6B.
  - **8B:** ` Re` is a word fragment, which the rule allows.
  - **Group C:** every size's post-trained model opened 400/400 reasoning traces with "Okay,", the same as the 4B in e03.
- **Cue counts:** 0.6B 9 cues, 1.7B 11, 8B 11, plus no cue for each (`data/cues_<size>.json`, `data/eval_cues_<size>.json`).
- **e04 spend so far: $0.17.**

## Stage 2: screen (2026-10-22, 06:26–09:47Z)
- `analysis/screen.py` was tested before any GPU spend: synthetic success path (a planted near-tie was forwarded, nothing else), the revision guard (a wrong revision raises an error), and the config lookups.
- Pod `zm3cchrd7nm1nn`: 1× A40, $0.59/hr. Attended, with the pod count checked after every check-in. Setup rc=0 (snapshot `env/20261022T063031Z/`).
- **Launch error, caught and fixed:** my first `stage2.sh` was built with a faulty `awk` filter (`NR<=4 || /^cfg/{f=1} f` sets the print flag on line 1), so it contained all of `run.sh` and started re-running stage 1. Killed after about 1 min, while the models were still loading, with no stage-1 outputs overwritten. The pod's partial logs were renamed to `stage1_aborted_rerun/` so a pull couldn't overwrite the real stage-1 logs. The fixed filter (`NR<=4{print; next} /^cfg\(\)/{f=1} f`) was verified locally (no stage-1 or build lines, valid syntax), uploaded, and launched at 06:32:05Z.
- Every eval passed `--revision` explicitly, and `screen.py` asserted `experiment.model` = config hub + revision on every cell.
- Run times: 0.6B 06:32–07:26 (10 cells), 1.7B 07:26–08:17 (12 cells), 8B 08:17–09:46 (12 cells). All rc=0. Pulled incrementally, checksum-verified, pod deleted (`not_found`, 0 pods). **e04 spend so far: $2.20.**

| size | no cue | ` Alright,` | ` To determine` | forwarded (lower bound < +0.05) |
|---|---|---|---|---|
| 0.6B | 0.281 | 0.430 | 0.407 | ` Okay,` (+1.3 [−2.1, +4.6]), ` \n\nOkay` (+6.4 [+2.5, +10.2]) |
| 1.7B | 0.434 | 0.606 | 0.579 | ` \n\nOkay` (+8.7 [+4.3, +13.0]) |
| 8B | 0.505 | 0.775 | 0.690 | none |

- Per-size tables are in `results/screen_<size>.json`.
- **Descriptive:** ` Alright,`'s pass@1 rises with size (0.43 → 0.61 → 0.74 (4B, e03) → 0.78), while its opening probability falls (0.070 → 0.0057 → 0.0019 → 0.0003). This holds within 0.6B–8B only: the 14B, not tested here, has 0.040 (e02), so the probability is U-shaped across the family.
- **The user approved the confirm stage** for the 0.6B and 1.7B (projected about $1.50, total about $3.70, under the $5 cap).

## Stage 3: confirm (2026-10-22, 11:08–13:11Z)
- `analysis/final.py` was tested before any GPU spend on synthetic confirm data: a planted tie came out "NOT below", forwarded controls were judged on confirm data and the rest on screen data, and the 8B (nothing forwarded) path worked.
- `stage3.sh` = `run.sh`'s header, `cfg` and confirm section, built with an `awk` filter verified locally (no stage-1 or screen lines, valid syntax) and uploaded as-is.
- Pod `y8i9ifjb78wzog`: 1× A40, $0.59/hr. Attended. Setup rc=0 (snapshot `env/20261022T111247Z/`). Confirm evals with explicit `--revision`: 0.6B 11:14–12:30 (3 cells × 350 problems), 1.7B 12:30–13:10 (2 cells), both rc=0. Pulled, checksum-verified, pod deleted (`not_found`, 0 pods).
- Confirm pass@1:
  - 0.6B: ` Alright,` 0.444, ` Okay,` 0.421, ` \n\nOkay` 0.388;
  - 1.7B: ` Alright,` 0.658, ` \n\nOkay` 0.546.

## Stage 4: analysis (2026-10-22, local)
- `final.py` per size: Holm within size across the 6 B–D controls, using confirm data for forwarded controls and screen data otherwise. It writes `results/summary_<size>.json` and `results/scores_{screen,confirm}_<size>.parquet`.
- **Decision for every size: row 1, specific to ` Alright,`.** The tightest margin is the 0.6B vs ` Okay,`, at +0.022 with Holm CI [+0.002, +0.043]. That's barely above zero.
- **e04 total spend: $3.43** (balance $39.75 → $36.32 after the last pod's billing settled; $3.38 at deletion), under the $5 cap.

## Correction (2026-10-22)
- The user noted that REPORT and findings overstated "the models become less likely to write the cue with size". That holds only within the tested 0.6B–8B. The 14B is much more likely to write it (0.040, rank 7; e02), consistent with its own beam search selecting it. Wording now scoped to 0.6B–8B, with the U-shape noted.
