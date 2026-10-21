# e03_cue_controls — Is ` Alright,` specifically good for Qwen3-4B, or are similar openers equally good?

Instruction packet for an agent working in the `cueseum` monorepo. Drafted on 2026-10-21 by the agent at the user's request,
from e01, the e02 pilot and external feedback. **Needs the user's (and the supervisor's) approval before any GPU spend.**

- **Read first:** `AGENTS.md`, then this file.
- **Scope:** this experiment only. Other model pairs, budgets, a cross-model cue matrix and mechanistic work go in
  REPORT.md under "Next".

## 1. Background
- On Qwen3-4B-Base (boxed prompt), the sibling Qwen3-14B's cue ` Alright,` beat the 4B's registered cue ` To determine`:
  - e01 (420 MATH-train problems, 4k tokens, 8 rollouts): +4.7 points [2.9, 6.6]. Exploratory: best of 24 cues.
  - e02 pilot (50 MATH-500 problems, 31,744 tokens, 4 rollouts): +10.0 [4.0, 16.5]. Not confirmatory.
- **Why the 4B's search never proposed it** (e02 H4): ` Alright` is about the 49th most likely first token for the 4B, and
  upstream's beam keeps the top 12.
- **The open question** (raised in feedback): is this specific to ` Alright,`, or would any similar opener do? e01 tested
  only two other conversational openers (` Okay,`, ` \n\nOkay`). Both scored 13–16 points lower, but at a non-standard
  budget, on the same problems the ranking came from, and with no probability-matched controls.

## 2. Hypotheses (pre-registered)
**H (primary):** on fresh MATH-500 problems, ` Alright,` scores higher than every control opener in groups B–D on
Qwen3-4B-Base. The test is the paired per-problem difference (` Alright,` minus the control), as described in §6.

Each group tests one alternative explanation:

| Group | Cues | Source (the selection rule) | Alternative explanation tested |
|---|---|---|---|
| A target | ` Alright,` | Qwen3-14B's registered cue | — |
| B other-model cues | ` \n\nOkay`, ` \n\n` | upstream registry: the boxed-prompt cues of Olmo-3-7B and Olmo-3-32B | any model's selected cue transfers, not specifically a sibling's |
| C reasoning-style | the top 3 openings of post-trained Qwen3-4B (thinking mode), derived in Phase 1 | measured | the effect is a reasoning *style*, not this specific cue |
| D probability-matched | 3 openers drawn at random from the 4B's first tokens with probability in the same band as ` Alright`, derived in Phase 1 | `cueseum.cueprob`, fixed seed | rare (low-probability) openers help in general |
| E reference | ` To determine`, ` To`, no cue | the 4B's registered cue; the branch RL favors on the 4B (paper App. D) | — (context, not in the H family) |

## 3. Fixed settings (`config.yaml`)
- **Model:** Qwen3-4B-Base @ `906bfd4b`, boxed prompt.
- **Sampling:** temperature 0.6, top-p 0.95, 8 rollouts, 4,096 new tokens, seed 20260819 (rollout r uses seed + r).
- **Grader:** upstream math-verify.
- **Upstream code:** the fork pin `owayys/cues@339de49`.
- **Why 4k tokens:** in the e02 pilot, truncating to 4k left every cue's pass@1 unchanged. This is stated as a limitation.
- **Problems:** MATH-500 minus the first 50 (used in e02's pilot), shuffled with seed 0.
  - **screen** = the first 100 of the shuffled set;
  - **confirm** = the next 350, never used in the screen.
- **Budget:** **$8** or 10 GPU-hours, whichever comes first. Stop and ask beyond it.
- **Runs are attended only:**
  - one pod at a time;
  - after each step, verify that `runpodctl pod list --all` shows exactly the expected pods;
  - no unattended create loops (see e02 LOG, the 2026-10-19 incident).

## 4. Phases
### Phase 1 — Derive groups C and D (forward passes and short samples, ~$0.5)
**Group C:**
- sample post-trained Qwen3-4B (thinking mode, chat template) on the 100 probe problems: 4 samples each, 12 new tokens, at the config's temperature and top-p;
- take the first word of the reasoning trace (after `<think>\n`), including trailing punctuation;
- the cue is `" " + word`;
- the top 3 by frequency become group C, excluding any cue already in groups A, B or E.

**Group D:**
- with `cueprob`, compute the 4B base's mean first-token probability over the same 100 probe problems;
- candidates are tokens with a leading space, alphabetic, and with mean probability in [0.5×, 2×] that of ` Alright`;
- exclude the words in `config.probability_matched.exclude_words`;
- draw 3 with `random.Random(0)`.

**Record:** both lists, with counts and probabilities, in `data/cues.json` and LOG.md before Phase 2 starts.

### Phase 2 — Screen (~$1)
- **What runs:** all cues (A–E) on the 100 screen problems.
- **Forwarding rule:** a control in B–D is **forwarded** if the lower bound of its 95% bootstrap CI for (` Alright,` − control) is below +0.05. That covers controls not clearly 5+ points worse, including any that score higher.
- **The rest:** controls that aren't forwarded are reported as "separated at screen" (screen-only evidence).

### Phase 3 — Confirm (~$0–2)
- **Runs only if something is forwarded:** ` Alright,` plus the forwarded controls, on the 350 confirm problems.
- **H is tested on confirm data only,** with a Holm correction across the forwarded controls.

### Phase 4 — Analysis
- **Primary:** H as specified in §6.
- **Descriptive:**
  - pass@1 per cue with CI;
  - mean tokens and cap rate per cue;
  - the screen table.

## 5. Sample size (from e01 data)
- **Spread:** the SD of per-problem paired differences between ` Alright,` and the relevant cues is 0.19–0.24.
- **At screen** (100 problems), gaps of about 10–15+ points resolve.
- **At confirm** (350 problems, Holm over about 3 forwarded controls), gaps of about 4–5 points are detectable at 80% power.
- **Below that:** smaller gaps would be reported as unresolved, not as "no difference".

## 6. Decision (state which row applies in REPORT.md)
For each control: **below** = the Holm-adjusted two-sided CI for (` Alright,` − control) excludes 0 and is positive
(confirm data, or the screen if not forwarded).

| Outcome | Conclusion |
|---|---|
| ` Alright,` is above every control in B, C and D | The effect is specific to this cue: neither style, rarity, nor "any model's cue" explains it. It supports transfer of the sibling's cue. |
| Some group C cue is not below | A reasoning-style effect: similar openers do about as well. The beam misses that style on the 4B. |
| Some group D cue is not below | A rare-opener effect: the beam's bias toward likely openings is the issue, not this cue. |
| Some group B cue is not below | Other families' cues transfer as well, so the effect isn't sibling-specific. |

Several rows can apply at once; report every one that does.

## 7. Deliverables
- `REPORT.md`: the decision rows, the screen and confirm tables, cost, limitations.
- `results/`: `summary.json` with provenance, `scores.parquet`, `cues.json`.
- `LOG.md` and `scripts/run.sh`.
- README row, and a findings paragraph.

## 8. Caveats
- One model, one prompt, math only, temperature 0.6, a 4k budget.
- Group C depends on the post-trained model's opening habits, sampled at temperature 0.6.
- Group D tokens are single tokens. ` Alright,` is two tokens (` Alright` + `,`).
- The result shows whether ` Alright,` is special *for this model*, not why. Mechanism is out of scope.
