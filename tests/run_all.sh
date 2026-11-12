#!/usr/bin/env bash
# Run every smoke test of the collection. Usage: tests/run_all.sh [-h]
# Each tests/smoke_<skill>.sh creates its own temporary directory, uses only synthetic inputs (or skips a step whose
# tool is missing, saying so), and exits non-zero on failure. Nothing here calls an agent or touches the network.
set -euo pipefail
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then sed -n '2,4p' "$0"; exit 0; fi
cd "$(dirname "$0")"
LOGS="$(mktemp -d)"
fail=0; n=0
for t in smoke_*.sh; do
  n=$((n+1))
  if bash "$t" > "$LOGS/$t.log" 2>&1; then echo "PASS $t"; else echo "FAIL $t (log: $LOGS/$t.log)"; fail=$((fail+1)); fi
done
echo "run_all: $n smoke tests, $fail failed"
if (( fail == 0 )); then rm -rf "$LOGS"; else echo "logs kept in $LOGS"; fi
find .. -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
exit $(( fail > 0 ))
