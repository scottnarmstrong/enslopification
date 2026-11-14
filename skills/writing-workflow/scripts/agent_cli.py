#!/usr/bin/env python3
"""Run one agent job through a command-line agent (the Codex CLI, Claude Code, or any CLI that reads a prompt).

This is the shared agent layer of the enslopification skills: rollout.py imports it, and it runs single jobs from
the command line. A job sends a rendered prompt to an agent *profile*, waits, retries once on failure, stops
without retrying when the output carries a quota or rate-limit message, and checks the deliverables:

  report mode (profile "stdout": "report")  the agent prints its deliverable; stdout is saved as the report, so a
                                            read-only reviewer never needs write permission; the report must have
                                            at least min_chars characters and, if required, a line matching a regex
  log mode    (profile "stdout": "log")     the agent writes files; stdout is a log; expected files must exist

Optional protect paths are hashed before and after the job; any change fails the job loudly, without a retry.
The agent runs in its own process group with stdout going to a file, so a job survives the death of its driver;
a restarted driver adopts it (waits for it and checks its outputs) instead of starting a second copy.

Placeholders are {{name}} (never Python str.format: prompts contain LaTeX braces). Unknown names are an error.
Write {{{{ for a literal {{. In an argv element that is exactly one placeholder, a list value expands to several
arguments. Profile fields and the rollout config: references/driver.md of the writing-workflow skill.

Exit status: 0 ok; 1 the job failed (including quota and protect stops; the summary line says which); 2 usage or
input error.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping

PLACEHOLDER = re.compile(r"\{\{\{\{|\{\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}\}")
WHOLE_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*\}\}")
DEFAULT_FAIL_PATTERNS = ["usage limit", "rate limit", "rate_limit", "quota exceeded", "insufficient_quota",
                         "you've hit your"]
DEFAULT_PROTECT_EXCLUDE = [".git", ".lake", "__pycache__"]
PROFILE_FIELDS = {"argv", "model", "effort", "family", "stdin", "stdout", "timeout_s", "retries", "fail_patterns",
                  "fail_scan_chars", "fail_max_chars", "min_chars", "env", "vars", "strip_lines", "extends", "description"}
HASH_LIMIT = 64 * 1024 * 1024        # larger protected files are fingerprinted by size and mtime only
WRAPPER = '"$@"; rc=$?; echo "$rc" > "$ENSLOP_EXIT_FILE"; exit "$rc"'
POLL_S = 5


class TemplateError(ValueError):
    """A template uses an unknown placeholder, or an agent profile is malformed."""


# ----------------------------------------------------------------------------------------------- rendering

Lookup = Callable[[str], Any]


def _lookup(variables: Mapping[str, Any] | Lookup) -> Lookup:
    if callable(variables):
        return variables
    return lambda name: variables[name]


def format_value(value: Any) -> str:
    """Render a variable value as text: lists are joined with ', ', booleans are true/false, None is empty."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return ", ".join(format_value(v) for v in value)
    return str(value)


def render(text: str, variables: Mapping[str, Any] | Lookup, where: str = "template") -> str:
    """Replace every {{name}}; leave every other brace alone; {{{{ gives a literal {{."""
    get = _lookup(variables)
    missing: list[str] = []

    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name is None:
            return "{{"
        try:
            return format_value(get(name))
        except KeyError:
            missing.append(name)
            return m.group(0)

    out = PLACEHOLDER.sub(sub, text)
    if missing:
        names = ", ".join("{{%s}}" % n for n in sorted(set(missing)))
        raise TemplateError(f"{where}: unknown placeholder(s) {names}")
    return out


def render_list(items: list[str], variables: Mapping[str, Any] | Lookup, where: str = "list") -> list[str]:
    """Render each item; an item that is exactly one placeholder with a list value expands to several items."""
    get = _lookup(variables)
    out: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise TemplateError(f"{where}: expected strings, got {item!r}")
        m = WHOLE_PLACEHOLDER.fullmatch(item)
        if m:
            try:
                value = get(m.group(1))
            except KeyError:
                raise TemplateError(f"{where}: unknown placeholder {{{{{m.group(1)}}}}}") from None
            if isinstance(value, (list, tuple)):
                out.extend(render(format_value(v), variables, where) for v in value)
                continue
        out.append(render(item, variables, where))
    return out


