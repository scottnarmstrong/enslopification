# Compiling the development and releasing the build

The graph is read from compiled `.olean` files, so the campaign needs a compiled build of the pinned commit. This
file covers getting one on a shared machine, and releasing it so that readers can load the development without
recompiling it. Lessons: [L33](../../lean-to-manuscript/references/lessons-learned.md#l33),
[L34](../../lean-to-manuscript/references/lessons-learned.md#l34).

## Pin first

Record three facts before anything runs, in a status file that every later report quotes:

- the commit id, in full (a branch or tag moves; links and counts must not);
- the toolchain, from `lean-toolchain` (`.olean` files are specific to the Lean version that wrote them, so the
  extractor must run with the same toolchain);
- the dependency revisions, from `lake-manifest.json` (Mathlib and the others).

## Compiling on a shared machine

**Never rebuild what an official cache provides.** For a development on Mathlib, fetch the compiled Mathlib
first, then build only the project:

```sh
LOGS=/path/outside/the/checkout                      # logs never go inside the checkout
git clone <repo-url> src && cd src && git checkout <commit>
lake exe cache get > "$LOGS/cache.log" 2>&1          # Mathlib and other dependencies, precompiled
/usr/bin/time -v taskset -c 0-7 nice -n 10 lake build <Target1> <Target2> > "$LOGS/build.log" 2>&1
grep -E 'Elapsed|Maximum resident' "$LOGS/build.log" # record wall time and peak memory
```

- Build the targets that the authors' instructions name (the README or the Lake file), not `lake build` of
  everything: a repository can hold unused tooling and experiments.
- One heavy job at a time. Check the load first (`uptime`); do not start a build, an extraction and an analysis
  together. Limit the cores (`taskset`) and the priority (`nice`). A development of about one million lines, such
  as the Yang–Mills one, takes hours to compile.
- Write a one-line status entry for each step (toolchain, cache, build exit code, time, peak memory), with UTC
  times, so that a later reader knows what was run.
- Write logs, extraction output and release files **outside the checkout**: a file written inside it is a local
  change, which `package_build.sh` refuses. `extract.py` and `package_build.sh` refuse an output directory inside
  the checkout.
- If the checkout must stay untouched (a source shared with other work), do not run `lake` in it at all: `lake`
  can update `.lake/` and the manifest. Extraction does not need it: `Extract.lean` reads `.olean` files with the
  toolchain's own `lean` (`lean +<toolchain> --run Extract.lean ...`).

If the authors or anyone else already released a compiled build of the same commit, load it instead
([below](#loading-a-released-build)), and check its checksums before use.

## Releasing the build for readers

A released build lets readers explore the development (open files, query declarations, run the extractor)
without hours of compilation. `package_build.sh` does the whole procedure; `--dry-run` prints the plan. It writes
everything to `--out`, outside the checkout, and appends a line per step to `STATUS`: a successful run contains
`TEST_PASS` (the fresh-clone test) and ends with a `DONE` line.

1. **Check the source.** The checkout is at the expected commit and has no changes outside `.lake/`.
2. **Archive what Lake needs.** The archive is the build directory as `lake unpack` expects it: `./lib` (the
   `.olean`, `.ilean` and trace files) plus the generated C files and their hashes (`./ir/**/*.c`, `*.c.hash`),
   which Lake checks. Leave out the other files under `ir/`, which Lake does not need.
3. **Checksum.** `sha256sum` of the archive into `SHA256SUMS`.
4. **Test in a fresh clone.** Clone the public repository, check out the commit, fetch dependencies from the
   official cache, `lake unpack` the archive, then `lake build --no-build <targets>`. With `--no-build`, Lake
   fails if any module would be recompiled, so success means every build job is up to date.
5. **Split under the hosting limit.** GitHub release assets are limited to 2 GiB each: split at 1.9 GB
   (`split -b 1900M -d -a 1`) and checksum the parts as well as the whole.

The Yang–Mills release: 2.2 GB compressed, in two parts, unpacking to 8.8 GB.

## Loading a released build

```sh
git clone <repo-url> src && cd src && git checkout <commit>   # the full commit id of the release notes
lake exe cache get                                            # dependencies from the official cache
mkdir ../dl && cd ../dl                                       # downloads outside the checkout
# download every part (<name>.tgz.part0, .part1, ...) and SHA256SUMS from the release page
cat <name>.tgz.part* > <name>.tgz                             # in order (a release in one file: skip this)
sha256sum -c SHA256SUMS                                       # every part and the whole archive
cd ../src && lake unpack ../dl/<name>.tgz
lake build --no-build <targets>                               # fails if any module would be recompiled
```

The compiled modules are then in `src/.lake/build/lib/lean/`: give that directory to `extract.py --lib-dir`.
`lake unpack` and `lake build` write only under `.lake/`; a checkout that must stay untouched gets its own clone for
this. A failed checksum or a module that `--no-build` would recompile means the archive does not match the
commit: do not extract from it.

## Release notes

State, in this order:

- the source repository and the full commit id, the toolchain, and the revision of each dependency;
- the contents (which directories, which files left out) and the sizes (compressed, each part, unpacked);
- the commands: clone, check out, fetch dependencies, download the parts and `SHA256SUMS`, concatenate,
  `sha256sum -c`, `lake unpack`, `lake build <targets>` (and `--no-build` to confirm nothing is recompiled);
- the test performed (fresh clone, platform, number of jobs up to date) and what was not tested;
- the licence of the source, which applies to the compiled files; attach its `LICENSE` and `NOTICE`.

## What loading a released build establishes

Say this in the release notes and wherever the release is mentioned:

- A matching checksum shows that the download is the file that was published. It says nothing about how that
  file was produced.
- "All targets up to date" shows that Lake's trace hashes match the source at that commit. Lake did not
  recompile anything and the kernel did not re-check anything: loading the build is convenient for exploring and
  is **not an independent rebuild**.
- Give the rebuild recipe separately: a fresh clone without the archive, the dependency cache, the build of the
  targets, and the authors' own verification programs. Say that this recipe still trusts the downloaded
  dependency cache.

A sentence of the form "Loading these files is convenient for exploring the proof; it does not independently
recompile it. To rebuild from source, follow ..." covers the second and third points.
