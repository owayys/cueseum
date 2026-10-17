# e01: Do optimal token cues form a tree over problem groups?

**Decision: Not supported** (§6, computed by `analysis/analyze.py` on all 420 problems). One global cue beats per-group and per-problem cue selection on held-out problems at every level, and named groups do no better than random groups.

## Question
Does the best opening cue for Qwen3-4B-Base differ between groups of related MATH problems (subject → subject × level → problem), so that choosing a cue per group generalizes better than one global cue (H1)? H2 (child cues extend parent cues as token prefixes) was optional and only applies if H1 holds, so it was not run.

## Setup
- **Model and sampling:** Qwen/Qwen3-4B-Base @ `906bfd4b`, `boxed` prompt, temperature 0.6, top-p 0.95, 4,096 new tokens, seed 20260819 (rollout r uses seed + r). Grader: upstream math-verify.
- **Inference code:** upstream `sophicle/cues` via the fork `owayys/cues@339de49`, which is `cd9caab` plus a one-line change, `enforce_eager=False` (CUDA graphs on). Sampling is unchanged.
- **Problems:** 420 MATH-train problems, 12 per subject × level cell (7 × 5), seed 0. The 300 beam-probe problems were excluded. No overlap with MATH-500.
- **Cues:** 23 cues plus no-cue. The 20 come from upstream's beam over the model's likely openings, plus ` Okay,`, ` Alright,` and ` \n\nOkay` (` Let's` and ` First,` were already nominees). None merges with the prompt's final token.
- **Rollouts:** 8 per (cue, problem), 80,640 in total, all complete. Cap rate 3.1% overall, highest for ` Alright,` (7.5%). No-answer rate 2.1–7.6% per cue.
- **Compute:** one RTX PRO 4500 (32 GB) on RunPod, about 5.0 pod-hours, **$3.65**. The analysis ran locally on CPU.
- The analyses below are the ones pre-registered in PACKET §5a–5f. Their definitions were fixed in LOG.md before any full-run results were read.