def placeholders_in(text: str) -> set[str]:
    return {m.group(1) for m in PLACEHOLDER.finditer(text) if m.group(1)}


# ----------------------------------------------------------------------------------------------- profiles

def load_profiles(source: str | os.PathLike | Mapping) -> dict[str, dict]:
    """Load agent profiles (a JSON file or a mapping); resolve "extends"; validate. Keys starting with _ are notes."""
    if isinstance(source, Mapping):
        raw = dict(source)
    else:
        try:
            raw = json.loads(Path(source).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise TemplateError(f"agent profiles {source}: {e}") from None
    if not isinstance(raw, dict):
        raise TemplateError("agent profiles: expected a JSON object of profiles")
    profiles = {k: v for k, v in raw.items() if not k.startswith("_")}
    resolved: dict[str, dict] = {}

    def resolve(name: str, chain: tuple[str, ...] = ()) -> dict:
        if name in resolved:
            return resolved[name]
        if name not in profiles:
            via = f" (extended by {chain[-1]!r})" if chain else ""
            raise TemplateError(f"unknown agent profile {name!r}{via}")
        if name in chain:
            raise TemplateError("profile inheritance cycle: " + " -> ".join(chain + (name,)))
        own = profiles[name]
        if not isinstance(own, dict):
            raise TemplateError(f"profile {name!r}: expected an object")
        own = {k: v for k, v in own.items() if not k.startswith("_")}
        base = dict(resolve(own["extends"], chain + (name,))) if "extends" in own else {}
        merged = {**base, **{k: v for k, v in own.items() if k != "extends"}}
        for key in ("vars", "env"):
            if isinstance(base.get(key), dict) and isinstance(own.get(key), dict):
                merged[key] = {**base[key], **own[key]}
        resolved[name] = merged
        return merged

    for name in profiles:
        resolve(name)
    for name, p in resolved.items():
        _validate_profile(name, p)
    return resolved


def _validate_profile(name: str, p: dict) -> None:
    unknown = set(p) - PROFILE_FIELDS
    if unknown:
        raise TemplateError(f"profile {name!r}: unknown field(s) {sorted(unknown)} (custom values go in \"vars\")")
    argv = p.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise TemplateError(f"profile {name!r}: argv must be a non-empty list of strings")
    if p.get("stdin", "prompt") not in ("prompt", "none"):
        raise TemplateError(f"profile {name!r}: stdin must be 'prompt' or 'none'")
    if p.get("stdout", "log") not in ("report", "log"):
        raise TemplateError(f"profile {name!r}: stdout must be 'report' or 'log'")
    for key in ("timeout_s", "retries", "min_chars", "fail_scan_chars", "fail_max_chars"):
        if key in p and (not isinstance(p[key], int) or p[key] < 0):
            raise TemplateError(f"profile {name!r}: {key} must be a non-negative integer")
    for key in ("fail_patterns", "strip_lines"):
        if key in p and (not isinstance(p[key], list) or not all(isinstance(x, str) for x in p[key])):
            raise TemplateError(f"profile {name!r}: {key} must be a list of strings")
    for key in ("env", "vars"):
        if key in p and not isinstance(p[key], dict):
            raise TemplateError(f"profile {name!r}: {key} must be an object")


# ----------------------------------------------------------------------------------------------- jobs

@dataclass
class Job:
    """One agent run. Paths should be absolute. For report-mode profiles, `report` is required."""
    profile: dict
    prompt_file: Path
    cwd: Path
    log: Path
    report: Path | None = None
    variables: Mapping[str, Any] | Lookup = field(default_factory=dict)
    expect: list[Path] = field(default_factory=list)
    min_chars: int | None = None
    require: str | None = None
    protect: list[Path] = field(default_factory=list)
    protect_exclude: list[str] = field(default_factory=lambda: list(DEFAULT_PROTECT_EXCLUDE))
    env: dict[str, str] = field(default_factory=dict)
    name: str = "job"

    @property
    def report_mode(self) -> bool:
        return self.profile.get("stdout", "log") == "report"

    def state(self, suffix: str) -> Path:
        base = self.log.with_suffix("") if self.log.suffix == ".log" else self.log
        return base.with_name(base.name + suffix)

    @property
    def partial(self) -> Path:
        assert self.report is not None
        return self.report.with_name(self.report.name + ".partial")


@dataclass
class Result:
    status: str                      # ok | failed | quota | protect | dry-run
    attempts: int = 0
    returncode: int | None = None
    message: str = ""
    adopted: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "ok"


def build_command(job: Job) -> tuple[list[str], dict[str, str]]:
    """Render the profile's argv and env. Job variables override profile vars; model, effort, family, cwd and
    prompt_file come from the profile and the job."""
    p = job.profile
    get = _lookup(job.variables)
    fixed = {k: p[k] for k in ("model", "effort", "family") if k in p}
    fixed.update(cwd=str(job.cwd), prompt_file=str(job.prompt_file))
    cache: dict[str, Any] = {}

    def lookup(name: str) -> Any:
        if name in fixed:
            return fixed[name]
        try:
            return get(name)
        except KeyError:
            pass
        pvars = p.get("vars") or {}
        if name in pvars:
            if name not in cache:
                v = pvars[name]
                cache[name] = render_list(v, lookup, f"profile var {name}") if isinstance(v, list) \
                    else render(str(v), lookup, f"profile var {name}")
            return cache[name]
        raise KeyError(name)

    argv = render_list(p["argv"], lookup, "profile argv")
    env = {k: render(str(v), lookup, f"profile env {k}") for k, v in (p.get("env") or {}).items()}
    return argv, env


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    try:                                  # a zombie is not alive
        with open(f"/proc/{pid}/stat", encoding="ascii") as f:
            return f.read().split(") ", 1)[1][:1] != "Z"
    except (OSError, IndexError):
        return True


def pending(job: Job) -> bool:
    """True if a previous driver started this job and did not record its end (it may still be running)."""
    return job.state(".running").exists()


def snapshot(paths: list[Path], exclude: list[str]) -> dict[str, str]:
    """Fingerprint every file under the protected paths: SHA-256, or size and mtime for very large files."""
    out: dict[str, str] = {}

    def skip(name: str) -> bool:
        return any(fnmatch.fnmatch(name, pat) for pat in exclude)

    def add(f: Path) -> None:
        try:
            st = f.stat()
            if st.st_size > HASH_LIMIT:
                out[str(f)] = f"size={st.st_size} mtime={st.st_mtime_ns}"
            else:
                out[str(f)] = hashlib.sha256(f.read_bytes()).hexdigest()
        except OSError as e:
            out[str(f)] = f"unreadable: {e.__class__.__name__}"

    for p in paths:
        p = Path(p)
        if p.is_file():
            add(p)
        elif p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if not skip(d))
                for name in sorted(files):
                    if not skip(name):
                        add(Path(root) / name)
        else:
            out[str(p)] = "absent"
    return out


