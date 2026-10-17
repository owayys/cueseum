# e01_cue_tree — Do optimal token cues form a tree over problem groups?

Instruction packet for an autonomous agent working in the `cueseum` monorepo.

- **Lives at:** `cueseum/experiments/e01_cue_tree/PACKET.md`
- **Scope:** this one experiment, plus the one-time repo bootstrap in §3 (e01 is the first experiment,
  so the repo may not exist yet). Do not start other ablations (temperature sweeps, cue length, RL,
  SFT, step-level cues) even if they look cheap.
- **Read `cueseum/AGENTS.md` before this file.** If it doesn't exist yet, create it in §3 step 4.

---

## 1. Background

**Paper:** Wang, Dravid et al., *Base Models Can Reason By Taking a Cue From Training Data* (2026).
PDF: https://www.sophielwang.com/cues/paper.pdf · Code: https://github.com/sophicle/cues

**What a token cue is.** A short string prefilled at the start of a base model's response (e.g.
`.\n\nOkay` for Olmo-3-7B, ` Alright,` for Qwen3-14B). The model writes everything after it. The
paper shows a single 1–2 token cue can lift a base model's MATH-500 accuracy to near its RL-trained
counterpart.

**How the paper picks a cue.** One cue per (model, prompt format), applied to every problem:
1. Beam search ranks short openings by probability, averaged over 100 MATH-train problems; keep 20.
2. Sample 16 answers per opening on 30 problems.
3. Drop openings whose no-answer rate exceeds no-cue's by >10 points.
4. Pick the opening with the lowest mean answer entropy (answers agree most). No answer key used.

**Facts relevant to this experiment.**
- The paper never examines per-group or per-problem optimal cues. Its "best of 500 openings" check is
  an average over all of MATH-500, which could hide group differences.
- Domains do prefer different cues: Qwen's math cues *lowered* HumanEval accuracy under one prompt.
- Extending a cue along the model's single most likely continuation added little and then *hurt*
  once the opening became problem-specific (Olmo-3-7B, App. A.2.3). That tested one greedy path,
  not the best opening per group.
- Prior work (CoT-decoding, Wang & Zhou 2024) branches on alternative first tokens per problem,
  which suggests per-problem signal exists.

## 2. Hypothesis

For a set of related problems, the best cue differs between subgroups, and the subgroups nest:
domain → subject → subject × difficulty → individual problem. Two versions:

- **H1 (group tree):** best cues differ by group, and selecting per group generalizes to new problems
  in that group better than one global cue. Cues at different nodes need not be related.
- **H2 (token tree):** child-group cues extend their parent's cue as token prefixes
  (`Okay,` → `Okay, so the area` → …). H2 implies H1, not vice versa.

This experiment tests **H1 fully** and **H2 only descriptively** (Phase 6, optional).

## 3. Repo bootstrap (skip any step already done)

### 3.1 Target structure

```
cueseum/
├── AGENTS.md                  # repo-wide rules (content in §3.3)
├── README.md                  # purpose, setup, experiment index table
├── pyproject.toml             # package `cueseum` (src layout); upstream installed from submodule
├── .gitignore                 # runs/, *.parquet outside results/, caches, envs
├── third_party/
│   └── cues/                  # git submodule, pinned; never edited
├── src/cueseum/               # shared library (only code ≥2 experiments use; see §3.4)
│   ├── __init__.py
│   ├── paths.py               # resolves $CUESEUM_RUNS, experiment dirs, upstream commit
│   ├── rollouts.py            # upstream rollout JSONL → score table (parquet)
│   ├── problems.py            # load/sample problem sets with subject/level labels
│   ├── cuesets.py             # cue-list I/O, tokenization checks
│   ├── stats.py               # bootstrap CIs, grouped cross-validation, permutation nulls
│   └── plots.py               # shared figure style
├── experiments/
│   └── e01_cue_tree/
│       ├── PACKET.md          # this file
│       ├── config.yaml        # every fixed setting from §4
│       ├── data/              # tree_problems.jsonl, tree_cues.json (small, committed)
│       ├── scripts/           # run.sh + thin wrappers around `python -m cues …`
│       ├── analysis/          # e01-specific analysis code
│       ├── results/           # summary.json, figures (small, committed)
│       ├── LOG.md
│       └── REPORT.md
├── tests/                     # tests for src/cueseum only
└── docs/
    └── findings.md            # one-paragraph running summary per finished experiment
```

### 3.2 Steps

1. `git init cueseum` (or use the existing repo).
2. Add upstream as a pinned submodule:
   ```
   git submodule add https://github.com/sophicle/cues third_party/cues
   git -C third_party/cues checkout cd9caabe748307df0565502f630e3a834a9f998d
   git add third_party/cues .gitmodules
   ```