## Per-cue accuracy (all 8 rollouts, all problems, descriptive)
| cue | accuracy | no answer | cap | mean tokens |
|---|---|---|---|---|
| ` Alright,` | **0.834** | 0.075 | 0.075 | 1,340 |
| ` To determine` (upstream's registered cue) | 0.786 | 0.021 | 0.015 | 573 |
| ` To solve` | 0.725 | 0.033 | 0.017 | 547 |
| ` To` | 0.707 | 0.030 | 0.014 | 489 |
| ` \n\nOkay` | 0.704 | 0.063 | 0.050 | 800 |
| no cue | 0.616 | 0.052 | 0.027 | 458 |
| ` Let $` (lowest) | 0.529 | 0.047 | 0.040 | 440 |

## Held-out accuracy by grouping level (5b, 5c)
2-fold CV within groups, 50 repeats. The gain is paired per problem against a global cue CV'd on the same problems with the same seed. 95% bootstrap CIs over problems (2,000 resamples). p is one-sided, against 200 random groupings of matched sizes. Cues are selected by accuracy.

| level | groups | held-out acc [95% CI] | gain vs global [95% CI] | null mean | p |
|---|---|---|---|---|---|
| global | 1 | 0.834 [0.803, 0.865] | — | — | — |
| subject | 7 | 0.829 [0.799, 0.861] | −0.004 [−0.008, −0.001] | 0.829 | 0.34 |
| level | 5 | 0.832 [0.802, 0.864] | −0.001 [−0.002, −0.001] | 0.831 | 0.07 |
| subject × level | 35 | 0.798 [0.768, 0.828] | −0.036 [−0.046, −0.027] | 0.797 | 0.46 |

On the 408 informative problems the pattern is the same: gains −0.004, −0.002 and −0.036; p = 0.31, 0.25 and 0.41. The H1 signature (accuracy rising from global to subject or level) is absent. Every finer grouping loses a little, and the losses grow as groups shrink.

## Per-problem variation (5a, rollout split)
Cue chosen per problem on rollouts 0–3 and scored on rollouts 4–7, against one global cue chosen on 0–3. The global cue is ` Alright,`.

| | all (420) | informative (408) |
|---|---|---|
| per-problem cue, held-out | 0.729 [0.696, 0.762] | 0.741 [0.710, 0.771] |
| global cue, held-out | 0.833 [0.802, 0.865] | 0.847 [0.819, 0.876] |
| difference | **−0.104 [−0.127, −0.080]** | −0.107 [−0.131, −0.084] |
| *in-sample* difference (selected and scored on 0–3; biased, for reference only) | +0.080 [0.062, 0.098] | +0.082 [0.065, 0.100] |

On 86% of problems the best cue on rollouts 0–3 is tied with at least one other cue, and ties go to the earliest cue in the fixed order. Per-problem selection from 4 rollouts recovers noise rather than a real per-problem preference. The +8-point in-sample gain becomes a −10-point held-out loss.

## Data-driven tree (5d)
- **Clustering:** 408 informative problems were clustered on their cue profiles (accuracy minus the problem's mean, average linkage, correlation distance; `results/dendrogram.png`). No profile was constant.
- **Agreement with labels:** the k = 5 and k = 7 clusters show essentially no agreement with subject (ARI 0.003, NMI 0.045–0.056), level (ARI 0.006) or answer type (ARI 0.002–0.014).
- **Stability:** clusterings built from rollouts 0–3 and from rollouts 4–7 agree with ARI 0.107 (k = 5) and 0.113 (k = 7), on 389 problems non-constant in both halves.
- **Conclusion:** the profiles are too noisy at 8 rollouts to support a learned tree.

## Label-free variant (5e)
Cues are selected by lowest mean answer entropy (upstream's agreement criterion, with the no-answer guard at +0.10 against no-cue) and scored by accuracy.
- The global choice is again ` Alright,`.
- **5a:** per-problem selection loses 0.094 [−0.119, −0.071] held-out (in-sample gain +0.028).
- **5b/5c:** subject −0.002 (p = 0.89), level −0.008 (p = 1.0), subject × level −0.043 (p = 1.0).
- Answer agreement picks the same global cue that accuracy does. It never finds a better per-group cue.

## Descriptive (5f)
- The winning cue (all 8 rollouts) is ` Alright,` overall, in all 7 subjects, in all 5 levels, and in 30 of 35 subject × level cells. The other five are ` To determine` (3), ` To solve` (1) and ` \n` (1).
- The winner differs from its parent for 0% of subjects, 0% of levels and 14% of subject × level cells.
- Heatmaps of rollouts 4–7 accuracy by subject and by subject × level are in `results/heatmap_*.png`, with the numbers in matching `.csv` files.

## Limitations
- One model (Qwen3-4B-Base), one prompt, math only, temperature 0.6.
- **4,096-token budget.** ` Alright,` writes about 2.3× longer solutions than ` To determine` and hits the cap 5× as often, so cue rankings at a 31k budget may differ.
- Per-problem estimates from 8 rollouts are noisy (about ±15–20 points), so the 5a and 5d nulls are weak evidence against per-problem structure. They are strong evidence only against *finding* that structure with 4–8 rollouts.
- Only the model's likely openings plus 3 extras were screened. A low-probability cue that wins for some group could not be found.
- Upstream's README and the paper disagree on the probe count (100 vs 30). We used upstream's code as-is, with 100 beam problems.
- Inference used CUDA graphs (the fork), so rollouts are not token-identical to upstream's eager-mode sampling. The sampling distribution is the same.

## Exploratory (not pre-registered)
- **Why upstream registered ` To determine`, not ` Alright,`, for this model.** ` Alright,` is not among the 31 openings upstream's beam produced for Qwen3-4B. The beam keeps openings in the top-k at the answer boundary on at least half of the probe problems, so the cue was never screened. It is upstream's registered cue for Qwen3-14B, where the beam does find it. ` To determine` ranked only 17th by beam mass but won upstream's entropy screen among the nominees. Our label-free selection (5e) over all 24 cues picks ` Alright,`, so upstream's criterion would probably have chosen it had it been nominated. This was not verified on upstream's own screen (30 problems, 16 rollouts, 16k tokens). It is a mild instance of the known failure mode above: +4.8 points over the registered cue at 4k.

## Total GPU-hours
About 5.0 pod-hours (4.7 of active GPU work: setup 0.13, smoke test 0.1, beam 0.03, pilot 0.51, full run 4.09). $3.65 total, against a $20 budget and the packet's 40 GPU-hour cap. Phase 6 was not triggered.
