#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cfg() { python -c "import sys, yaml; print(yaml.safe_load(open('../config.yaml'))[sys.argv[1]])" "$1"; }
R=$CUESEUM_RUNS/e01_cue_tree
M=$(cfg model) P=$(cfg prompt)
python build_problems.py
./logged.sh smoke demo python -m cues demo --model "$M" --out "$R/smoke"
./logged.sh search beam_only python -m cues search --model "$M" --prompt "$P" --beam-only --out "$R/search"
./logged.sh search build_cues python build_cues.py "$R/search/nominees.json"
./logged.sh pilot eval python -m cues eval --model "$M" --prompt "$P" --benchmark ../data/tree_problems_pilot.jsonl \
  --cues none --cues-file ../data/tree_cues.json --n-rollouts "$(cfg n_rollouts)" --max-new-tokens "$(cfg max_new_tokens)" \
  --temperature "$(cfg temperature)" --top-p "$(cfg top_p)" --seed "$(cfg seed)" \
  --gpu-memory-utilization "$(cfg gpu_memory_utilization)" --out "$R/pilot"
python ../analysis/pilot_report.py "$R/pilot" 0.731 12
./logged.sh full eval python -m cues eval --model "$M" --prompt "$P" --benchmark ../data/tree_problems.jsonl \
  --cues none --cues-file ../data/tree_cues.json --n-rollouts "$(cfg n_rollouts)" --max-new-tokens "$(cfg max_new_tokens)" \
  --temperature "$(cfg temperature)" --top-p "$(cfg top_p)" --seed "$(cfg seed)" \
  --gpu-memory-utilization "$(cfg gpu_memory_utilization)" --out "$R/full"
python ../analysis/analyze.py "$R/full" ../results
python -c "import sys; from cueseum.rollouts import load_cells, save; save(load_cells(sys.argv[1]), '../results/scores.parquet')" "$R/full"