3. Environment, using upstream's pinned setup:
   ```
   bash third_party/cues/scripts/setup_env.sh /path/to/env    # Python 3.11, pinned deps, CPU tests
   source /path/to/env/bin/activate
   pip install -e third_party/cues -e .
   export CUESEUM_RUNS=/path/to/runs HF_HOME=/path/to/hf
   export RUNS=$CUESEUM_RUNS     # upstream reads $RUNS
   ```
   Requires Linux and an NVIDIA driver supporting CUDA 13. If setup fails on the driver, **stop and
   report**; do not unpin versions.
4. Write `AGENTS.md` with the content in §3.3, `README.md` with an experiment index table
   (`id | question | status | report`), `.gitignore`, and `docs/findings.md` (empty heading).
5. Create the `src/cueseum/` modules as needed by e01 (§3.4) with tests in `tests/`.
6. Commit the scaffold before running any experiment.

### 3.3 `AGENTS.md` content (create verbatim if missing; edit only with the user's approval)

```markdown
# cueseum — rules for agents

Monorepo for token-cue ablations building on sophicle/cues. Read this, then the experiment's PACKET.md.

## Layout rules
- One folder per experiment: experiments/eNN_<name>/. Numbers are sequential and never reused;
  an abandoned experiment keeps its folder and a REPORT.md saying why it stopped.
- Experiments never import from each other. Shared code lives in src/cueseum/.
- Code moves into src/cueseum/ when a second experiment needs it (exceptions are named in a packet).
  Library changes need tests in tests/ and must not break earlier experiments' scripts.
- third_party/cues is upstream, pinned as a submodule. Never edit it. If an internal change is needed,
  stop and ask; the fix is to point the submodule at a cueseum-owned fork.

## Data and outputs
- Large outputs (rollouts, checkpoints, caches) go under $CUESEUM_RUNS/<experiment>/<phase>/, never in git.
- Commit only small inputs (experiments/*/data/) and summaries (experiments/*/results/: JSON, figures,
  score tables under ~50 MB).
- Every results file records: upstream commit, cueseum commit, model id + revision, prompt, sampling
  settings, seeds.

## Running
- Call upstream through its CLI: `python -m cues …`. Settings come from the experiment's config.yaml.
- Every experiment has scripts/run.sh that reproduces it end to end, resuming from cached outputs.
- Log in the experiment's LOG.md as you go: phase start/end, GPU-hours, deviations and reasons.

## Integrity
- Headline numbers are held-out. In-sample numbers may appear only labeled as such.
- Pre-registered analyses are listed in the packet. Anything else goes in an "Exploratory" section.
- Report null and inconclusive results plainly; don't add analyses until something is significant.
- Don't change model, prompt, temperature or grader mid-experiment. If you must, restart the affected
  phases and log it.

## Stop and ask before
- exceeding the packet's GPU-hour cap,
- swapping the model or benchmark,
- deleting run outputs,
- editing third_party/ or AGENTS.md.

## Finishing an experiment
- REPORT.md written, README index row updated, one paragraph added to docs/findings.md.
- Commit messages: `eNN: <what>` for experiment work, `lib: <what>` for src/cueseum, `repo: <what>` otherwise.
```

### 3.4 Shared library scope for e01 (named exception to the "second use" rule)

These are built in `src/cueseum/` from the start because later experiments will reuse them. Keep
them general (no e01-specific names or constants):

- `rollouts.load_cells(root) -> DataFrame` — read upstream `rollouts_p*.jsonl` cells into one table:
  `cue, problem_key, rollout_index, correct, committed, hit_token_cap, output_tokens, answer_key`.
  `answer_key` via `cues.agree.answer_key(completion, style)`; check the style value against
  `cues.prompts.GRADING`. Save/load parquet.
- `problems.stratified_sample(rows, by, n_per_cell, seed, exclude_texts)`.
- `cuesets.load/save` (`{name: opening}` format), `cuesets.token_report(tokenizer, prompt, cues)`.
- `stats.bootstrap_ci`, `stats.grouped_cv_select_score(table, groups, select_fn, folds, repeats, seed)`,
  `stats.permutation_null(...)` with random groupings of matched sizes.
- `plots`: a single style function and figure-saving helper.

Everything else (hierarchy levels, clustering, decision logic) stays in
`experiments/e01_cue_tree/analysis/`.

## 4. Fixed settings (write these into `config.yaml`)

