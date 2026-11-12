#!/usr/bin/env python3
"""Collect the REQUESTS.md files that section writers left in a rollout workdir and deliver the accepted ones to the
INBOX.md of the section that owns them (rollout.py appends a unit's INBOX.md to its next writer prompt).

A request asks another section to state and prove a result the requesting section needs. Its format is the
REQUESTS.template.md asset: one "## <id>" block per request with "- To:", "- Needed by:", "- Statement:", "- Lean:"
and "- Why ...:" lines (a field may continue on the following lines); a file whose text is "None." has no requests.

Without --deliver the script only lists the requests (the editor decides which to accept); --deliver appends the
new ones (or only those named with --select) to <workdir>/<To>/INBOX.md, creating the unit's directory if it does
not exist yet. Each delivered request carries a marker with a hash of its text, so running the script again never
delivers it twice.

Unit keys: with --config, the units of that rollout config (its 'extends' chain resolved by the loader of
writing-workflow's rollout.py, found next to this skill or named by ENSLOP_ROLLOUT), so that a section that has not
run yet can receive requests in its inbox. Without --config, the directories that exist in WORKDIR: a request to a
unit without a directory is then reported as an unknown unit.

Usage:
  route_requests.py WORKDIR [--config CONFIG.json] [--stage NAME] [--deliver] [--select ID]...
Output: one line per request (id, from, to, status, statement), then a summary.
Exit status: 0 ok; 1 a request names an unknown unit or lacks To or Statement; 2 usage or input error.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import re
import sys
from pathlib import Path

FIELD = re.compile(r"^\s*[-*]\s*([A-Za-z][A-Za-z ]{0,40}?)\s*:\s*(.*)$")
ROLLOUT = Path(__file__).resolve().parents[2] / "writing-workflow" / "scripts" / "rollout.py"


class InputError(ValueError):
    pass


def config_units(config: str) -> list[str]:
    """The unit keys of a rollout config, read with rollout.py's own loader (relative paths, 'extends')."""
    driver = Path(os.environ.get("ENSLOP_ROLLOUT") or ROLLOUT)
    if not driver.is_file():
        raise InputError(f"--config needs rollout.py of writing-workflow, not found at {driver} (set ENSLOP_ROLLOUT)")
    sys.dont_write_bytecode = True          # no __pycache__ inside an installed skill
    spec = importlib.util.spec_from_file_location("enslop_rollout", driver)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        cfg = module.load_config(Path(config))
    except module.ConfigError as e:
        raise InputError(str(e)) from None
    units = cfg.get("units")
    if not isinstance(units, dict) or not units:
        raise InputError(f"{config}: the config (with what it extends) has no units")
    return list(units)


def parse(text: str) -> list[dict]:
    if text.strip().rstrip(".").lower() in ("none", ""):
        return []
    reqs, cur, field = [], None, None
    for line in text.splitlines():
        h = re.match(r"^##\s+(\S+)", line)
        if h:
            cur, field = {"rid": h.group(1), "fields": {}}, None
            reqs.append(cur)
            continue
        if cur is None:
            continue
        m = FIELD.match(line)
        if m:
            field = m.group(1).strip().lower()
            cur["fields"][field] = m.group(2).strip()
        elif field and line.strip():
            cur["fields"][field] += "\n" + line.rstrip()
    return reqs


