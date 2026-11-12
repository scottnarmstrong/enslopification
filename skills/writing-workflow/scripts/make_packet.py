#!/usr/bin/env python3
"""Freeze a review packet: copy files into a directory and write manifest.json (SHA-256 of every file, the git HEAD
of each repository given with --repo, the UTC time).

A review verdict applies to the packet it read and to nothing else. Reviewers read the copy, so the writers and the
editor may keep working on the originals; verify_packet.py later tells whether the copy or the originals changed.

Each SOURCE argument is [DEST=]PATH:
  a file        is copied to DEST (default: its file name);
  a directory   is copied recursively to DEST/ (default: its directory name);
  a glob        (quote it) copies every match into DEST/ (default: the packet root).
DEST is a relative path inside the packet; it lets prompts say "the proposal is in PACKET/proposal/".

The manifest is written last: a packet without manifest.json is incomplete. An existing packet is never
overwritten (exit 2) unless --force is given.

Usage:
  make_packet.py OUT [DEST=]PATH [...] [--repo DIR]... [--exclude GLOB]... [--note TEXT] [--force]
Exit status: 0 ok, 2 usage or input error (missing source, two sources for one destination, existing packet).
"""
from __future__ import annotations

import argparse
import fnmatch
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_EXCLUDE = [".git", ".lake", "__pycache__"]
DEST_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-/")


class PacketError(ValueError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def split_spec(spec: str) -> tuple[str | None, str]:
    """'proposal=/a/b' -> ('proposal', '/a/b'); '/a/b' -> (None, '/a/b')."""
    if "=" in spec:
        dest, src = spec.split("=", 1)
        if dest and set(dest) <= DEST_OK and not dest.startswith(("/", "..")):
            return dest.strip("/"), src
    return None, spec


def _excluded(name: str, rel: str, exclude: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat) for pat in exclude)


def expand(specs: list[tuple[str | None, str]], exclude: list[str]) -> list[tuple[str, Path]]:
    """Turn (DEST, SOURCE) pairs into (relative destination, absolute source file) pairs."""
    out: list[tuple[str, Path]] = []
    for dest, src in specs:
        if glob.has_magic(src):
            matches = sorted(glob.glob(src))
            if not matches:
                raise PacketError(f"no file matches {src}")
            pairs = [(f"{dest}/{Path(m).name}" if dest else Path(m).name, Path(m)) for m in matches]
        else:
            pairs = [(dest or Path(src).name, Path(src))]
        for d, s in pairs:
            s = s.resolve()
            if not s.exists():
                raise PacketError(f"source does not exist: {s}")
            if s.is_file():
                out.append((d, s))
                continue
            for root, dirs, files in os.walk(s):
                rel_root = os.path.relpath(root, s)
                dirs[:] = sorted(x for x in dirs if not _excluded(x, os.path.normpath(os.path.join(rel_root, x)),
                                                                   exclude))
                for name in sorted(files):
                    rel = os.path.normpath(os.path.join(rel_root, name))
                    if not _excluded(name, rel, exclude):
                        out.append((os.path.normpath(os.path.join(d, rel)), Path(root) / name))
    seen: dict[str, Path] = {}
    for d, s in out:
        if d in seen and seen[d] != s:
            raise PacketError(f"two sources for {d}: {seen[d]} and {s} (give one of them a DEST= name)")
        seen[d] = s
    return sorted(seen.items())


def git_state(repo: Path) -> dict:
    """HEAD and whether tracked files differ from it. Read-only (no index refresh)."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    try:
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True,
                              env=env, timeout=60)
        if head.returncode != 0:
            return {"head": None, "error": head.stderr.strip()[:200]}
        status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
                                capture_output=True, text=True, env=env, timeout=120)
        return {"head": head.stdout.strip(), "dirty": bool(status.stdout.strip())}
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"head": None, "error": str(e)}


def freeze(out: Path, specs: list[tuple[str | None, str]], repos: list[str] | None = None,
           exclude: list[str] | None = None, note: str | None = None, force: bool = False) -> dict:
    """Copy the sources into OUT and write OUT/manifest.json. Returns the manifest."""
    out = Path(out)
    exclude = DEFAULT_EXCLUDE + list(exclude or [])
    if (out / "manifest.json").exists() and not force:
        raise PacketError(f"{out} is already a frozen packet (manifest.json exists); use a new directory")
    files = expand(specs, exclude)
    if not files:
        raise PacketError("nothing to freeze")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    manifest = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "tool": "make_packet.py",
                "note": note or "", "files": {}, "sources": {}, "repos": {}, "exclude": exclude}
    for dest, src in files:
        target = out / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
        manifest["files"][dest] = sha256(target)
        manifest["sources"][dest] = str(src)
    for repo in repos or []:
        manifest["repos"][str(Path(repo).resolve())] = git_state(Path(repo))
    tmp = out / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    os.replace(tmp, out / "manifest.json")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Freeze a review packet: copy sources and write manifest.json with SHA-256 hashes, git heads "
                    "and the UTC time.",
        epilog="example:\n  make_packet.py reviews/r1/packet proposal=rollout/F/w1 manuscript=../manuscript "
               "SPINE-NATURAL.md=spine/SPINE-NATURAL.md SPINE.md=spine/SPINE.md --repo ../manuscript "
               "--exclude 'prompt*.md'",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", help="packet directory to create")
    ap.add_argument("sources", nargs="+", metavar="[DEST=]PATH", help="file, directory or quoted glob")
    ap.add_argument("--repo", action="append", default=[], help="repository whose HEAD to record (repeat)")
    ap.add_argument("--exclude", action="append", default=[], help="glob of names or relative paths to skip")
    ap.add_argument("--note", help="free text stored in the manifest (e.g. section and round)")
    ap.add_argument("--force", action="store_true", help="replace an existing packet")
    a = ap.parse_args(argv)
    try:
        m = freeze(Path(a.out), [split_spec(s) for s in a.sources], a.repo, a.exclude, a.note, a.force)
    except (PacketError, OSError) as e:
        print(f"make_packet: error: {e}", file=sys.stderr)
        return 2
    heads = ", ".join(f"{Path(r).name}@{(v.get('head') or 'none')[:7]}" for r, v in m["repos"].items())
    print(f"make_packet: {a.out}: {len(m['files'])} files frozen" + (f"; repos {heads}" if heads else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