| Setting | Value | Why |
|---|---|---|
| Model | `qwen4b` (Qwen/Qwen3-4B-Base, rev `906bfd4b…`, upstream registry key) | Registered, cheap, fits one GPU, has a known cue |
| Prompt | `boxed` | The model's registry prompt |
| Temperature / top-p | 0.6 / 0.95 | Paper defaults; do not vary |
| Rollouts per (cue, problem) | 8 | Split 4/4 for select/score (Phase 5a) |
| Token budget | `--max-new-tokens 4096` | Cost; cue effects show within ~1k tokens. Report cap rate |
| Seed | `20260819` (upstream default) | Rollout r uses seed + r |
| Grader | upstream (`math-verify`, boxed answer contract) | Comparability |
| Runs root | `$CUESEUM_RUNS/e01_cue_tree/` | Per AGENTS.md |
| GPU-hour cap | 40 total (Phase 6: extra 15, only if triggered) | Stop and ask beyond this |

If no GPU with ≥24 GB is available, stop and report what is available before changing the model.

## 5. Phases

Paths below are relative to `experiments/e01_cue_tree/` unless they start with `$CUESEUM_RUNS` or
`third_party/`. Track each phase in `LOG.md`.

### Phase 0 — Smoke test
1. `python -m cues demo --model qwen4b --dry-run`, then without `--dry-run`,
   `--out $CUESEUM_RUNS/e01_cue_tree/smoke`.
2. Confirm a rollouts JSONL appears with fields `problem_key, rollout_index, cue, committed, correct,
   hit_token_cap, output_tokens, completion`.
3. Confirm `cueseum.rollouts.load_cells` reads it.

### Phase 1 — Build the problem set
Source: `third_party/cues/data/math_train.jsonl` (7,495 MATH-train problems, disjoint from MATH-500,
with `capability` = subject and `level` = 1–5).

1. Exclude the 2 rows with `level: null`.
2. Exclude any problem whose text matches a problem in
   `third_party/cues/data/problems/math_train_probe.jsonl` (the beam search's probe set; match on
   whitespace-normalized text, since keys differ).
3. Stratified sample, seed 0: **12 problems per subject × level cell** → 7 × 5 × 12 = **420 problems**.
   Every cell has ≥41 problems, so this is feasible.
4. Write `data/tree_problems.jsonl` with `problem_key, problem, gt, capability, level`, and
   `data/tree_problems_pilot.jsonl` (one problem per cell, 35 total, drawn from the 420).
5. Log the per-cell counts.

### Phase 2 — Build the candidate cue list
1. Get the model's likely openings without the expensive screen:
   `python -m cues search --model qwen4b --prompt boxed --beam-only --out $CUESEUM_RUNS/e01_cue_tree/search`
   This writes `nominees.json` (20 openings, `{slug: opening}`).
2. Add these extras if not already present (exact strings; leading spaces matter):
   ` Okay,` · ` Alright,` · ` \n\nOkay` · ` Let's` · ` First,`
3. No-cue is passed separately as `--cues none`; do not put an empty string in the file.
4. Write `data/tree_cues.json` in the same `{name: opening}` format. Target 20–26 cues.
5. Use `cueseum.cuesets.token_report` to log each cue's token ids after the rendered prompt.
   Flag any cue that merges with the prompt's final characters.

### Phase 3 — Pilot (required before the full run)
```
python -m cues eval --model qwen4b --prompt boxed \
  --benchmark data/tree_problems_pilot.jsonl \
  --cues none --cues-file data/tree_cues.json \
  --n-rollouts 8 --max-new-tokens 4096 --gpus <N> \
  --out $CUESEUM_RUNS/e01_cue_tree/pilot
```
Report in `LOG.md`:
- GPU-hours, and projected GPU-hours for 420 problems.
- Per-cue cap rate (share hitting 4,096) and no-answer rate.
- Per-cue pilot accuracy, as a sanity check that ` To determine` helps (paper: Qwen3-4B boxed
  MATH-500 54.9% → 71.5% at a 31k budget; expect lower at 4k).

**Stop conditions.** Pause and write up findings instead of continuing if:
- projected full run > 40 GPU-hours, or
- any cue's cap rate > 25% (consider raising the budget to 8,192 for all cues, logged), or
- extraction / grading errors > 2% of records.

### Phase 4 — Full run
Same command on `data/tree_problems.jsonl`, `--out $CUESEUM_RUNS/e01_cue_tree/full`. It resumes from
cached cells; rerun after any interruption. Verify every (cue, problem) has exactly 8 rollouts
(indices 0–7) before analysis.

### Phase 5 — Analysis (pre-registered: 5a–5e)
Build the score table with `cueseum.rollouts.load_cells` and save it as `results/scores.parquet`
(or under `$CUESEUM_RUNS` with a pointer if it exceeds ~50 MB).

**Informative problems.** A problem where every cue scores 0/8 or 8/8 carries no cue signal. Report
how many problems are informative and run all analyses on (a) all problems and (b) informative only.