def get(fields: dict, name: str) -> str:
    """The field called `name`, else the first field whose name starts with it ("needed" -> "needed by")."""
    if name in fields:
        return fields[name]
    return next((v for k, v in fields.items() if k.startswith(name)), "")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="List the REQUESTS.md files of a rollout workdir and deliver accepted requests to the owning "
                    "unit's INBOX.md.",
        epilog="examples:\n"
               "  route_requests.py rollout/ --config rollout/section-cycle.json --stage w1\n"
               "      list the requests made in stage w1; the unit keys come from the config\n"
               "  route_requests.py rollout/ --config rollout/section-cycle.json --stage w1 --deliver --select D/w1/R2\n"
               "      deliver one of them to its owner's INBOX.md",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir", help="rollout workdir (one directory per unit)")
    ap.add_argument("--config", metavar="CONFIG.json",
                    help="rollout config whose units are the valid addresses (default: the directories of WORKDIR)")
    ap.add_argument("--stage", help="stage whose REQUESTS.md to read (default: the newest per unit)")
    ap.add_argument("--deliver", action="store_true", help="append new requests to the owners' INBOX.md")
    ap.add_argument("--select", action="append", default=[], help="deliver only these request ids (repeat)")
    a = ap.parse_args(argv)
    wd = Path(a.workdir)
    if not wd.is_dir():
        print(f"route_requests: error: {wd} is not a directory", file=sys.stderr)
        return 2
    dirs = sorted(p.name for p in wd.iterdir() if p.is_dir() and not p.name.startswith("."))
    if a.config:
        try:
            units = config_units(a.config)
        except InputError as e:
            print(f"route_requests: error: {e}", file=sys.stderr)
            return 2
    else:
        units = dirs
        print("route_requests: no --config: the unit keys are the directories of WORKDIR, so a unit that has not "
              "run yet cannot receive a request; pass --config CONFIG.json to take them from the rollout config",
              file=sys.stderr)
    source = Path(a.config).name if a.config else "the directories"
    found = []
    for u in dirs:
        files = [wd / u / a.stage / "REQUESTS.md"] if a.stage else sorted(
            (wd / u).glob("*/REQUESTS.md"), key=lambda p: p.stat().st_mtime)[-1:]
        for f in files:
            if f.is_file():
                for r in parse(f.read_text(encoding="utf-8")):
                    found.append((u, f.parent.name, r))
    bad = delivered = 0
    for u, stage, r in found:
        f = r["fields"]
        to, statement = get(f, "to").strip(), get(f, "statement").strip()
        rid = f"{u}/{stage}/{r['rid']}"
        digest = hashlib.sha256(re.sub(r"\s+", " ", f"{to}|{statement}").encode()).hexdigest()[:12]
        marker = f"<!-- request {digest} -->"
        if not to or not statement:
            status = "INCOMPLETE (needs To and Statement)"
            bad += 1
        elif to not in units:
            status = f"UNKNOWN UNIT {to!r} ({'not a unit of ' + source if a.config else 'no directory in WORKDIR'})"
            bad += 1
        else:
            seen = "".join((wd / to / n).read_text(encoding="utf-8") for n in ("INBOX.md", "inbox-archive.md")
                           if (wd / to / n).is_file())
            if marker in seen:
                status = "delivered earlier"
            elif a.deliver and (not a.select or rid in a.select):
                block = [f"## Request {rid} {marker}",
                         f"From section {u} (stage {stage}); needed by: {get(f, 'needed') or 'not stated'}.",
                         f"Statement: {statement}", f"Lean: {get(f, 'lean') or 'not stated'}",
                         f"Why no existing statement serves: {get(f, 'why') or 'not stated'}",
                         "Answer it in your response table: prove it here, point to the existing statement that "
                         "says it, or decline with a mathematical reason.", ""]
                (wd / to).mkdir(parents=True, exist_ok=True)
                with open(wd / to / "INBOX.md", "a", encoding="utf-8") as out:
                    out.write("\n".join(block) + "\n")
                status = "DELIVERED"
                delivered += 1
            else:
                status = "new"
        short = re.sub(r"\s+", " ", statement)[:70]
        print(f"{rid}\t{u} -> {to or '?'}\t{status}\t{short}")
    print(f"route_requests: {len(found)} request(s) in {len(dirs)} unit(s) with a directory; {len(units)} unit "
          f"key(s) from {source}; {delivered} delivered; {bad} with problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
