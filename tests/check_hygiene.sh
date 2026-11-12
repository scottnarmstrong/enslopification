#!/usr/bin/env bash
# Repository hygiene: no machine paths, e-mail addresses, account or wrapper names, LLM-coded filler words, and none of
# the project-specific private patterns listed in the file named by ENSLOP_PRIVATE_PATTERNS (kept outside the repo).
# Usage: [ENSLOP_PRIVATE_PATTERNS=file] tests/check_hygiene.sh [-h] [ROOT]. Exit 1 on any hit, 2 on a bad pattern file.
set -euo pipefail
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then sed -n '2,4p' "$0"; exit 0; fi
ROOT="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$ROOT"
hits=0
scan() {  # $1 = label, $2 = extended regex, $3.. = extra grep options
  local label="$1" re="$2"; shift 2
  local out
  out="$(grep -rInE "$@" --exclude-dir=.git --exclude-dir=.orchestrator --exclude=check_hygiene.sh -e "$re" . || true)"
  if [[ -n "$out" ]]; then echo "== $label"; echo "$out" | head -20; hits=$((hits + $(echo "$out" | wc -l))); fi
}
scan "machine paths"            '/home/[a-z]|/Users/[A-Za-z]|/tmp/claude'
scan "email addresses"          '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(com|org|net|edu|fr|io)'
scan "account or wrapper names" '\b(claude|codex)-[0-9]\b'
scan "LLM-coded words"          '\b(delve|leverag(e|es|ed|ing)|seamless(ly)?|tapestry|game-changer|cutting-edge|state-of-the-art|unlock(s|ed|ing)?|showcas(e|es|ed|ing)|holistic|multifaceted|pivotal|groundbreaking|paradigm shift|it.s worth noting)\b' -i --exclude='smoke_*.sh' --exclude-dir=wordlists
# Project-specific patterns (names of private directories, machines, sessions or people that must never appear) are
# kept OUT of the repository: one extended regex per line in the file named by ENSLOP_PRIVATE_PATTERNS.
if [[ -n "${ENSLOP_PRIVATE_PATTERNS:-}" ]]; then
  [[ -r "$ENSLOP_PRIVATE_PATTERNS" ]] || { echo "check_hygiene: cannot read $ENSLOP_PRIVATE_PATTERNS"; exit 2; }
  while IFS= read -r pat; do
    [[ -z "$pat" || "$pat" == \#* ]] && continue
    scan "private pattern" "$pat" --exclude=LICENSE
  done < "$ENSLOP_PRIVATE_PATTERNS"
else
  echo "(no ENSLOP_PRIVATE_PATTERNS file given: project-specific private names not checked)"
fi
echo "check_hygiene: $hits hit(s)"
exit $(( hits > 0 ))
