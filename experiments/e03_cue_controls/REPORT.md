# e03: Is ` Alright,` specifically good for Qwen3-4B, or are similar openers equally good?

**Decision (§6, row 1): specific to ` Alright,`.** On fresh MATH-500 problems it beats every control: other models'
cues (B), the reasoning-style opener of the 4B's own post-trained sibling (C), and openers of the same opening
probability (D). All six comparisons hold after Holm correction. The evidence is **screen-only (100 problems)**: no control
came within the forwarding margin, so the confirm stage was skipped by the pre-registered rule.

## Question
e01 and the e02 pilot found that ` Alright,` (Qwen3-14B's cue) beats Qwen3-4B's registered cue. Feedback asked whether
that is about this cue, or whether any conversational, reasoning-style or rare opener would do as well. Each control
group targets one of those explanations, and every cue was chosen by a rule fixed before running (PACKET.md).

## Setup
- **Model and sampling:** Qwen3-4B-Base @ `906bfd4b`, boxed prompt, temperature 0.6, top-p 0.95, 8 rollouts, 4,096 tokens,
  seed 20260819 + rollout index.
- **Grading and code:** upstream math-verify grader, via the fork `owayys/cues@339de49`.
- **Problems:** 100 MATH-500 problems (screen split). The first 50 were excluded because e02's pilot used them; the rest
  were shuffled with seed 0.
- **How the control cues were derived:**
  - **C:** post-trained Qwen3-4B (thinking mode) opened 400/400 sampled reasoning traces with "Okay,", so the rule gives one cue.
  - **D:** a seeded draw from the 23 first tokens with mean opening probability within 0.5–2× of ` Alright` (0.00185,
    rank 43 for the 4B).
- **Cost:** $0.69 in total. Attended runs, one pod at a time, with the pod count checked after every step.

## Results
pass@1 with 95% bootstrap CIs over problems:

| cue | group | pass@1 [95% CI] | cap rate | no answer | mean tokens |
|---|---|---|---|---|---|
| ` Alright,` | A target | **0.744** [0.672, 0.810] | 13.5% | 13.1% | 1,613 |
| ` To determine` | E reference (4B's registered cue) | 0.684 [0.613, 0.752] | 2.1% | 2.9% | 657 |
| ` \n\nOkay` | B (Olmo-3-7B's cue) | 0.640 [0.568, 0.709] | 9.6% | 10.0% | 1,092 |
| ` To` | E reference (RL-favored branch) | 0.603 [0.529, 0.672] | 2.9% | 5.0% | 600 |
| ` Okay,` | C reasoning-style | 0.580 [0.511, 0.646] | 8.9% | 11.3% | 1,010 |
| ` \n\n` | B (Olmo-3-32B's cue) | 0.522 [0.446, 0.596] | 3.0% | 4.0% | 561 |
| no cue | E reference | 0.500 [0.426, 0.574] | 4.1% | 5.9% | 553 |
| ` It` | D probability-matched | 0.426 [0.359, 0.495] | 4.5% | 8.3% | 506 |
| ` Every` | D probability-matched | 0.372 [0.304, 0.441] | 5.2% | 8.6% | 540 |
| ` Each` | D probability-matched | 0.372 [0.309, 0.436] | 5.4% | 9.3% | 552 |

**Primary test** (paired per problem, 10,000 bootstrap resamples, Holm across the 6 family controls):

| control | ` Alright,` − control | Holm-adjusted CI | below? |
|---|---|---|---|
| ` \n\nOkay` | +0.104 | [+0.049, +0.158] (99.2%) | yes |
| ` Okay,` | +0.164 | [+0.104, +0.223] (98.8%) | yes |
| ` \n\n` | +0.221 | [+0.150, +0.294] (99.0%) | yes |
| ` It` | +0.318 | [+0.261, +0.374] (95.0%) | yes |
| ` Every` | +0.371 | [+0.293, +0.449] (98.3%) | yes |
| ` Each` | +0.371 | [+0.300, +0.439] (97.5%) | yes |

All six bootstrap p-values are at the floor (p < 0.0001), so Holm's ordering among them is a tie. It happened to give
` \n\nOkay`, the closest control, the strictest level, which is the conservative assignment.

**Reference comparisons** (outside the test family): ` Alright,` beats the 4B's registered ` To determine` by +0.060
[+0.018, +0.103]. That replicates e01's +0.047 and the e02 pilot's +0.100 on fresh problems. It also beats no cue by
+0.244 [+0.186, +0.300].

## Interpretation
- **Not just reasoning style.** ` Okay,` is what the 4B's own reasoning-trained sibling always opens with, yet it is
  16 points worse.
- **Not "any model's cue".** Olmo's registered cues are 10–22 points worse.
- **Not "rare openers help".** Openers exactly as unlikely as ` Alright` score **below no cue**, so low probability alone
  hurts if anything.
- **What's left:** something specific to ` Alright,` on this model, consistent with transfer of the sibling's cue.
  This shows *that* the cue is special here, not *why*.

## Limitations
- **Screen-only evidence:** 100 problems. Gaps smaller than about 10 points wouldn't have been resolved at this size.
  The closest control was 10.4 points behind, with Holm lower bound +4.9.
- **The 4k budget works against ` Alright,`.** It has the most capped rollouts (13.5%) and no-answers (13.1%), because its
  solutions are longest, and capped responses count as wrong. So its lead is if anything understated, but rankings at
  31k could differ. The packet's case for 4k (e02's pilot) looks weaker on these problems than it did there.
- **Group C has 1 cue, not 3,** because the post-trained model used a single opening.
- **Group D cues are single tokens.** ` Alright,` is two.
- **Scope:** one model, one prompt, math only, temperature 0.6. MATH-500 may be in both models' training data, which
  affects all cues alike.

## Next
- **Confirm the gap at 31k** on the 4B, for ` Alright,` vs ` To determine` (e02's H1). This is still the confirmatory test of transfer.
- **Cross-model cue matrix:** each Qwen3 size with every other size's cue, to see whether transfer is general within the family.
- **Mechanism:** what ` Alright,` changes in the 4B's reasoning. e02's pilot found checking phrases in 68% of responses, against 4%.

## Cost
$0.69: stage 1 $0.06 (A40), stage 2 $0.63 (A40, 1.0 h). Stage 3 was skipped by rule.
