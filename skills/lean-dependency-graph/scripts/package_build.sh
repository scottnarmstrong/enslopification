#!/usr/bin/env bash
# package_build.sh: package the compiled Lake build of a pinned commit for readers.
#
# Steps: (1) check that the source checkout is at the expected commit with no local changes (outside .lake/);
# (2) archive the build directory as `lake unpack` expects it (./lib, plus the generated C files ./ir/**/*.c and
# *.c.hash that Lake checks; other ir files are left out); (3) write SHA256SUMS; (4) test in a fresh clone:
# fetch dependencies (official cache), `lake unpack`, then `lake build --no-build <targets>`, which fails if any
# module would be recompiled; (5) split the archive into parts below the hosting limit (GitHub: 2 GiB per file)
# and checksum the parts too. Every step appends a line to <out>/STATUS, a UTC time followed by the event
# ("2026-11-01T08:00:00Z DONE ..."): on success the file contains TEST_PASS (unless --skip-test) and ends with a DONE
# line. --out must lie outside the checkout: a file written there is a local change, which step (1) refuses.
#
# Loading such an archive is convenient for exploring; it is not an independent rebuild. Say so in the release
# notes and give the rebuild recipe separately (see references/build-and-release.md).
set -euo pipefail

usage() {
  cat <<'EOF'
usage: package_build.sh --source DIR --commit SHA --out DIR --targets "T1 T2" [options]

  --source DIR        project checkout holding .lake/build (required)
  --commit SHA        commit the checkout must be at (hex, full or abbreviated; required)
  --out DIR           output directory for the archive, SHA256SUMS, logs and STATUS (required; outside
                      the checkout)
  --targets "A B"     Lake targets for `lake build --no-build` in the fresh clone (required unless --skip-test)
  --name FILE         archive name (default: build-<commit[0:7]>.tgz)
  --repo-url URL      repository cloned for the test (default: the origin URL of --source)
  --cache-cmd CMD     dependency fetch in the fresh clone (default: "lake exe cache get"; "" skips it)
  --split-size SIZE   size of each part, as for split -b (default 1900M)
  --split-threshold N split when the archive has at least N bytes (default 2000000000)
  --jobs N            compression threads when pigz is available (default 4)
  --skip-test         do not run the fresh-clone test
  --dry-run           print the plan and change nothing
  -h, --help          this text

example (the Yang-Mills release: 2.2 GB in two parts):
  package_build.sh --source src/OpenAI-YM-20261028 --commit 3456e5e75cf8d4cd558955a5c7638fba2d68f464 \
      --out release --name ym-build-3456e5e.tgz --targets "WilsonReference WilsonConstruction"
EOF
}

SRC= COMMIT= OUT= TARGETS= NAME= REPO= CACHE_CMD="lake exe cache get" SPLIT=1900M THRESH=2000000000
JOBS=4 SKIP_TEST=0 DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --source) SRC=$2; shift 2 ;;
    --commit) COMMIT=$2; shift 2 ;;
    --out) OUT=$2; shift 2 ;;
    --targets) TARGETS=$2; shift 2 ;;
    --name) NAME=$2; shift 2 ;;
    --repo-url) REPO=$2; shift 2 ;;
    --cache-cmd) CACHE_CMD=$2; shift 2 ;;
    --split-size) SPLIT=$2; shift 2 ;;
    --split-threshold) THRESH=$2; shift 2 ;;
    --jobs) JOBS=$2; shift 2 ;;
    --skip-test) SKIP_TEST=1; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "package_build.sh: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
