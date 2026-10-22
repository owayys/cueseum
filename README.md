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
| e03 | Is ` Alright,` specifically good for Qwen3-4B, or are similar openers equally good? | done: specific to ` Alright,` (screen) | [REPORT](experiments/e03_cue_controls/REPORT.md) |
| e04 | Is ` Alright,` a good cue across the Qwen3 base family? | done: specific to ` Alright,` at 0.6B–8B | [REPORT](experiments/e04_cue_family/REPORT.md) |
