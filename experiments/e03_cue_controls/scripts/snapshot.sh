#!/usr/bin/env bash
set -euo pipefail
out="$CUESEUM_RUNS/e03_cue_controls/env/$(date -u +%Y%m%dT%H%M%SZ)"
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
mkdir -p "$out"
nvidia-smi > "$out/nvidia-smi.txt"
uname -a > "$out/uname.txt"
python -c "import importlib.metadata as m; print('\n'.join(sorted(f'{d.name}=={d.version}' for d in m.distributions())))" > "$out/packages.txt"
{ git -C "$root" rev-parse HEAD; git -C "$root" submodule status; git -C "$root" status --short; } > "$out/git.txt"
env | grep -E '^(CUESEUM_RUNS|RUNS|HF_HOME|CUDA_VISIBLE_DEVICES|RUNPOD_POD_ID|RUNPOD_GPU_COUNT)=' > "$out/env.txt" || true
echo "$out"