die() { echo "package_build.sh: $*" >&2; exit 2; }
[ -n "$SRC" ] && [ -n "$COMMIT" ] && [ -n "$OUT" ] || { usage >&2; exit 2; }
[[ "$COMMIT" =~ ^[0-9a-fA-F]{7,40}$ ]] || die "--commit must be a hexadecimal commit id, not a branch or tag: $COMMIT"
COMMIT=${COMMIT,,}
[ "$SKIP_TEST" = 1 ] || [ -n "$TARGETS" ] || die "--targets is required for the fresh-clone test (or --skip-test)"
SRC=$(cd "$SRC" && pwd -P) || die "no such directory: $SRC"
case "$OUT" in /*) OUT_ABS=$OUT ;; *) OUT_ABS=$PWD/$OUT ;; esac
OUT_ABS=$(realpath -m "$OUT_ABS" 2>/dev/null || printf '%s' "$OUT_ABS")
case "$OUT_ABS/" in "$SRC"/*) die "--out $OUT is inside the checkout $SRC: write the archive and logs outside it" ;; esac
BUILD="$SRC/.lake/build"
[ -d "$BUILD/lib" ] || die "no compiled build at $BUILD/lib"
[ -n "$NAME" ] || NAME="build-${COMMIT:0:7}.tgz"
[ -n "$REPO" ] || REPO=$(git -C "$SRC" remote get-url origin 2>/dev/null) || die "no --repo-url and no origin remote"
if command -v pigz >/dev/null 2>&1; then ZIP=(pigz -9 -p "$JOBS"); else ZIP=(gzip -9); fi

if [ "$DRY" = 1 ]; then
  cat <<EOF
plan (dry run; nothing is changed):
  1. check $SRC is at $COMMIT with no changes outside .lake/
  2. archive $BUILD/lib (+ ir *.c, *.c.hash if present) with ${ZIP[*]} -> $OUT/$NAME
  3. sha256sum -> $OUT/SHA256SUMS
EOF
  if [ "$SKIP_TEST" = 1 ]; then echo "  4. fresh-clone test skipped (--skip-test)"; else cat <<EOF
  4. git clone $REPO $OUT/test; checkout $COMMIT; ${CACHE_CMD:-(no dependency fetch)};
     lake unpack $OUT/$NAME; lake build --no-build $TARGETS
EOF
  fi
  echo "  5. if the archive has >= $THRESH bytes: split -b $SPLIT into $OUT/$NAME.partN, checksum the parts"
  exit 0
fi

mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$OUT/STATUS"; }
log "START source=$SRC commit=$COMMIT"
HEAD=$(git -C "$SRC" rev-parse HEAD)
case "$HEAD" in "$COMMIT"*) ;; *) log "FAIL source HEAD $HEAD is not $COMMIT"; exit 1 ;; esac
if git -C "$SRC" status --porcelain | grep -v '^?? \.lake/$' | grep -q .; then
  log "FAIL source tree has local changes"; exit 1
fi

# 1. archive (lib, and the generated C files that Lake checks)
cd "$BUILD"
: > "$OUT/irlist"
[ -d ./ir ] && find ./ir -type f \( -name '*.c' -o -name '*.c.hash' \) | sort > "$OUT/irlist"
log "ARCHIVE lib=$(du -sb lib | cut -f1) bytes, ir C files=$(wc -l < "$OUT/irlist")"
tar -cf - ./lib -T "$OUT/irlist" | nice -n 10 "${ZIP[@]}" > "$OUT/$NAME"
cd "$OUT"
SZ=$(stat -c %s "$NAME")
log "ARCHIVE_OK $NAME $SZ bytes"
sha256sum "$NAME" > SHA256SUMS

# 2. test in a fresh clone
if [ "$SKIP_TEST" = 0 ]; then
  rm -rf "$OUT/test"
  git clone -q "$REPO" "$OUT/test"
  git -C "$OUT/test" checkout -q "$COMMIT"
  cd "$OUT/test"
  if [ -n "$CACHE_CMD" ]; then
    t0=$(date +%s)
    if bash -c "$CACHE_CMD" > "$OUT/test-cache.log" 2>&1; then log "TEST dependencies OK ($(( $(date +%s) - t0 )) s)"
    else log "FAIL dependency fetch (see test-cache.log)"; exit 1; fi
  fi
  t0=$(date +%s)
  if lake unpack "$OUT/$NAME" > "$OUT/test-unpack.log" 2>&1; then log "TEST unpack OK ($(( $(date +%s) - t0 )) s)"
  else log "FAIL lake unpack (see test-unpack.log)"; exit 1; fi
  # shellcheck disable=SC2086
  if lake build --no-build $TARGETS > "$OUT/test-nobuild.log" 2>&1; then
    log "TEST_PASS $(tail -1 "$OUT/test-nobuild.log")"
  else
    log "TEST_FAIL $(grep -m3 -E 'error|out-of-date|✖' "$OUT/test-nobuild.log" | tr '\n' ' ')"; exit 1
  fi
  cd "$OUT"
fi

# 3. split below the hosting limit
if [ "$SZ" -ge "$THRESH" ]; then
  split -b "$SPLIT" -d -a 1 "$NAME" "$NAME.part"
  sha256sum "$NAME" "$NAME".part* > SHA256SUMS
  log "SPLIT $(ls "$NAME".part* | tr '\n' ' ')"
fi
log "DONE $NAME $SZ bytes; checksums in SHA256SUMS"
