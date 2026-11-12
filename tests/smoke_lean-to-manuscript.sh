#!/usr/bin/env bash
# Smoke test for lean-to-manuscript: init_campaign.py --help, dry run, real run, idempotent rerun.
set -euo pipefail
S="$(cd "$(dirname "$0")/.." && pwd)/skills/lean-to-manuscript/scripts"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
python3 -I "$S/init_campaign.py" --help > /dev/null
python3 -I "$S/init_campaign.py" "$T/w" --dry-run | grep -q 'would create: BRIEF.md'
[ ! -e "$T/w" ]
python3 -I "$S/init_campaign.py" "$T/w" --title "Smoke" > /dev/null
grep -q '^# Brief: Smoke' "$T/w/BRIEF.md"
for d in spine prompts/superseded proposals reviews rollout correspondence; do [ -d "$T/w/$d" ]; done
python3 -I "$S/init_campaign.py" "$T/w" | grep -q '0 created'
echo "smoke_lean-to-manuscript: ok"
