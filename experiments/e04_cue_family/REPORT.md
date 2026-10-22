# e04: Is ` Alright,` a good cue across the Qwen3 base family?

**Decision (§6): row 1 at every size.** On Qwen3-0.6B, 1.7B and 8B Base, as on the 4B in e03, ` Alright,` (Qwen3-14B's cue)
beats every rule-selected control after Holm correction within each size:
- other models' cues;
- that size's own reasoning-model opener ` Okay,`;
- openers of matched opening probability.

The narrowest margin is at 0.6B vs ` Okay,`: +2.2 points, with a Holm lower bound of only +0.2.

## Setup
- **Models:** Qwen3-{0.6B,1.7B,8B}-Base at pinned revisions. `--revision` was passed explicitly and asserted in every rollout record.
- **Prompt and sampling:** boxed prompt, temperature 0.6, top-p 0.95, 8 rollouts, 4,096 tokens. Fork `owayys/cues@339de49`.
- **Problems:** the same splits as e03 (screen 100, confirm 350), so the 4B is directly comparable.
- **Controls:** derived per size by e03's rules.
  - **C:** every size's post-trained model opened 400/400 reasoning traces with "Okay,".
  - **D:** seeded draws from tokens within 0.5–2× of ` Alright`'s first-token probability for that size.
- **Confirm stage:** run where the screen forwarded controls. The 0.6B forwarded ` Okay,` and ` \n\nOkay`; the 1.7B forwarded ` \n\nOkay`.
- **Cost:** $3.43, attended, one pod per stage.

## Results
**Screen pass@1** (100 problems; the 4B row is e03's):

| size | no cue | ` Alright,` | ` To determine` (4B's cue) | ` Okay,` (C) | ` \n\nOkay` (B) | D controls | ` Alright` first-token prob (rank) |
|---|---|---|---|---|---|---|---|
| 0.6B | 0.281 | **0.430** | 0.407 | 0.417 | 0.366 | 0.20–0.24 | 0.070 (4) |
| 1.7B | 0.434 | **0.606** | 0.579 | 0.496 | 0.519 | 0.27–0.35 | 0.0057 (19) |
| 4B (e03) | 0.500 | **0.744** | 0.684 | 0.580 | 0.640 | 0.37–0.43 | 0.0019 (43) |
| 8B | 0.505 | **0.775** | 0.690 | 0.606 | 0.626 | 0.31–0.44 | 0.0003 (120) |

**Confirm pass@1** (350 fresh problems):
- 0.6B: ` Alright,` 0.444, ` Okay,` 0.421, ` \n\nOkay` 0.388.
- 1.7B: ` Alright,` 0.658, ` \n\nOkay` 0.546.

**Primary test:** ` Alright,` minus each control, Holm-adjusted CI within size. Every comparison is "below"; the smallest margins are:

| size | closest control | data | difference [Holm CI] |
|---|---|---|---|
| 0.6B | ` Okay,` | confirm | +0.022 [+0.002, +0.043] |
| 0.6B | ` \n\nOkay` | confirm | +0.056 [+0.027, +0.084] |
| 1.7B | ` Okay,` | screen | +0.110 [+0.059, +0.163] |
| 1.7B | ` \n\nOkay` | confirm | +0.112 [+0.080, +0.144] |
| 8B | ` \n\nOkay` | screen | +0.149 [+0.081, +0.214] |

Full tables are in `results/summary_<size>.json`.

## Interpretation
- **` Alright,` is a family-wide cue for these Qwen3 base models.** At every size it beats the reasoning-style, other-model and
  probability-matched controls, and in the screen it beats the 4B's registered ` To determine` by 2–9 points (outside the test family).
- **Specificity grows with size.** Its margin over the closest control widens from +2 points at 0.6B to +11 at 1.7B and +15 at 8B
  (+10 at the 4B in e03).
- **Its absolute benefit grows while the models become less likely to write it** (descriptive, four sizes). The 8B almost never
  starts with "Alright" (rank 120) yet gains the most (0.505 → 0.775). Its no-cue baseline barely moves from the 4B (0.500 → 0.505).
  So how *natural* a cue is to a model does not predict how much it helps.
- **What's tested:** what differs between "Alright," and "Okay," is not tested. Every reasoning-trained Qwen3 size uses "Okay,".

## Limitations
- Screen-only evidence (100 problems) for every non-forwarded control.
- 4k budget. In e03 it biased against ` Alright,` (the most capped).
- One prompt, math only, temperature 0.6.
- No 14B (dropped on cost), so the "own cue" reference point is missing.
- Group D's meaning varies by size. At 0.6B its controls are common openers (` We`, ` The`, ` Since`), because ` Alright` is common for that model.
- ` Re` (8B) is a word fragment.
- Four sizes describe a trend; they can't test one.

## Next
- Confirm at 31k (e02's H1 for the 4B, and the same here).
- The 14B, to anchor the own-cue comparison.
- Mechanism: why "Alright," helps more than "Okay," in base models.

## Cost
$3.43: stage 1 $0.17, screen $2.03, confirm $1.23 (including $0.05 that settled after deletion).
