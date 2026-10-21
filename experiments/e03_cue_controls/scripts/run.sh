#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
R=$CUESEUM_RUNS/e03_cue_controls
mkdir -p "$R/stage1"
python build_problems.py
./logged.sh stage1 reasoning_style python derive_reasoning_style.py "$R/stage1/reasoning_style.json"
./logged.sh stage1 probability_matched python derive_probability_matched.py "$R/stage1/probability_matched.json"
