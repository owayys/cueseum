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
