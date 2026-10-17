# e02_cue_transfer — Do cues from a larger model transfer to a smaller sibling?

Instruction packet for an autonomous agent working in the `cueseum` monorepo.

- **Lives at:** `cueseum/experiments/e02_cue_transfer/PACKET.md`
- **Read first:** `cueseum/AGENTS.md`, then this file.
- **Scope:** this one experiment. Do not add other model pairs, prompts, temperature sweeps or new
  cue searches beyond what is listed here. Ideas that come up go in REPORT.md under "Next".

---

## 1. Background

**Paper:** Wang, Dravid et al., *Base Models Can Reason By Taking a Cue From Training Data* (2026).
PDF: https://www.sophielwang.com/cues/paper.pdf · Code: https://github.com/sophicle/cues

**Token cues.** A short string prefilled at the start of a base model's response. The paper selects
one cue per (model, prompt) with a label-free search:
1. beam search ranks openings by how likely the model is to write them; the top 20 are shortlisted,
2. each shortlisted opening is sampled on 30 probe problems,
3. the opening whose sampled answers agree most (lowest answer entropy) wins.

Each model is searched independently. The paper never tests whether one model's cue works on
another model.

**Why cues might transfer within a family.** The paper's account is that cues work because of
associations learned from training data. Models in the same family usually share most of their
training data and tokenizer, so a cue that triggers reasoning in one may trigger it in its siblings.
But the search only considers openings the model itself is *likely* to write, so a cue that works for
a smaller sibling can be missed if that sibling rarely writes it unprompted. The paper documents this
failure mode (bare `Okay` scored 74.9% on Olmo-3-7B but ranked 542nd in probability). Larger models'
searches are also a natural source of candidates: they are run anyway, and their cues are public.

**Upstream's registered cues for Qwen3 base models, boxed prompt:**

| Model | Registered cue | Paper MATH-500 pass@1 (no cue → cued, 31k budget) |
|---|---|---|
| Qwen3-14B-Base | `' Alright,'` | 72.2% → 86.6% |
| Qwen3-4B-Base | `' To determine'` | 54.9% → 71.5% |

`' Alright,'` does not appear among the 20 openings upstream's search shortlisted for Qwen3-4B (paper
App. A, Table 1).

**Prior evidence from e01.** e01 (see `experiments/e01_cue_tree/REPORT.md`) screened 24 candidate
cues on Qwen3-4B-Base, boxed prompt, including the larger sibling's registered cue. On 420 MATH-train
problems at a 4,096-token budget with 8 rollouts each, `' Alright,'` scored 0.834 pass@1 vs 0.786 for
`' To determine'` and 0.616 with no cue, and was the best single cue. e01 labeled this exploratory: it
was the best of 24 on the same problems, at a non-standard budget. `' Alright,'` produced solutions
about 2.3× longer and hit the 4k cap 5× as often. **e02 is the confirmatory test.**

## 2. Hypotheses

Pre-registered. **H1 is the only confirmatory test.** H2–H4 are supporting analyses that explain the
result; report them, but do not frame them as confirmed or rejected with the same weight as H1.

**H1 (transfer).** On MATH-500, boxed prompt, upstream's full settings (31,744 tokens, temperature
0.6), the larger sibling's cue `' Alright,'` gives higher pass@1 on Qwen3-4B-Base than the cue
upstream selected for it, `' To determine'`.
- Test: paired difference in per-problem pass@1 (`' Alright,'` minus `' To determine'`), bootstrap 95% CI
  over problems (10,000 resamples), two-sided, α = 0.05.
- **Supported** if the CI excludes zero and the difference is positive.
- **Practically meaningful** if the point estimate is ≥ 2 points.
- **Rejected** if the CI includes zero or the difference is negative.

**H2 (budget robustness).** `' Alright,'`'s advantage holds when the same responses are truncated to
4k, 8k and 16k tokens and rescored, i.e. it doesn't come only from using a longer budget better.

**H3 (where the search fails).** When `' Alright,'` is added to upstream's 20 shortlisted openings for
Qwen3-4B, upstream's answer-agreement rule selects it.
- If yes: the search failed only at *proposing* candidates, so adding a sibling's cues to the
  shortlist fixes it.
- If no: the agreement rule also misranks a cue it can see.

