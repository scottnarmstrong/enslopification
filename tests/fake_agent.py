#!/usr/bin/env python3
"""A stand-in agent CLI for the smoke tests: reads a prompt on stdin and behaves like a writer or a reviewer.

It never calls a model. Its behaviour is decided by the environment that agent_cli.py and rollout.py give every job
(ENSLOP_UNIT, ENSLOP_STAGE, ENSLOP_JOB, ENSLOP_EXPECT, ENSLOP_REPORT, ENSLOP_ATTEMPT) and by fault-injection
variables. Each is a comma-separated list of glob patterns over the job id "UNIT/STAGE/JOB":

  FAKE_FAIL_ONCE      exit 1 without output the first time a matching job runs (state kept in FAKE_STATE)
  FAKE_QUOTA          print a usage-limit message and exit 1
  FAKE_SHORT          print a report that is too short
  FAKE_NOT_YET        verdict NOT YET (default: DELIVER for jobs whose name starts with "delivery", else PASS)
  FAKE_VERDICT        PATTERN=TEXT: the verdict text for matching jobs (TEXT without commas)
  FAKE_OVERRUN_ONCE   write a standalone PDF and .tex files far over any allowance (40 pages), unless the prompt
                      quotes a failed check
  FAKE_BAD_TEX_ONCE   write .tex files with an undefined command (a LaTeX error), unless the prompt quotes a failed
                      check
  FAKE_SLEEP          PATTERN=SECONDS: sleep before answering
  FAKE_WRITE_OUTSIDE  PATTERN=PATH: also append to PATH (to test protect)
  FAKE_TEX            PATTERN=PATH: write every .tex deliverable as a copy of PATH
  FAKE_READONLY=1     refuse the WRITE step of a preflight (behave like a read-only reviewer)
  FAKE_PAGES          pages of the PDFs it writes (default 5)
  FAKE_LOG            file that gets one line per call: UNIT STAGE JOB attempt=N
  FAKE_STATE          directory for the once-only state

Writer mode (no ENSLOP_REPORT): writes every file listed in ENSLOP_EXPECT: a .pdf as a minimal PDF with a LaTeX
log next to it, a .tsv with a header row, a .tex with a section that compiles to as many pages as the PDF has (or
the file FAKE_TEX names), anything else as Markdown.
Reviewer mode: prints a report of about 2,600 characters with "Sources consulted:" and a verdict line last.
A preflight prompt (READ / RUN / WRITE lines) is carried out literally.

Usage: fake_agent.py [--mode auto|write|report] < prompt
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def job_id() -> str:
    e = os.environ
    return f"{e.get('ENSLOP_UNIT', '-')}/{e.get('ENSLOP_STAGE', '-')}/{e.get('ENSLOP_JOB', '-')}"


def matches(var: str) -> str | None:
    """Return the value part ('' if none) of the first pattern in $var matching this job, else None."""
    for item in filter(None, (x.strip() for x in os.environ.get(var, "").split(","))):
        pat, _, value = item.partition("=")
        if fnmatch.fnmatch(job_id(), pat):
            return value
    return None


def minimal_pdf(path: Path, pages: int) -> None:
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            "<< /Type /Pages /Kids [" + " ".join(f"{3 + i} 0 R" for i in range(pages)) + f"] /Count {pages} >>"]
    objs += ["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"] * pages
    out, offsets = bytearray(b"%PDF-1.4\n"), []
    for n, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n{body}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(out))
    path.with_suffix(".log").write_text(f"Output written on {path.name} ({pages} pages, {len(out)} bytes).\n")


def preflight(prompt: str) -> int:
    for line in prompt.splitlines():
        m = re.match(r"(READ|RUN|WRITE) (\w+) (.+)$", line.strip())
        if not m:
            continue
        kind, sid, arg = m.groups()
        if kind == "READ":
            try:
                first = next((x.strip() for x in Path(arg).read_text().splitlines() if x.strip()), "")
            except OSError as e:
                first = f"cannot read: {e}"
            print(f"<<<{sid}\n{first}\n{sid}>>>")
        elif kind == "RUN":
            r = subprocess.run(arg, shell=True, capture_output=True, text=True)
            print(f"<<<{sid}\n{r.stdout.strip()}\n{sid}>>>")
        else:
            if os.environ.get("FAKE_READONLY") == "1":
                print(f"{sid} refused: read-only")
            else:
                Path(arg).write_text("ok\n")
                print(f"{sid} attempted")
    print("PREFLIGHT-END")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Stand-in agent CLI for tests (reads the prompt on stdin).")
    ap.add_argument("--mode", choices=["auto", "write", "report"], default="auto")
    a = ap.parse_args()
    prompt = sys.stdin.read()
    if os.environ.get("FAKE_LOG"):
        with open(os.environ["FAKE_LOG"], "a") as f:
            f.write(f"{job_id().replace('/', ' ')} attempt={os.environ.get('ENSLOP_ATTEMPT', '?')}\n")
    if "PREFLIGHT TEST" in prompt:
        return preflight(prompt)
    sleep = matches("FAKE_SLEEP")
    if sleep:
        time.sleep(float(sleep))
    if matches("FAKE_QUOTA") is not None:
        print("Working...\nYou've hit your usage limit. Try again later.")
        return 1
    if matches("FAKE_FAIL_ONCE") is not None:
        state = Path(os.environ.get("FAKE_STATE", "."))
        marker = state / ("failed-" + re.sub(r"[^A-Za-z0-9_.-]", "_", job_id()))
        if not marker.exists():
            state.mkdir(parents=True, exist_ok=True)
            marker.write_text("1")
            print("simulated failure", file=sys.stderr)
            return 1
    outside = matches("FAKE_WRITE_OUTSIDE")
    if outside:
        with open(outside, "a") as f:
            f.write("% written by a stand-in writer outside its directory\n")
    report_mode = a.mode == "report" or (a.mode == "auto" and os.environ.get("ENSLOP_REPORT"))
    if not report_mode:
        pages = int(os.environ.get("FAKE_PAGES", "5"))
        if matches("FAKE_OVERRUN_ONCE") is not None and "The check failed" not in prompt:
            pages = 40
        bad_tex = matches("FAKE_BAD_TEX_ONCE") is not None and "The check failed" not in prompt
        written = 0
        for name in json.loads(os.environ.get("ENSLOP_EXPECT", "[]")):
            p = Path(name)
            p.parent.mkdir(parents=True, exist_ok=True)
            if p.suffix == ".pdf":
                minimal_pdf(p, pages)
            elif p.suffix == ".tsv":
                p.write_text("finding\tdecision\tedit\tcheck\nmath-1\tapplied\tfake edit\tre-read\n")
            elif p.suffix == ".tex":
                src = matches("FAKE_TEX")
                p.write_text((Path(src).read_text() if src else
                              "\\section{A section written for a test}\nThis text was written by a stand-in agent.\n"
                              + "\\newpage\\null\n" * (pages - 1))
                             + ("\\undefinedcommandofthestandin\n" if bad_tex else ""))
            else:
                p.write_text(f"# {p.name}\n\nWritten by the stand-in agent for {job_id()}.\n")
            written += 1
        print(f"fake writer {job_id()}: wrote {written} file(s)")
        return 0
    if matches("FAKE_SHORT") is not None:
        print("Too short.")
        return 0
    job = os.environ.get("ENSLOP_JOB", "")
    verdict = "NOT YET" if matches("FAKE_NOT_YET") is not None else (
        matches("FAKE_VERDICT") or ("DELIVER" if job.startswith("delivery") else "PASS"))
    body = [f"# Report of the stand-in reviewer for {job_id()}", "",
            "Sources consulted: the frozen packet (manifest hashes checked); no other source was opened.", ""]
    body += [f"- Finding {i}: MINOR, location quoted, evidence given, exact repair proposed." for i in range(1, 41)]
    body += ["", "What this review does not establish: anything about the Lean; this is a test double.", "",
             f"**Verdict: {verdict}**"]
    print("\n".join(body))
    return 0


if __name__ == "__main__":
    sys.exit(main())
