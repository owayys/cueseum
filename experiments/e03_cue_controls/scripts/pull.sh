#!/usr/bin/env bash
set -euo pipefail
host=$1 port=$2 remote=${3:-/workspace/runs}
dest="${CUESEUM_RUNS:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/runs}/e03_cue_controls/"
mkdir -p "$dest"
rsync -az --partial -e "ssh -p $port" "$host:$remote/e03_cue_controls/" "$dest"
