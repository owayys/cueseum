#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
R=$CUESEUM_RUNS/e04_cue_family
mkdir -p "$R/stage1"
python build_problems.py
for m in qwen0.6b qwen1.7b qwen8b; do
  ./logged.sh stage1 "derive_$m" python derive_cues.py "$m" "$R/stage1/cues_$m.json"
done
