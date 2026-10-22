#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
R=$CUESEUM_RUNS/e04_cue_family
mkdir -p "$R/stage1"
python build_problems.py
for m in qwen0.6b qwen1.7b qwen8b; do
  ./logged.sh stage1 "derive_$m" python derive_cues.py "$m" "$R/stage1/cues_$m.json"
done
cfg() { python -c "import sys, yaml; c = yaml.safe_load(open('../config.yaml'))
for k in sys.argv[1].split('/'): c = c[k]
print(c)" "$1"; }
for m in qwen0.6b qwen1.7b qwen8b; do
  ./logged.sh screen "eval_$m" python -m cues eval --model "$(cfg models/$m/hub)" --revision "$(cfg models/$m/revision)" \
    --family "$(cfg family)" --label "$m" --prompt "$(cfg prompt)" --cues none --cues-file "../data/eval_cues_$m.json" \
    --n-rollouts "$(cfg n_rollouts)" --max-new-tokens "$(cfg max_new_tokens)" --temperature "$(cfg temperature)" \
    --top-p "$(cfg top_p)" --seed "$(cfg seed)" --gpu-memory-utilization "$(cfg gpu_memory_utilization)" \
    --benchmark ../data/screen.jsonl --out "$R/screen"
done
python build_confirm_cues.py
for m in qwen0.6b qwen1.7b qwen8b; do
  [ -f "../data/confirm_cues_$m.json" ] || continue
  ./logged.sh confirm "eval_$m" python -m cues eval --model "$(cfg models/$m/hub)" --revision "$(cfg models/$m/revision)" \
    --family "$(cfg family)" --label "$m" --prompt "$(cfg prompt)" --cues --cues-file "../data/confirm_cues_$m.json" \
    --n-rollouts "$(cfg n_rollouts)" --max-new-tokens "$(cfg max_new_tokens)" --temperature "$(cfg temperature)" \
    --top-p "$(cfg top_p)" --seed "$(cfg seed)" --gpu-memory-utilization "$(cfg gpu_memory_utilization)" \
    --benchmark ../data/confirm.jsonl --out "$R/confirm"
done
P=exploratory_post_trained
./logged.sh "$P" pilot python -m cues eval --model "$(cfg $P/model/hub)" --revision "$(cfg $P/model/revision)" --family "$(cfg family)" \
  --label "$(cfg $P/label)" --chat --no-think --prompt "$(cfg $P/prompt)" --cues none --cues-file ../data/eval_cues_post_trained.json \
  --n-rollouts "$(cfg n_rollouts)" --max-new-tokens "$(cfg max_new_tokens)" --temperature "$(cfg temperature)" --top-p "$(cfg top_p)" \
  --seed "$(cfg seed)" --gpu-memory-utilization "$(cfg gpu_memory_utilization)" --benchmark ../data/pilot_post_trained.jsonl --out "$R/$P/pilot"
