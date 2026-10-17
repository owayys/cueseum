#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cfg() { python -c "import sys, yaml; c = yaml.safe_load(open('../config.yaml'))
for k in sys.argv[1].split('.'): c = c[k]
print(c)" "$1"; }
R=$CUESEUM_RUNS/e02_cue_transfer
M=$(cfg model) P=$(cfg prompt) B=$(cfg benchmark)
python -c "import json, yaml; from cues.models import cue_slug; c = yaml.safe_load(open('../config.yaml'))['cues']
json.dump({cue_slug(x): x for x in c if x != 'none'}, open('../data/cues.json', 'w'), indent=1)"
SAMPLING=(--temperature "$(cfg temperature)" --top-p "$(cfg top_p)" --seed "$(cfg seed)" --gpu-memory-utilization "$(cfg gpu_memory_utilization)")
./logged.sh smoke eval python -m cues eval --model "$M" --prompt "$P" --benchmark "$B" --cues none $' Alright,' \
  --problem-count "$(cfg smoke.problems)" --n-rollouts "$(cfg smoke.n_rollouts)" --max-new-tokens "$(cfg smoke.max_new_tokens)" \
  "${SAMPLING[@]}" --out "$R/smoke"
./logged.sh pilot eval python -m cues eval --model "$M" --prompt "$P" --benchmark "$B" --cues none --cues-file ../data/cues.json \
  --problem-count "$(cfg pilot.problems)" --n-rollouts "$(cfg pilot.n_rollouts)" --max-new-tokens "$(cfg max_new_tokens)" \
  "${SAMPLING[@]}" --out "$R/pilot"