**5a. Is there per-problem variation at all? (rollout split)**
- For each problem, choose its best cue using rollouts 0–3; score that cue on rollouts 4–7.
- Global baseline: choose the single best cue by mean accuracy on rollouts 0–3 across all problems;
  score it on rollouts 4–7.
- Report held-out accuracy for both, the difference, and a bootstrap 95% CI over problems
  (2,000 resamples). Ties: break by lowest cue index (fixed order), and record how often ties occur.
- Also report the *in-sample* gain (select and score on 0–3), labeled, to show the selection bias.

**5b. The levels (problem split)**
Levels: global (1 group) → subject (7) → level (5) → subject × level (35).
For each level, 2-fold cross-validation over problems within each group, repeated 50× with different
fold splits (`cueseum.stats.grouped_cv_select_score`):
- choose the group's best cue on the selection fold (all 8 rollouts),
- score it on the held-out fold.
Report mean held-out accuracy per level with CI. The H1 signature: held-out accuracy rises from
global to subject (and/or level), and stops rising or falls at subject × level, where groups are
only ~12 problems.

**5c. Null model: random groupings**
For each non-global level, shuffle problems into random groups of the same sizes and rerun 5b,
200 shuffles (`cueseum.stats.permutation_null`). Real groups must beat the null distribution.
Report the one-sided p-value per level.

**5d. Data-driven tree**
- Per informative problem, build a profile: cue accuracies on rollouts 0–7, minus the problem's mean
  (removes difficulty).
- Hierarchical clustering (average linkage, correlation distance). Save the dendrogram.
- Cut at k = 5 and k = 7; compare with subject and with level using adjusted Rand index and NMI.
- Stability: recompute profiles from rollouts 0–3 vs 4–7 separately and report agreement between the
  two clusterings (ARI). If they disagree, say profiles are too noisy to support a learned tree.
- Also test answer type (integer / fraction / expression / other) as an extra label.

**5e. Label-free variant**
Repeat 5a–5c choosing cues by lowest answer entropy (upstream's agreement criterion, with the
no-answer guard) instead of accuracy. Always *score* by accuracy. This tests whether a per-group
cue can be chosen without answers.

**5f. Descriptive outputs**
- Heatmap: held-out cue accuracy (rows: cues, columns: subjects; then subject × level).
- The winning cue per group at each level, and how often the winner changes vs its parent.

### Phase 6 — Token tree (optional; only if 5b/5c support H1 at the subject level)
For each of the 2–3 subjects whose best cue differs most from the global cue:
1. `python -m cues.beam --model qwen4b --prompt boxed --benchmark <subject_problems.jsonl> --depth 4
   --problems <n> --out $CUESEUM_RUNS/e01_cue_tree/phase6/<subject>` using a held-out set of that
   subject's MATH-train problems, not the 420.
2. Evaluate the top 10 openings on that subject's problems from the 420, 8 rollouts.
3. Report whether the best 3–4 token opening beats the best 1–2 token opening on held-out problems,
   and whether subject winners extend the global winner as a prefix.
Cap: 15 GPU-hours. Results go in REPORT.md under "Exploratory" unless 5b/5c triggered it.

## 6. Decision criteria (state which applies in REPORT.md)

- **H1 supported:** subject and/or level grouping beats both the global cue and the random-group
  null (p < 0.05) on held-out problems, and 5a shows positive held-out per-problem gain.
- **Partial:** per-problem variation exists (5a) but named groups don't beat random groups, i.e.
  structure exists but isn't subject/level. Point to 5d for what it might be.
- **Not supported:** no held-out gain over the global cue at any level beyond noise.
- **Inconclusive:** too few informative problems or unstable profiles. Say what sample size would be
  needed (estimate from observed variance).

## 7. Deliverables

1. `REPORT.md`: question, setup, one table of held-out accuracy by level with CIs and null p-values,
   the 5a result, clustering result, label-free result, decision, limitations, total GPU-hours.
2. `results/`: `summary.json` (all headline numbers + provenance per AGENTS.md), figures as PNG,
   score table or a pointer to it.
3. `LOG.md` with timings and deviations.
4. `scripts/run.sh` reproducing Phases 1–5 end to end with fixed seeds, resuming from cached outputs.
5. `src/cueseum/` modules from §3.4 with passing tests.
6. README index row for e01 and a paragraph in `docs/findings.md`.

## 8. Known caveats to mention in the report

- One model (Qwen3-4B-Base), one prompt, math only, 4k budget, temperature 0.6.
- Per-problem estimates from 8 rollouts are noisy (±15–20 points); leaf-level claims are weak by design.
- The candidate set comes from the model's likely openings; a low-probability cue that wins for some
  group cannot be found (the paper's own known failure mode).
- Upstream's README says the beam ranks on 100 probe problems; the paper text says 30. This
  experiment uses upstream's code as-is.
