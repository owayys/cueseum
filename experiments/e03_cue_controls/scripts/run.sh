#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
R=$CUESEUM_RUNS/e03_cue_controls
mkdir -p "$R/stage1"
python build_problems.py
./logged.sh stage1 reasoning_style python derive_reasoning_style.py "$R/stage1/reasoning_style.json"
./logged.sh stage1 probability_matched python derive_probability_matched.py "$R/stage1/probability_matched.json"
cfg() { python -c "import sys, yaml; print(yaml.safe_load(open('../config.yaml'))[sys.argv[1]])" "$1"; }
EVAL=(--model "$(cfg model)" --prompt "$(cfg prompt)" --cues none --cues-file ../data/eval_cues.json --n-rollouts "$(cfg n_rollouts)"
  --max-new-tokens "$(cfg max_new_tokens)" --temperature "$(cfg temperature)" --top-p "$(cfg top_p)" --seed "$(cfg seed)"
  --gpu-memory-utilization "$(cfg gpu_memory_utilization)")
./logged.sh screen eval python -m cues eval "${EVAL[@]}" --benchmark ../data/screen.jsonl --out "$R/screen"
