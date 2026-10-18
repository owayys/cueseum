# cueseum

Token-cue ablations building on [sophicle/cues](https://github.com/sophicle/cues) (pinned at `third_party/cues`). Agents: read `AGENTS.md` first.

## Setup

```bash
git submodule update --init
bash third_party/cues/scripts/setup_env.sh /path/to/env
source /path/to/env/bin/activate
pip install -e third_party/cues -e .
export CUESEUM_RUNS=/path/to/runs HF_HOME=/path/to/hf RUNS=$CUESEUM_RUNS
```

## Experiments

| id | question | status | report |
|---|---|---|---|
| e01 | Do optimal token cues form a tree over problem groups? | done: not supported | [REPORT](experiments/e01_cue_tree/REPORT.md) |
| e02 | Do cues from a larger model transfer to a smaller sibling? | paused: H1 over budget | [REPORT](experiments/e02_cue_transfer/REPORT.md) |
