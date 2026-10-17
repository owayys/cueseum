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