def _diff(before: dict[str, str], after: dict[str, str]) -> list[str]:
    lines = []
    for k in sorted(set(before) | set(after)):
        if k not in after:
            lines.append(f"REMOVED  {k}")
        elif k not in before:
            lines.append(f"ADDED    {k}")
        elif before[k] != after[k]:
            lines.append(f"CHANGED  {k}")
    return lines


ATTEMPT_HEADER = re.compile(r"\n=== \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ attempt \d+: [^\n]*\n")


def _attempt_tail(path: Path, n: int) -> str:
    """The last n characters written to the log by the current attempt, after its header line (earlier attempts,
    for example one that stopped at a quota limit, must not count against this one)."""
    text = _tail(path, max(n, 2 * 1024 * 1024))
    last = None
    for last in ATTEMPT_HEADER.finditer(text):
        pass
    if last is not None:
        text = text[last.end():]
    return text[-n:]


def _tail(path: Path, n: int) -> str:
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - n))
            return f.read().decode("utf-8", errors="replace")
    except OSError:
        return ""


def match_fail_pattern(texts: list[str], patterns: list[str]) -> str | None:
    """Return the first quota/rate-limit pattern found; 're:' prefixes a regex, else a case-insensitive substring."""
    for pat in patterns:
        for text in texts:
            if pat.startswith("re:"):
                if re.search(pat[3:], text, re.IGNORECASE | re.MULTILINE):
                    return pat
            elif pat.lower() in text.lower():
                return pat
    return None


