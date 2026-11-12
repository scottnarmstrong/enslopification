#!/usr/bin/env python3
"""Run Extract.lean over a compiled Lean build, a chunk of modules at a time, one process at a time.

Lists the `.olean` files under a build library directory (for a Lake project: `.lake/build/lib/lean`), splits
them into chunks of N modules and runs `Extract.lean` on each chunk with the Lean command you choose. The runs
are sequential (never two Lean processes at once), niced, and resumable: a chunk whose `chunk_NNNNN.tsv`
exists is skipped, and a failed chunk leaves only a `.part` file and a log.

Output directory (outside the checkout; one inside the directory that holds `.lake` is refused):
  plan.json           lib dir, chunk size, module count (a resumed run must use the same values)
  modules.tsv         module, path of every listed .olean (in chunk order)
  chunk_NNNNN.tsv     Extract.lean output for chunk NNNNN (see Extract.lean for the record format)
  chunk_NNNNN.log     stderr/stdout of the Lean process, with wall time and peak memory

Usage:
  extract.py --lib-dir PROJECT/.lake/build/lib/lean --out-dir raw \
      --lean-cmd "lean +leanprover/lean4:v4.32.0 --run"
  extract.py ... --dry-run          print the plan and the first command; run nothing, write nothing
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def die(msg):
    print(f'extract.py: {msg}', file=sys.stderr)
    sys.exit(2)


def list_modules(lib_dir, include, exclude):
    """Return (module, path) for every .olean under lib_dir, sorted by module name."""
    mods = []
    for p in lib_dir.rglob('*.olean'):
        rel = p.relative_to(lib_dir).with_suffix('')
        mod = '.'.join(rel.parts)
        if include and not re.search(include, mod):
            continue
        if exclude and re.search(exclude, mod):
            continue
        mods.append((mod, str(p)))
    mods.sort()
    return mods


def main():
    ap = argparse.ArgumentParser(
        description='Run Extract.lean over a compiled Lean build in chunks, one Lean process at a time.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example:\n'
               '  extract.py --lib-dir Proj/.lake/build/lib/lean --out-dir raw \\\n'
               '      --lean-cmd "lean +leanprover/lean4:v4.32.0 --run"\n'
               'Most of a chunk\'s peak memory is the Lean runtime itself, so larger chunks cost little more.')
    ap.add_argument('--lib-dir', required=True, help='directory holding the project .olean files')
    ap.add_argument('--out-dir', required=True, help='directory for plan.json, modules.tsv and chunk files')
    ap.add_argument('--lean-cmd', default=os.environ.get('ENSLOP_LEAN_CMD', 'lean --run'),
                    help='command that runs a Lean file with `--run` (default: $ENSLOP_LEAN_CMD or "lean --run"); '
                         'e.g. "lean +leanprover/lean4:v4.32.0 --run" or "lake env lean --run"')
    ap.add_argument('--extract', default=str(HERE / 'Extract.lean'), help='path to Extract.lean')
    ap.add_argument('--chunk-size', type=int, default=1000, help='modules per Lean process (default 1000)')
    ap.add_argument('--include', help='only modules whose name matches this regex')
    ap.add_argument('--exclude', help='skip modules whose name matches this regex')
    ap.add_argument('--limit', type=int, help='only the first N modules (for a test run)')
    ap.add_argument('--max-chunks', type=int, help='run at most this many pending chunks, then stop')
    ap.add_argument('--cwd', help='working directory for the Lean command (needed for "lake env")')
    ap.add_argument('--nice', type=int, default=10, help='niceness of the Lean process (default 10; 0 = none)')
    ap.add_argument('--dry-run', action='store_true', help='print the plan; run and write nothing')
    a = ap.parse_args()

    lib = Path(a.lib_dir).expanduser().resolve()
    out = Path(a.out_dir).expanduser().resolve()
    extract = Path(a.extract).expanduser().resolve()
    if not lib.is_dir():
        die(f'no such directory: {lib}')
    if '.lake' in lib.parts:      # the checkout is the directory holding .lake: write nothing inside it
        root = Path(*lib.parts[:lib.parts.index('.lake')])
        if out == root or root in out.parents:
            die(f'--out-dir {out} is inside the checkout {root}: write chunks and logs outside it (the checkout '
                f'stays read-only, and package_build.sh refuses a checkout with local changes)')
    if not extract.is_file():
        die(f'Extract.lean not found: {extract}')
    if a.chunk_size < 1:
        die('--chunk-size must be positive')
    mods = list_modules(lib, a.include, a.exclude)
    if a.limit:
        mods = mods[:a.limit]
    if not mods:
        die(f'no .olean files selected under {lib}')
    chunks = [mods[i:i + a.chunk_size] for i in range(0, len(mods), a.chunk_size)]
    plan = {'lib_dir': str(lib), 'chunk_size': a.chunk_size, 'modules': len(mods),
            'include': a.include, 'exclude': a.exclude, 'limit': a.limit}
    base_cmd = shlex.split(a.lean_cmd)
    if a.nice > 0:
        base_cmd = ['nice', '-n', str(a.nice)] + base_cmd

    def done(k):
        return (out / f'chunk_{k:05d}.tsv').exists()

    pending = [k for k in range(len(chunks)) if not done(k)]
    if a.dry_run:
        print(f'plan: {len(mods)} modules from {lib}, {len(chunks)} chunks of at most {a.chunk_size}; '
              f'{len(chunks) - len(pending)} done, {len(pending)} pending')
        if pending:
            k = pending[0]
            cmd = base_cmd + [str(extract), str(out / f'chunk_{k:05d}.tsv.part'), '@' + str(out / f'chunk_{k:05d}.pairs')]
            print('first command:', shlex.join(cmd))
            print(f'  chunk {k:05d}: {chunks[k][0][0]} .. {chunks[k][-1][0]} ({len(chunks[k])} modules)')
        print('dry run: nothing executed, nothing written')
        return 0

    out.mkdir(parents=True, exist_ok=True)
    pf = out / 'plan.json'
    if pf.exists():
        old = json.loads(pf.read_text())
        if {k: old.get(k) for k in plan} != plan:
            die(f'{pf} was written with different settings {old}; use a fresh --out-dir')
    else:
        pf.write_text(json.dumps(plan, indent=1) + '\n')
    with open(out / 'modules.tsv', 'w', encoding='utf-8') as f:
        f.write('module\tpath\n')
        for m, p in mods:
            f.write(f'{m}\t{p}\n')

    ran = failed = 0
    peak_kb = 0
    t_all = time.time()
    for k in pending:
        if a.max_chunks is not None and ran + failed >= a.max_chunks:
            break
        part = out / f'chunk_{k:05d}.tsv.part'
        pairs = out / f'chunk_{k:05d}.pairs'
        logf = out / f'chunk_{k:05d}.log'
        pairs.write_text(''.join(f'{m}={p}\n' for m, p in chunks[k]), encoding='utf-8')
        cmd = base_cmd + [str(extract), str(part), '@' + str(pairs)]
        t0 = time.time()
        with open(logf, 'w', encoding='utf-8') as lg:
            lg.write('$ ' + shlex.join(cmd) + '\n')
            lg.flush()
            proc = subprocess.Popen(cmd, cwd=a.cwd, stdout=lg, stderr=subprocess.STDOUT)
            _, status, ru = os.wait4(proc.pid, 0)
            proc.returncode = os.waitstatus_to_exitcode(status)
            secs = time.time() - t0
            peak_kb = max(peak_kb, ru.ru_maxrss)
            lg.write(f'\nexit {proc.returncode}; {secs:.1f} s; peak RSS {ru.ru_maxrss / 1024:.0f} MB\n')
        if proc.returncode == 0 and part.exists():
            part.rename(out / f'chunk_{k:05d}.tsv')
            pairs.unlink()
            ran += 1
            print(f'chunk {k:05d}: {len(chunks[k])} modules, {secs:.1f} s, peak {ru.ru_maxrss / 1024:.0f} MB', flush=True)
        else:
            failed += 1
            print(f'chunk {k:05d}: FAILED (exit {proc.returncode}); see {logf}', flush=True)
    left = sum(1 for k in range(len(chunks)) if not done(k))
    print(f'extract: {len(mods)} modules in {len(chunks)} chunks; ran {ran}, failed {failed}, '
          f'still pending {left}; peak RSS {peak_kb / 1024:.0f} MB; {time.time() - t_all:.0f} s')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
