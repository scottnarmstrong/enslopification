#!/usr/bin/env python3
"""Check a frozen review packet against its manifest.json (written by make_packet.py).

Three checks, each optional except the first:
  (default)   the packet's own copies: every listed file present with its recorded SHA-256; files added later;
  --sources   the originals the packet was frozen from: changed or missing since the freeze (does the review
              still describe the current text?);
  --repos     the recorded repositories: HEAD moved since the freeze.

Usage:
  verify_packet.py PACKET [--sources] [--repos] [--quiet]
Output: one line per mismatch (CHANGED, MISSING, EXTRA, SOURCE-CHANGED, SOURCE-MISSING, HEAD-MOVED), then a summary.
Exit status: 0 everything matches, 1 a mismatch, 2 usage or input error (no manifest).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify(packet: Path, sources: bool = False, repos: bool = False) -> list[str]:
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    listed = manifest.get("files", {})
    for rel, digest in sorted(listed.items()):
        f = packet / rel
        if not f.is_file():
            problems.append(f"MISSING         {rel}")
        elif sha256(f) != digest:
            problems.append(f"CHANGED         {rel}")
    for root, _dirs, files in os.walk(packet):
        for name in files:
            rel = os.path.relpath(os.path.join(root, name), packet)
            if rel not in listed and rel != "manifest.json":
                problems.append(f"EXTRA           {rel}")
    if sources:
        for rel, src in sorted(manifest.get("sources", {}).items()):
            s = Path(src)
            if not s.is_file():
                problems.append(f"SOURCE-MISSING  {rel} <- {src}")
            elif sha256(s) != listed.get(rel):
                problems.append(f"SOURCE-CHANGED  {rel} <- {src}")
    if repos:
        env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
        for repo, state in sorted(manifest.get("repos", {}).items()):
            r = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env)
            now = r.stdout.strip() if r.returncode == 0 else None
            if now != state.get("head"):
                problems.append(f"HEAD-MOVED      {repo}: {state.get('head')} -> {now}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Re-hash a frozen review packet (and optionally its sources and repositories) against its "
                    "manifest.",
        epilog="example:\n  verify_packet.py rollout/F/r1/packet --sources --repos",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("packet", help="packet directory containing manifest.json")
    ap.add_argument("--sources", action="store_true", help="also re-hash the original files")
    ap.add_argument("--repos", action="store_true", help="also compare the repositories' HEADs")
    ap.add_argument("--quiet", action="store_true", help="print only the summary line")
    a = ap.parse_args(argv)
    packet = Path(a.packet)
    if not (packet / "manifest.json").is_file():
        print(f"verify_packet: error: {packet}/manifest.json not found", file=sys.stderr)
        return 2
    try:
        problems = verify(packet, a.sources, a.repos)
    except (OSError, json.JSONDecodeError) as e:
        print(f"verify_packet: error: {e}", file=sys.stderr)
        return 2
    if not a.quiet:
        for p in problems:
            print(p)
    n = len(json.loads((packet / "manifest.json").read_text(encoding="utf-8")).get("files", {}))
    print(f"verify_packet: {packet}: {n} files, {len(problems)} mismatch(es)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