**H4 (why it wasn't proposed).** `' Alright,'` has low probability as Qwen3-4B's opening (averaged
over the beam's probe problems), ranking it outside the top 20 openings, while it ranks at or near
the top for Qwen3-14B. Purely descriptive.

## 3. Setup

The repo, environment and shared library exist from e01. Do not re-bootstrap.

- Upstream is pinned via the cueseum fork `owayys/cues@339de49` (upstream `cd9caab` + `enforce_eager=False`).
  Do not change the pin. Record it in every results file.
- Reuse `src/cueseum/` (`rollouts`, `stats`, `cuesets`, `plots`, `paths`). Anything new that e03 is
  likely to reuse (the cue-probability measurement in Phase 3, the truncate-and-rescore helper in
  Phase 5) goes in `src/cueseum/` with tests; everything else stays in the experiment folder.
- GPU: rent as in e01 (RunPod), with the same checksum-then-delete routine for outputs.

```
experiments/e02_cue_transfer/
  PACKET.md  config.yaml  data/  scripts/run.sh  analysis/  results/  LOG.md  REPORT.md
```

## 4. Fixed settings (write into `config.yaml`)

| Setting | Value |
|---|---|
| Target model | `qwen4b` (Qwen/Qwen3-4B-Base, rev `906bfd4b…`) |
| Source model (H4 only) | `qwen14b` (Qwen/Qwen3-14B-Base, rev `0b0bd373…`) |
| Prompt | `boxed` |
| Benchmark | `math500` (upstream `data/problems/math500.jsonl`, 500 problems) |
| Cues (Phase 2) | `none`, `' To determine'`, `' Alright,'` (exact strings, leading space included) |
| Temperature / top-p | 0.6 / 0.95 |
| Rollouts | 32 per (cue, problem): two batches of 16 (`--rollout-index-offset 16 --suffix _b2`), as upstream's `eval_grid.sh` |
| Token budget | `--max-new-tokens 31744` |
| Seed | `20260819` |
| Runs root | `$CUESEUM_RUNS/e02_cue_transfer/` |
| Budget cap | **$25 total** or 35 GPU-hours, whichever comes first. Stop and ask beyond it. |

## 5. Phases

Log each phase in `LOG.md`: start/end, GPU-hours, dollars, deviations.

### Phase 0 — Smoke test
Run `none` and `' Alright,'` on 5 MATH-500 problems, 2 rollouts, 2,048 tokens. Confirm the cue appears
at the head of each stored completion and that `cueseum.rollouts.load_cells` reads the output.

### Phase 1 — Pilot (required)
All three cues, first 50 MATH-500 problems, 4 rollouts, full 31,744 budget.
```
python -m cues eval --model qwen4b --prompt boxed --benchmark math500 \
  --cues none $' To determine' $' Alright,' \
  --problem-count 50 --n-rollouts 4 --max-new-tokens 31744 \
  --out $CUESEUM_RUNS/e02_cue_transfer/pilot
```
Report: GPU-hours and dollars, projected cost of Phase 2, mean output tokens and cap rate per cue,
extraction-error rate.

**Stop conditions:**
- projected Phases 2–4 cost > $25 → stop and propose reducing to 16 rollouts per cue,
- any cue's cap rate > 10% at 31,744 → stop and report (it would make H1 a budget comparison),
- extraction/grading errors > 2% → stop and report.

### Phase 2 — Main run (H1, H2)
Full MATH-500, three cues, 32 rollouts in two batches of 16:
```
python -m cues eval --model qwen4b --prompt boxed --benchmark math500 \
  --cues none $' To determine' $' Alright,' \
  --n-rollouts 16 --max-new-tokens 31744 --out $CUESEUM_RUNS/e02_cue_transfer/main
python -m cues eval ... --rollout-index-offset 16 --suffix _b2      # same args otherwise
```
Verify every (cue, problem) has rollout indices 0–31 before analysis.

**Setup sanity check (before reading H1).** Compare no-cue and `' To determine'` pass@1 with the paper
(54.9%, 71.5%). If either differs by more than 3 points, stop and investigate before analyzing H1
(prompt rendering, stop strings, grader, the fork's `enforce_eager` change). Log the comparison
either way.

### Phase 3 — Cue probability (H4)
Measure, for each of `' Alright,'`, `' To determine'`, `' To'`, and the top 5 beam openings:
- the mean probability of the full cue string as the model's opening, over the 100 probe problems
  (`third_party/cues/data/problems/math_train_probe.jsonl[0:100]`), boxed prompt,
- its rank among all openings of the same token length at that position (rank among first tokens for
  the first token; rank of the second token given the first).

For both `qwen4b` and `qwen14b`. Compute with a forward pass over prompt + cue (sum of the cue tokens'
log-probs), not with the beam, which only lists openings it kept. Cross-check: for openings that the
beam did list, your numbers should match upstream's `mean_prob_mass` within rounding.
Put the measurement function in `src/cueseum/cueprob.py` with a test.

Also report whether `' Alright,'` would have passed upstream's beam filters
(`--min-problem-fraction 0.5`, beam width 40, top-first 12, top-second 4; see `cues/beam.py`): which
filter, if any, removed it.

### Phase 4 — Search with the sibling cue added (H3)
1. `python -m cues search --model qwen4b --prompt boxed --beam-only --out $CUESEUM_RUNS/e02_cue_transfer/search`
2. Add `' Alright,'` to the written `nominees.json` (same `{slug: opening}` format; slug via
   `cues.models.cue_slug`). Log the file before and after.
3. Rerun the same `search` command without `--beam-only`. It skips the existing beam and nominee steps
   and runs the screen (21 openings + no cue, 30 probe problems × 16 rollouts, 16,384 tokens) and the
   decider.
4. Record `winner.json`, and `' Alright,'`'s entropy rank and accuracy rank among the 21 openings.
   Also check that the shortlist without `' Alright,'` still selects `' To determine'`, as upstream
   reports.

### Phase 5 — Analysis
Score table via `cueseum.rollouts.load_cells`; save as `results/scores.parquet`.

**H1 (confirmatory).** Per-problem pass@1 = mean over 32 rollouts. Paired difference, bootstrap CI as
in §2. Also report each cue's pass@1 with CI and the no-cue baseline. State the H1 outcome in one line.

**H2.** For each completion, re-tokenize with the model's tokenizer, truncate the generated part at
B ∈ {4096, 8192, 16384, 31744} tokens (cue tokens count toward B), rescore with upstream's grader.
Report pass@1 per cue per B and the paired `' Alright,'` − `' To determine'` difference with CI at each B.
Plot pass@1 against B. Put the truncate-and-rescore helper in `src/cueseum/`.

**H3.** From Phase 4: winner, `' Alright,'`'s entropy and accuracy ranks, and the agreement between the
entropy ranking and the accuracy ranking across the 21 openings (Spearman ρ).

**H4.** Table from Phase 3, and which beam filter excluded `' Alright,'`.

**Secondary descriptives (not hypothesis tests):**
- per-subject and per-level paired differences on MATH-500 (no significance claims; e01 found no
  group structure, so treat as descriptive),
- mean output tokens and cap rate per cue,
- the share of `' Alright,'` responses containing checking phrases (`let me check`, `double-check`,
  `verify`, `wait`) vs `' To determine'`, to describe the style difference.

## 6. Interpreting the outcome (state which row applies in REPORT.md)

| H1 | H3 | Conclusion |
|---|---|---|
| Supported | Selected | The search works but proposes too few candidates. Adding sibling models' cues to the shortlist is a cheap fix worth testing across families (candidate for e03). |
| Supported | Not selected | Answer agreement misranks a better cue it can see. The selection rule, not only the proposal step, is a limitation of the method. |
| Rejected | Either | e01's result was specific to its budget or problems. Upstream's registered cue stands for Qwen3-4B; report H2 to show whether the budget explains it. |

Whatever the outcome, state clearly that this is **one model pair, one prompt, one benchmark**, so
it shows transfer can happen, not that it generally does.

## 7. Deliverables

1. `REPORT.md`: question, setup, H1 result (one table: three cues' pass@1 with CIs and the paired
   difference), H2 plot and table, H3 and H4 results, the §6 row that applies, limitations, cost.
2. `results/`: `summary.json` (headline numbers + provenance per AGENTS.md), `scores.parquet`,
   figures, `cue_probabilities.json`, `search_winner.json`.
3. `LOG.md`, `scripts/run.sh` reproducing Phases 1–5 from cached outputs.
4. New library code (`cueprob`, truncate-and-rescore) with passing tests.
5. README index row and a paragraph in `docs/findings.md`.

## 8. Known caveats to mention in the report

- One family (Qwen3), one direction (14B → 4B), one prompt (boxed), math only, temperature 0.6.
- The paired comparison is between two specific cues; it doesn't show `' Alright,'` is the best cue
  for Qwen3-4B, only that it beats the registered one.
- MATH-500 is a standard benchmark both models may have seen in some form during training; this
  affects both cues equally but limits generality.
- The rollouts come from the fork with CUDA graphs enabled, so they are not token-identical to
  upstream's; the sampling distribution is the same.