def _write_json(path: Path, data: Any) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _launch(job: Job, argv: list[str], env_extra: dict[str, str], attempt: int) -> subprocess.Popen:
    exit_file = job.state(".exit")
    exit_file.unlink(missing_ok=True)
    env = os.environ.copy()
    env.update(env_extra)
    env.update(job.env)
    env.update(ENSLOP_EXIT_FILE=str(exit_file), ENSLOP_ATTEMPT=str(attempt))
    job.log.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(job.log, "ab") as log:
        log.write(f"\n=== {stamp} attempt {attempt}: {shlex.join(argv)}\n".encode())
    log_f = open(job.log, "ab")
    out_f = open(job.partial, "wb") if job.report_mode else log_f
    in_f = open(job.prompt_file, "rb") if job.profile.get("stdin", "prompt") == "prompt" else subprocess.DEVNULL
    try:
        proc = subprocess.Popen(["/bin/sh", "-c", WRAPPER, "enslop-agent", *argv], stdin=in_f, stdout=out_f,
                                stderr=log_f, cwd=str(job.cwd), env=env, start_new_session=True)
    finally:
        for f in {id(log_f): log_f, id(out_f): out_f}.values():
            f.close()
        if in_f is not subprocess.DEVNULL:
            in_f.close()
    _write_json(job.state(".running"), {"pid": proc.pid, "started": time.time(), "attempt": attempt,
                                         "argv0": argv[0]})
    return proc


def _kill_group(pid: int) -> None:
    for sig, wait in ((signal.SIGTERM, 15), (signal.SIGKILL, 5)):
        try:
            os.killpg(pid, sig)
        except (ProcessLookupError, PermissionError):
            return
        end = time.time() + wait
        while time.time() < end and _pid_alive(pid):
            time.sleep(0.5)


def _wait(job: Job, proc: subprocess.Popen | None, pid: int, started: float) -> bool:
    """Wait for the job to end; kill its process group at the timeout. Return True if it timed out."""
    timeout = job.profile.get("timeout_s", 14400)
    if proc is not None:
        try:
            proc.wait(timeout=max(1.0, started + timeout - time.time()))
            return False
        except subprocess.TimeoutExpired:
            _kill_group(pid)
            proc.wait()
            return True
    while _pid_alive(pid):
        if time.time() > started + timeout:
            _kill_group(pid)
            return True
        time.sleep(POLL_S)
    return False


def _finish(job: Job, timed_out: bool) -> int | None:
    rc_file = job.state(".exit")
    rc: int | None = None
    if rc_file.exists():
        try:
            rc = int(rc_file.read_text().strip())
        except ValueError:
            rc = None
    job.state(".running").unlink(missing_ok=True)
    return rc


def _evaluate(job: Job, rc: int | None, timed_out: bool, before: dict[str, str] | None) -> Result:
    p = job.profile
    if job.protect:
        after = snapshot(job.protect, job.protect_exclude)
        changes = _diff(before or {}, after)
        if changes:
            report = job.state(".protect.txt")
            report.write_text("Protected paths changed while this job ran (by this job or by another process):\n"
                              + "\n".join(changes) + "\n", encoding="utf-8")
            return Result("protect", returncode=rc,
                          message=f"{len(changes)} protected file(s) changed; see {report}")
    scan = p.get("fail_scan_chars", 4000)
    texts = [_attempt_tail(job.log, scan)] + ([_tail(job.partial, scan)] if job.report_mode else [])
    if rc == 0:
        # A run that exited cleanly is a quota stop only if its output is the short limit message itself, not a
        # report or summary that merely mentions a limit.
        out = texts[-1]
        texts = [out] if len(out.strip()) <= p.get("fail_max_chars", 1000) else []
    hit = match_fail_pattern(texts, p.get("fail_patterns", DEFAULT_FAIL_PATTERNS))
    if hit:
        return Result("quota", returncode=rc, message=f"output matches {hit!r}; not retried")
    if timed_out:
        return Result("failed", returncode=rc, message=f"timeout after {p.get('timeout_s', 14400)} s")
    if rc is None:
        return Result("failed", message="interrupted: no exit status was recorded")
    if rc != 0:
        return Result("failed", returncode=rc, message=f"exit status {rc}")
    if job.report_mode:
        assert job.report is not None
        try:
            text = job.partial.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        strip = [re.compile(s) for s in p.get("strip_lines", [])]
        if strip:
            text = "".join(line for line in text.splitlines(keepends=True) if not any(r.search(line) for r in strip))
        need = max(1, job.min_chars if job.min_chars is not None else p.get("min_chars", 0))
        problem = None
        if len(text.strip()) < need:
            problem = f"report has {len(text.strip())} characters, at least {need} required"
        elif job.require and not re.search(job.require, text, re.MULTILINE):
            problem = f"report has no line matching {job.require!r}"
        if problem:
            if job.partial.exists():
                os.replace(job.partial, job.report.with_name(job.report.name + ".rejected"))
            return Result("failed", returncode=rc, message=problem)
        tmp = job.report.with_name(job.report.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, job.report)
        job.partial.unlink(missing_ok=True)
    missing = [str(f) for f in job.expect if not f.exists() or (f.is_file() and f.stat().st_size == 0)]
    if missing:
        return Result("failed", returncode=rc, message="missing or empty deliverable(s): " + ", ".join(missing))
    return Result("ok", returncode=0)


