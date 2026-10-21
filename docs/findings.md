# Findings

## e01: cue tree (not supported)
For Qwen3-4B-Base on 420 MATH-train problems (24 cues × 8 rollouts, 4k tokens), one global cue, ` Alright,` (0.834 vs 0.616 with no cue and 0.786 with upstream's registered ` To determine`), beat cue selection per subject, level, subject × level and problem on held-out problems. The paired gains vs global were −0.004, −0.001, −0.036 and −0.104. Named groups did no better than random groups of the same sizes (p = 0.34, 0.07, 0.46), and selecting cues by answer agreement instead of accuracy gave the same picture. Clustering problems by their cue profiles matched neither subject, level nor answer type (ARI ≤ 0.014), and the clusters were unstable across rollout halves (ARI ≈ 0.11). ` Alright,` was never nominated by upstream's beam for this model, which is a small instance of discovery missing a lower-probability winning cue. Cost: $3.65. [Report](../experiments/e01_cue_tree/REPORT.md).

## e03: cue controls (specific to ` Alright,`)
On Qwen3-4B-Base (100 fresh MATH-500 problems, 8 rollouts, 4k tokens), Qwen3-14B's cue ` Alright,` (pass@1 0.744) beat every rule-selected control after Holm correction:
- other models' registered cues: ` \n\nOkay` 0.640, ` \n\n` 0.522;
- the opener the 4B's post-trained thinking model always uses, ` Okay,` (0.580);
- three openers with the same opening probability as ` Alright` (0.37–0.43, below no cue's 0.500).

The closest control trailed by 10.4 points (Holm lower bound +4.9). ` Alright,` also beat the 4B's registered ` To determine` by +6.0 [+1.8, +10.3], replicating e01 and the e02 pilot on fresh problems. So the advantage isn't a generic reasoning-style, any-model-cue or rare-opener effect. It is specific to this cue on this model.

This is screen-only evidence, since no control came close enough to need the confirm stage. At 4k, ` Alright,` loses the most rollouts to the cap (13.5%), which biases against it. Cost: $0.69. [Report](../experiments/e03_cue_controls/REPORT.md).
