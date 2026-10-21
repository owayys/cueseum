#!/usr/bin/env bash
set -uo pipefail
log="$CUESEUM_RUNS/e04_cue_family/$1/logs/$2.log"
shift 2
mkdir -p "$(dirname "$log")"
echo "# $(date -u +%FT%TZ) start: $*" | tee -a "$log"
"$@" 2>&1 | tee -a "$log"
rc=${PIPESTATUS[0]}
echo "# $(date -u +%FT%TZ) end rc=$rc" | tee -a "$log"
exit "$rc"