def _load_before(job: Job) -> dict[str, str] | None:
    try:
        return json.loads(job.state(".protect.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def run_job(job: Job, dry_run: bool = False, note: Callable[[str], None] | None = None) -> Result:
    """Run the job: adopt a previous run if one is pending, else launch; retry once (profile "retries") on
    failure; never retry after a quota message or a protect violation."""
    note = note or (lambda msg: None)
    if job.report_mode and job.report is None:
        raise TemplateError(f"{job.name}: the profile prints a report (stdout: report) but no report path was given")
    argv, env_extra = build_command(job)
    if dry_run:
        return Result("dry-run", message=shlex.join(argv))
    retries = job.profile.get("retries", 1)
    attempts = 0
    result = Result("failed", message="not run")
    if pending(job):
        info = {}
        try:
            info = json.loads(job.state(".running").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
        pid = int(info.get("pid", 0) or 0)
        if pid and _pid_alive(pid):
            note(f"adopting running job (pid {pid})")
            timed_out = _wait(job, None, pid, float(info.get("started", time.time())))
        else:
            timed_out = False
        rc = _finish(job, timed_out)
        before = _load_before(job) if job.protect else None
        if job.protect and before is None:
            before = snapshot(job.protect, job.protect_exclude)
        attempts = 1
        result = _evaluate(job, rc, timed_out, before)
        result.attempts, result.adopted = attempts, True
        if result.status in ("ok", "quota", "protect"):
            return result
        note(f"adopted job did not succeed ({result.message})")
    while attempts < 1 + retries:
        attempts += 1
        before = None
        if job.protect:
            before = snapshot(job.protect, job.protect_exclude)
            _write_json(job.state(".protect.json"), before)
        started = time.time()
        proc = _launch(job, argv, env_extra, attempts)
        timed_out = _wait(job, proc, proc.pid, started)
        rc = _finish(job, timed_out)
        result = _evaluate(job, rc, timed_out, before)
        result.attempts = attempts
        if result.status in ("ok", "quota", "protect"):
            return result
        if attempts < 1 + retries:
            note(f"attempt {attempts} failed ({result.message}); retrying")
    return result


# ----------------------------------------------------------------------------------------------- preflight

PREFLIGHT_INTRO = """PREFLIGHT TEST of your tool permissions. Carry out each step below with your tools, exactly, and print the
results in the format asked. Do nothing else. Do not explain.

- A line "READ <id> <path>": print the first non-empty line of that file, between a line "<<<<id>" and a line "<id>>>>".
- A line "RUN <id> <command>": run that shell command and print its complete output between "<<<<id>" and "<id>>>>".
- A line "WRITE <id> <path>": try to create that file containing the word ok, then print "<id> attempted".
If a step is refused or fails, print the refusal or error between the markers instead.
End with the line PREFLIGHT-END.

"""


def preflight(profile: dict, cwd: Path, reads: list[Path], runs: list[str], write: str,
              out_dir: Path, variables: Mapping[str, Any] | None = None) -> tuple[bool, list[str]]:
    """Ask the agent to read files, run commands and (optionally) write a file; compare with the truth.
    write: 'denied' (a reviewer must not be able to write), 'allowed' (a writer must), or 'skip'."""
    nonce = uuid.uuid4().hex[:8]
    out_dir.mkdir(parents=True, exist_ok=True)
    steps, expected = [], []
    for i, f in enumerate(reads, 1):
        first = next((ln.strip() for ln in f.read_text(encoding="utf-8", errors="replace").splitlines()
                      if ln.strip()), "")
        steps.append(f"READ R{i} {f}")
        expected.append((f"R{i}", f"read {f}", first))
    for i, cmd in enumerate(runs, 1):
        r = subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            raise TemplateError(f"preflight command fails for the driver itself (exit {r.returncode}): {cmd}")
        steps.append(f"RUN C{i} {cmd}")
        expected.append((f"C{i}", f"run {cmd}", r.stdout.strip()))
    target = cwd / f"preflight-write-{nonce}.txt"
    if write != "skip":
        steps.append(f"WRITE W1 {target}")
    prompt_file = out_dir / f"preflight-{nonce}.prompt.md"
    prompt_file.write_text(PREFLIGHT_INTRO + "\n".join(steps) + "\n", encoding="utf-8")
    prof = dict(profile, stdout="report", min_chars=0, retries=0)
    job = Job(profile=prof, prompt_file=prompt_file, cwd=cwd, log=out_dir / f"preflight-{nonce}.log",
              report=out_dir / f"preflight-{nonce}.out.md", variables=variables or {}, name="preflight")
    res = run_job(job)
    lines, ok = [], res.ok
    lines.append(f"{'PASS' if res.ok else 'FAIL'}  agent run: {res.status} {res.message}".rstrip())
    text = job.report.read_text(encoding="utf-8", errors="replace") if job.report and job.report.exists() else ""
    for sid, what, want in expected:
        m = re.search(rf"<<<{sid}\s*\n(.*?)\n?\s*{sid}>>>", text, re.S)
        got = m.group(1).strip() if m else None
        good = got is not None and (want == got or (want and want in got))
        ok &= good
        shown = "no output between the markers" if got is None else repr(got[:80])
        lines.append(f"{'PASS' if good else 'FAIL'}  {what}: expected {want[:80]!r}, got {shown}")
    if write != "skip":
        exists = target.exists()
        good = exists if write == "allowed" else not exists
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  write {target.name}: {'created' if exists else 'not created'} "
                     f"(expected {'created' if write == 'allowed' else 'not created'})")
        target.unlink(missing_ok=True)
    return ok, lines


# ----------------------------------------------------------------------------------------------- command line

def _parse_vars(items: list[str]) -> dict[str, str]:
    out = {}
    for item in items:
        if "=" not in item:
            raise TemplateError(f"--var expects NAME=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        out[k.strip()] = v
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Run one agent job (writer or reviewer) from a prompt file, through an agent profile.",
        epilog="examples:\n"
               "  agent_cli.py --agents agents.json --profile reviewer --prompt review.md --out report.md "
               "--var packet=/abs/packet\n"
               "  agent_cli.py --agents agents.json --profile writer --prompt task.md --cwd proposal/ "
               "--expect section.tex --expect NOTES.md --protect /abs/manuscript\n"
               "  agent_cli.py --agents agents.json --profile reviewer --preflight --read /abs/lean/Main.lean "
               "--run \"sqlite3 -readonly graph.sqlite 'select count(*) from nodes where used = 1'\"\n"
               "  agent_cli.py --agents agents.json --list",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agents", default=os.environ.get("ENSLOP_AGENTS"),
                    help="agent profiles JSON (default: $ENSLOP_AGENTS)")
    ap.add_argument("--profile", help="profile name, e.g. writer or reviewer")
    ap.add_argument("--list", action="store_true", help="list the profiles and their commands, then exit")
    ap.add_argument("--prompt", help="prompt template file")
    ap.add_argument("--raw", action="store_true", help="send the prompt file as it is (no placeholder rendering)")
    ap.add_argument("--var", action="append", default=[], metavar="NAME=VALUE", help="template variable (repeat)")
    ap.add_argument("--cwd", default=".", help="the agent's working directory (default: .)")
    ap.add_argument("--out", help="report file (required for report-mode profiles)")
    ap.add_argument("--log", help="log file (default: OUT.log, or CWD/agent.log)")
    ap.add_argument("--expect", action="append", default=[], help="file that must exist afterwards (repeat)")
    ap.add_argument("--min-chars", type=int, help="minimum report length (default: the profile's)")
    ap.add_argument("--require", help="regex a report must match, e.g. '(?im)^\\W*verdict'")
    ap.add_argument("--protect", action="append", default=[], help="path hashed before and after (repeat)")
    ap.add_argument("--dry-run", action="store_true", help="print the command and write the prompt; run nothing")
    ap.add_argument("--preflight", action="store_true", help="test the profile's permissions instead of a job")
    ap.add_argument("--read", action="append", default=[], help="preflight: a file the agent must be able to read")
    ap.add_argument("--run", action="append", default=[], help="preflight: a command the agent must be able to run")
    ap.add_argument("--write-test", choices=["denied", "allowed", "skip"],
                    help="preflight: may the agent write in CWD? (default: denied for report profiles, else allowed)")
    a = ap.parse_args(argv)
    if not a.agents:
        ap.error("--agents is required (or set ENSLOP_AGENTS)")
    try:
        profiles = load_profiles(a.agents)
        if a.list:
            for name, p in profiles.items():
                print(f"{name}\t{p.get('stdout', 'log')}\tfamily={p.get('family', '?')}\t{shlex.join(p['argv'])}")
            print(f"agent_cli: {len(profiles)} profile(s)")
            return 0
        if not a.profile:
            ap.error("--profile is required")
        if a.profile not in profiles:
            raise TemplateError(f"unknown profile {a.profile!r}; known: {', '.join(profiles)}")
        profile = profiles[a.profile]
        cwd = Path(a.cwd).resolve()
        variables = _parse_vars(a.var)
        if a.preflight:
            write = a.write_test or ("denied" if profile.get("stdout") == "report" else "allowed")
            ok, lines = preflight(profile, cwd, [Path(r).resolve() for r in a.read], a.run, write,
                                  cwd / ".preflight", variables)
            print("\n".join(lines))
            print(f"agent_cli preflight: profile {a.profile}: {'PASS' if ok else 'FAIL'} "
                  f"({sum(1 for x in lines if x.startswith('FAIL'))} failure(s))")
            return 0 if ok else 1
        if not a.prompt:
            ap.error("--prompt is required")
        text = Path(a.prompt).read_text(encoding="utf-8")
        if not a.raw:
            text = render(text, dict(variables, cwd=str(cwd)), a.prompt)
        report = Path(a.out).resolve() if a.out else None
        if profile.get("stdout") == "report" and report is None:
            ap.error(f"profile {a.profile} prints a report: --out is required")
        log = Path(a.log).resolve() if a.log else (report.with_name(report.name + ".log") if report
                                                   else cwd / "agent.log")
        rendered = log.with_name(log.stem + ".prompt.md")
        rendered.parent.mkdir(parents=True, exist_ok=True)
        rendered.write_text(text, encoding="utf-8")
        job = Job(profile=profile, prompt_file=rendered, cwd=cwd, log=log, report=report, variables=variables,
                  expect=[(cwd / e).resolve() for e in a.expect], min_chars=a.min_chars, require=a.require,
                  protect=[Path(p).resolve() for p in a.protect], name=a.profile)
        res = run_job(job, dry_run=a.dry_run, note=lambda m: print(f"agent_cli: {m}", file=sys.stderr))
    except TemplateError as e:
        print(f"agent_cli: error: {e}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"agent_cli: error: {e}", file=sys.stderr)
        return 2
    if res.status == "dry-run":
        print(res.message)
        print(f"agent_cli: dry run: prompt written to {rendered}; nothing run")
        return 0
    print(f"agent_cli: status={res.status} attempts={res.attempts} {res.message}".rstrip())
    return 0 if res.ok else 1


if __name__ == "__main__":
    sys.exit(main())
