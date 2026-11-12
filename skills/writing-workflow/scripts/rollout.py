#!/usr/bin/env python3
"""Run agent stages (write / review / verdict) for several units in parallel, resumably.

The roll-out driver of the enslopification skills. A JSON config lists units (sections, outline units, referee
reports, groups of citations) and a sequence of stages. Every unit goes through the stages in order; units run in
parallel; writer and reviewer jobs are limited by semaphores; each finished stage leaves a .done marker, so a
restart resumes where it stopped, and a job still running from an earlier driver is adopted, not started twice.

  write    one writer per unit. Files named by `seed` and the outputs of the `from` stage are copied into the stage
           directory; the prompt (with the unit's INBOX.md appended when it is not empty) goes to the agent; the
           `expect` files must exist afterwards; `check` commands run, and a failing check gives the writer one
           retry with the check output quoted (shape checks, the vocabulary check, page or word allowances).
  review   optional `build` commands run first (for example: compile the PDF from the sources about to be frozen;
           their output is frozen as build.txt); then a packet is frozen (make_packet.py); several named reviewers,
           and with `foreach` one reviewer per item of a list, run in parallel on it; each prints its report, which
           is saved and checked for length and for a required line (the verdict). Every profile of a review stage,
           and the profile of the write stage whose output it reads, must name its model `family`; a reviewer of
           the writer's family is refused unless the stage sets allow_same_family (then a warning is logged).
  verdict  reads the verdict line of one report and writes the unit's STATUS (for example DELIVER or NOT YET).

State: <workdir>/<key>/<stage>/ holds prompt files, outputs, logs, packet/ and .done; <workdir>/progress.log has
one line per event; <workdir>/<key>/STATUS the last verdict; <workdir>/<key>/INBOX.md requests for the next writer.
The config format, every field, the template variables and the environment given to agents are documented in
references/driver.md of the writing-workflow skill.

Usage:
  rollout.py CONFIG.json [--dry-run] [--only KEY,...] [--stages NAME,...] [--var NAME=VALUE]...
                         [--workdir DIR] [--agents FILE] [--limit NAME=N]... [--status]
Exit status: 0 every selected unit finished its selected stages; 1 a stage failed or was stopped (quota, protect
violation, failed check); 2 config or template error.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent


def _load(name: str):
    sys.dont_write_bytecode = True          # no __pycache__ inside an installed skill
    spec = importlib.util.spec_from_file_location(f"enslop_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


agent_cli = _load("agent_cli")
make_packet = _load("make_packet")
TemplateError = agent_cli.TemplateError
Result = agent_cli.Result

NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
VAR_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*\Z")
BUILTINS = {"key", "title", "pages", "stage", "stage_dir", "unit_dir", "workdir", "config_dir", "driver_dir",
            "prev_dir", "prev_stage", "reports_dir", "reports_stage", "packet", "inbox", "name", "review", "item",
            "item_slug", "unit_keys"}
TOP_FIELDS = {"workdir", "agents", "limits", "vars", "units", "stages", "protect", "protect_exclude",
              "packet_repos", "packet_exclude", "extends"}
UNIT_FIELDS = {"title", "pages", "vars"}
_COMMON = {"name", "kind", "when_status", "vars"}
STAGE_FIELDS = {
    "write": _COMMON | {"profile", "prompt", "seed", "from", "reports", "expect", "check", "inbox", "protect",
                        "cwd", "limit"},
    "review": _COMMON | {"profile", "reviews", "packet", "packet_exclude", "from", "reports", "min_chars",
                         "require", "allow_same_family", "protect", "cwd", "limit", "build"},
    "verdict": _COMMON | {"report", "pattern", "verdict_line", "pass", "fail"},
}
ENTRY_FIELDS = {"prompt", "foreach", "profile", "min_chars", "require"}
DRIVER_FILES = ["prompt*.md", "agent.log", "*.agent.log", "*.running", "*.exit", "*.protect.json", "*.protect.txt",
                "*.partial", "*.rejected", "*.tmp", ".done", "check-*.txt", "packet", "STATUS"]
DEFAULT_LIMITS = {"writer": 4, "reviewer": 6}
DEFAULT_VERDICT_LINE = r"(?i)^[\s#>*_|`-]*verdict\b"
CHECK_HEADER = "## The check failed: fix this before you finish"
BUILD_LOG = "build.txt"
INBOX_HEADER = "# Inbox: requests from the editor and from other sections"
UNSET = "SET-ME"


class ConfigError(ValueError):
    pass


class StageError(RuntimeError):
    pass


def utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _strip_notes(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: _strip_notes(v) for k, v in x.items() if not (isinstance(k, str) and k.startswith("_"))}
    if isinstance(x, list):
        return [_strip_notes(v) for v in x]
    return x


def _abs(value: Any, here: Path) -> Any:
    """Make a relative path (not starting with a placeholder) relative to the config file that wrote it."""
    if isinstance(value, list):
        return [_abs(v, here) for v in value]
    if not isinstance(value, str) or not value or value.startswith("{{") or os.path.isabs(value) or UNSET in value:
        return value
    return str(here / value)


def _abs_spec(value: Any, here: Path) -> Any:
    if isinstance(value, list):
        return [_abs_spec(v, here) for v in value]
    dest, src = make_packet.split_spec(value) if isinstance(value, str) else (None, value)
    return f"{dest}={_abs(src, here)}" if dest else _abs(src, here)


def load_config(path: Path, chain: tuple[Path, ...] = ()) -> dict:
    """Read a config, resolve its relative paths against its own directory, and merge any base it extends."""
    path = path.resolve()
    if path in chain:
        raise ConfigError("config 'extends' cycle: " + " -> ".join(str(p) for p in chain + (path,)))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"{path}: {e}") from None
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected a JSON object")
    data = _strip_notes(data)
    here = path.parent
    for key in ("workdir", "agents"):
        if key in data and not isinstance(data[key], dict):
            data[key] = _abs(data[key], here)
    for key in ("protect", "packet_repos"):
        if key in data:
            data[key] = _abs(data[key], here)
    if isinstance(data.get("vars"), dict) and "common" in data["vars"]:
        data["vars"]["common"] = _abs(data["vars"]["common"], here)
    for st in data.get("stages", []) if isinstance(data.get("stages"), list) else []:
        if not isinstance(st, dict):
            continue
        for key in ("prompt", "seed", "protect"):
            if key in st:
                st[key] = _abs(st[key], here)
        if "packet" in st:
            st["packet"] = _abs_spec(st["packet"], here)
        if isinstance(st.get("reviews"), dict):
            for rname, entry in st["reviews"].items():
                if isinstance(entry, dict) and "prompt" in entry:
                    entry["prompt"] = _abs(entry["prompt"], here)
                elif isinstance(entry, (str, list)):
                    st["reviews"][rname] = _abs(entry, here)
    if "extends" in data:
        base_ref = data.pop("extends")
        base = load_config(Path(_abs(base_ref, here)), chain + (path,))
        merged = dict(base)
        for k, v in data.items():
            if k in ("vars", "units", "limits") and isinstance(v, dict) and isinstance(base.get(k), dict):
                merged[k] = {**base[k], **v}
            else:
                merged[k] = v
        data = merged
    return data


@dataclass
class ReviewJob:
    name: str
    review: str
    item: str | None
    slug: str | None
    prompt: list[str]
    profile: str
    min_chars: int | None
    require: str | None


class Rollout:
    def __init__(self, config: str | Path, workdir: str | None = None, agents: str | None = None,
                 var_overrides: dict | None = None, limit_overrides: dict | None = None):
        self.config_path = Path(config).resolve()
        self.config_dir = self.config_path.parent
        cfg = load_config(self.config_path)
        unknown = set(cfg) - TOP_FIELDS
        if unknown:
            raise ConfigError(f"unknown top-level field(s): {sorted(unknown)}")
        self.cfg = cfg
        if workdir:
            self.workdir = Path(workdir).resolve()
        elif isinstance(cfg.get("workdir"), str) and UNSET not in cfg["workdir"]:
            self.workdir = Path(cfg["workdir"]).resolve()
        else:
            raise ConfigError("set 'workdir' in the config or pass --workdir")
        self.profiles = self._load_agents(agents or cfg.get("agents") or os.environ.get("ENSLOP_AGENTS"))
        self.limits = dict(DEFAULT_LIMITS)
        self.limits.update(cfg.get("limits", {}))
        self.limits.update(limit_overrides or {})
        for k, v in self.limits.items():
            if not isinstance(v, int) or v < 1:
                raise ConfigError(f"limit {k!r} must be a positive integer")
        self.vars = dict(cfg.get("vars", {}))
        self.vars.update(var_overrides or {})
        self.units = cfg.get("units")
        self.stages = cfg.get("stages")
        self._validate_structure()
        self.sems = {k: threading.BoundedSemaphore(v) for k, v in self.limits.items()}
        self.lock = threading.Lock()
        self.halted: dict[str, str] = {}
        self.halt_all: str | None = None
        self.outcome: dict[str, tuple[str | None, str]] = {}

    # ------------------------------------------------------------------ configuration

    def _load_agents(self, src: Any) -> dict:
        if src is None:
            raise ConfigError("no agent profiles: set 'agents' in the config, pass --agents, or set ENSLOP_AGENTS")
        if isinstance(src, dict):
            return agent_cli.load_profiles(src)
        candidates = src if isinstance(src, list) else [src]
        for c in candidates:
            p = self.path(c)
            if p.is_file():
                return agent_cli.load_profiles(p)
        raise ConfigError("agent profiles not found: " + ", ".join(str(self.path(c)) for c in candidates))

    def path(self, p: str | Path) -> Path:
        p = Path(p)
        return p if p.is_absolute() else self.config_dir / p

    def _validate_structure(self) -> None:
        errs: list[str] = []
        if not isinstance(self.units, dict) or not self.units:
            raise ConfigError("'units' must be a non-empty object")
        if not isinstance(self.stages, list) or not self.stages:
            raise ConfigError("'stages' must be a non-empty list")
        for name in list(self.vars):
            if not VAR_RE.match(name):
                errs.append(f"variable name {name!r} is not valid")
            if name in BUILTINS:
                errs.append(f"variable {name!r} shadows a built-in variable")
        for key, unit in self.units.items():
            if not NAME_RE.match(key):
                errs.append(f"unit key {key!r}: use letters, digits, _ . -")
            if not isinstance(unit, dict):
                errs.append(f"unit {key}: expected an object")
                continue
            for f in set(unit) - UNIT_FIELDS:
                errs.append(f"unit {key}: unknown field {f!r}")
            for name in unit.get("vars", {}) or {}:
                if name in BUILTINS:
                    errs.append(f"unit {key}: variable {name!r} shadows a built-in variable")
        seen = set()
        for i, st in enumerate(self.stages):
            if not isinstance(st, dict):
                errs.append(f"stage {i}: expected an object")
                continue
            name, kind = st.get("name"), st.get("kind")
            where = f"stage {name or i}"
            if not isinstance(name, str) or not NAME_RE.match(name):
                errs.append(f"{where}: 'name' is required (letters, digits, _ . -)")
            elif name in seen:
                errs.append(f"{where}: duplicate stage name")
            seen.add(name)
            if kind not in STAGE_FIELDS:
                errs.append(f"{where}: 'kind' must be write, review or verdict")
                continue
            for f in set(st) - STAGE_FIELDS[kind]:
                errs.append(f"{where}: unknown field {f!r} for a {kind} stage")
            for f in ("from", "reports"):
                if f in st and (not isinstance(st[f], str) or not NAME_RE.match(st[f])):
                    errs.append(f"{where}: {f!r} must name a stage")
            if "when_status" in st and not (isinstance(st["when_status"], list)
                                            and all(isinstance(x, str) for x in st["when_status"])):
                errs.append(f"{where}: 'when_status' must be a list of strings")
            if kind in ("write", "review"):
                if st.get("profile") not in self.profiles:
                    errs.append(f"{where}: unknown profile {st.get('profile')!r}")
                lim = st.get("limit", "writer" if kind == "write" else "reviewer")
                if lim not in self.limits:
                    errs.append(f"{where}: unknown limit {lim!r} (define it in 'limits')")
                for f in ("check", "build"):
                    if f in st and not (isinstance(st[f], str) or (
                            isinstance(st[f], list) and all(isinstance(c, str) for c in st[f]))):
                        errs.append(f"{where}: {f!r} must be a shell command or a list of shell commands")
            if kind == "write" and "prompt" not in st:
                errs.append(f"{where}: 'prompt' is required")
            if kind == "review":
                revs = st.get("reviews")
                if not isinstance(revs, dict) or not revs:
                    errs.append(f"{where}: 'reviews' must be a non-empty object")
                    continue
                for rname, entry in revs.items():
                    if not NAME_RE.match(rname):
                        errs.append(f"{where}: review name {rname!r} is not valid")
                    if isinstance(entry, dict):
                        for f in set(entry) - ENTRY_FIELDS:
                            errs.append(f"{where}, review {rname}: unknown field {f!r}")
                        if "prompt" not in entry:
                            errs.append(f"{where}, review {rname}: 'prompt' is required")
                        if "profile" in entry and entry["profile"] not in self.profiles:
                            errs.append(f"{where}, review {rname}: unknown profile {entry['profile']!r}")
                    elif not isinstance(entry, (str, list)):
                        errs.append(f"{where}, review {rname}: expected a template path, a list, or an object")
            if kind == "verdict":
                for f in ("report", "pattern"):
                    if f not in st:
                        errs.append(f"{where}: {f!r} is required")
                for f in ("pattern", "verdict_line"):
                    if f in st:
                        try:
                            re.compile(st[f])
                        except re.error as e:
                            errs.append(f"{where}: bad regex {f}: {e}")
        self.warnings: list[str] = []
        if not errs:
            for i, st in enumerate(self.stages):
                if st.get("kind") == "review":
                    problems = self._family_problems(i)
                    if st.get("allow_same_family"):
                        self.warnings += [f"stage {st['name']} (allow_same_family): {p}" for p in problems]
                    else:
                        errs += [f"stage {st['name']}: {p}; fix the profile or set allow_same_family on the stage"
                                 for p in problems]
        if errs:
            raise ConfigError("\n  ".join(["invalid config:"] + errs))

    def _family_problems(self, idx: int) -> list[str]:
        """A review stage needs a model family on every reviewer profile and on the profile of the write stage
        whose output it reads (its `from` stage if that is a write stage of this config, else the last write stage
        before it), and the two must differ."""
        st = self.stages[idx]
        named = next((s for s in self.stages if s.get("name") == st.get("from") and s.get("kind") == "write"), None)
        writer = named or next((s for s in reversed(self.stages[:idx]) if s.get("kind") == "write"), None)
        problems, wfam = [], None
        if writer is not None:
            wfam = self.profiles[writer["profile"]].get("family")
            if not wfam:
                problems.append(f"the writer profile {writer['profile']!r} of stage {writer['name']} has no 'family'")
        for rname, entry in st["reviews"].items():
            prof = entry.get("profile", st.get("profile")) if isinstance(entry, dict) else st.get("profile")
            rfam = self.profiles[prof].get("family")
            if not rfam:
                problems.append(f"review {rname}: the reviewer profile {prof!r} has no 'family'")
            elif wfam and rfam == wfam:
                problems.append(f"review {rname}: the reviewer profile {prof!r} is of the same model family ({rfam}) "
                                f"as the writer of stage {writer['name']}")
        return problems

    # ------------------------------------------------------------------ variables and templates

    def prev_stage(self, idx: int) -> str | None:
        st = self.stages[idx]
        if st.get("from"):
            return st["from"]
        return next((s["name"] for s in reversed(self.stages[:idx]) if s["kind"] == "write"), None)

    def reports_stage(self, idx: int) -> str | None:
        st = self.stages[idx]
        if st.get("reports"):
            return st["reports"]
        return next((s["name"] for s in reversed(self.stages[:idx]) if s["kind"] == "review"), None)

    def builtins(self, key: str, idx: int, job: ReviewJob | None = None) -> dict[str, Any]:
        st, unit = self.stages[idx], self.units[key]
        udir = self.workdir / key
        b: dict[str, Any] = {"key": key, "title": unit.get("title", key), "stage": st["name"],
                             "stage_dir": str(udir / st["name"]), "unit_dir": str(udir),
                             "workdir": str(self.workdir), "config_dir": str(self.config_dir),
                             "driver_dir": str(HERE),
                             "unit_keys": "\n".join(f"{k} — {u.get('title', k)}" for k, u in self.units.items())}
        if "pages" in unit:
            b["pages"] = unit["pages"]
        prev, rep = self.prev_stage(idx), self.reports_stage(idx)
        if prev:
            b.update(prev_stage=prev, prev_dir=str(udir / prev))
        if rep:
            b.update(reports_stage=rep, reports_dir=str(udir / rep))
        if st["kind"] == "review":
            b["packet"] = str(udir / st["name"] / "packet")
        elif rep:
            b["packet"] = str(udir / rep / "packet")
        if job is not None:
            b.update(name=job.name, review=job.review, item=job.item or "", item_slug=job.slug or "")
        return b

    def lookup(self, key: str, idx: int, job: ReviewJob | None = None,
               inbox: str | None = None) -> Callable[[str], Any]:
        """Variables for one job: built-ins, then stage vars over unit vars over config vars (resolved lazily,
        so a variable may use other variables). `common` is the rendered text of the file(s) it names."""
        b = self.builtins(key, idx, job)
        raw: dict[str, Any] = dict(self.vars)
        raw.update(self.units[key].get("vars", {}) or {})
        raw.update(self.stages[idx].get("vars", {}) or {})
        cache: dict[str, Any] = {}
        busy: set[str] = set()

        def get(name: str) -> Any:
            if name in b:
                return b[name]
            if name == "inbox":
                return inbox if inbox is not None else self.read_inbox(key)
            if name in cache:
                return cache[name]
            if name not in raw:
                raise KeyError(name)
            if name in busy:
                raise TemplateError(f"variable {{{{{name}}}}} refers to itself")
            busy.add(name)
            try:
                v = raw[name]
                if name == "common":
                    v = self._common_text(v, get)
                elif isinstance(v, list):
                    v = [agent_cli.render(str(x), get, f"variable {name}") for x in v]
                elif isinstance(v, str):
                    v = agent_cli.render(v, get, f"variable {name}")
                if name != "common" and UNSET in agent_cli.format_value(v):
                    raise TemplateError(f"variable {name!r} is not set (its value is {agent_cli.format_value(v)!r})")
            finally:
                busy.discard(name)
            cache[name] = v
            return v

        return get

    def _common_text(self, value: Any, get: Callable[[str], Any]) -> str:
        parts = []
        for p in value if isinstance(value, list) else [value]:
            path = self.path(agent_cli.render(str(p), get, "variable common"))
            if UNSET in str(path):
                raise TemplateError(f"variable 'common' is not set ({p})")
            try:
                parts.append(path.read_text(encoding="utf-8").rstrip("\n"))
            except OSError as e:
                raise TemplateError(f"cannot read the common rules {path}: {e}") from None
        return agent_cli.render("\n\n".join(parts), get, "common rules")

    def render_prompt(self, templates: Any, get: Callable[[str], Any], where: str) -> tuple[str, str]:
        parts = []
        for t in templates if isinstance(templates, list) else [templates]:
            path = self.path(agent_cli.render(t, get, f"{where} prompt path"))
            try:
                parts.append(path.read_text(encoding="utf-8").rstrip("\n"))
            except OSError as e:
                raise TemplateError(f"{where}: cannot read prompt template {path}: {e}") from None
        raw = "\n\n".join(parts) + "\n"
        return agent_cli.render(raw, get, where), raw

    def render_list(self, items: Any, get: Callable[[str], Any], where: str) -> list[str]:
        if items is None:
            return []
        return agent_cli.render_list(items if isinstance(items, list) else [items], get, where)

    def review_jobs(self, key: str, idx: int) -> list[ReviewJob]:
        st = self.stages[idx]
        get = self.lookup(key, idx, inbox="")
        jobs: list[ReviewJob] = []
        for rname, entry in st["reviews"].items():
            if not isinstance(entry, dict):
                entry = {"prompt": entry}
            prompts = entry["prompt"] if isinstance(entry["prompt"], list) else [entry["prompt"]]
            profile = entry.get("profile", st["profile"])
            mc, req = entry.get("min_chars", st.get("min_chars")), entry.get("require", st.get("require"))
            if "foreach" in entry:
                try:
                    items = get(entry["foreach"])
                except KeyError:
                    raise TemplateError(f"unit {key}, stage {st['name']}: foreach variable {entry['foreach']!r} is "
                                        f"not defined (define it, as [] when there is nothing)") from None
                if isinstance(items, str):
                    items = [items] if items.strip() else []
                if not isinstance(items, list):
                    raise TemplateError(f"unit {key}: foreach variable {entry['foreach']!r} must be a list")
                for it in items:
                    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(it)).strip("_") or "item"
                    jobs.append(ReviewJob(f"{rname}-{slug}", rname, str(it), slug, prompts, profile, mc, req))
            else:
                jobs.append(ReviewJob(rname, rname, None, None, prompts, profile, mc, req))
        names = [j.name for j in jobs]
        dupes = sorted({n for n in names if names.count(n) > 1})
        if dupes:
            raise TemplateError(f"unit {key}, stage {st['name']}: duplicate review job name(s) {dupes}")
        return jobs

    def validate_jobs(self, keys: list[str], stage_names: set[str]) -> None:
        """Render everything that will be rendered at run time, so that template errors stop the run before any
        agent starts."""
        errs = []
        for key in keys:
            for idx, st in enumerate(self.stages):
                if st["name"] not in stage_names:
                    continue
                where = f"unit {key}, stage {st['name']}"
                try:
                    get = self.lookup(key, idx, inbox="")
                    if st["kind"] == "write":
                        self.render_prompt(st["prompt"], get, where)
                        for f in ("seed", "expect", "protect"):
                            self.render_list(st.get(f), get, f"{where} {f}")
                        self.render_list(st.get("check"), get, f"{where} check")
                        if "cwd" in st:
                            agent_cli.render(st["cwd"], get, f"{where} cwd")
                        agent_cli.build_command(self._job_stub(st["profile"], get, idx, key))
                    elif st["kind"] == "review":
                        for j in self.review_jobs(key, idx):
                            jget = self.lookup(key, idx, job=j, inbox="")
                            self.render_prompt(j.prompt, jget, f"{where}, review {j.name}")
                            agent_cli.build_command(self._job_stub(j.profile, jget, idx, key))
                        self.render_list(st.get("packet"), get, f"{where} packet")
                        self.render_list(st.get("protect"), get, f"{where} protect")
                        self.render_list(st.get("build"), get, f"{where} build")
                    else:
                        agent_cli.render(st["report"], get, f"{where} report")
                    self.render_list(self.cfg.get("protect"), get, "config protect")
                    self.render_list(self.cfg.get("packet_repos"), get, "config packet_repos")
                except (TemplateError, ConfigError) as e:
                    if str(e) not in errs:
                        errs.append(str(e))
        if errs:
            raise ConfigError("\n  ".join(["template errors:"] + errs[:30]
                                          + ([f"... and {len(errs) - 30} more"] if len(errs) > 30 else [])))

    def _job_stub(self, profile: str, get: Callable[[str], Any], idx: int, key: str):
        sdir = self.workdir / key / self.stages[idx]["name"]
        return agent_cli.Job(profile=self.profiles[profile], prompt_file=sdir / "prompt.md", cwd=sdir,
                             log=sdir / "agent.log", report=sdir / "report.md", variables=get)

    # ------------------------------------------------------------------ helpers

    def log(self, key: str | None, stage: str | None, msg: str) -> None:
        line = f"{utc()} {key or '-'} {stage or '-'} {msg}"
        with self.lock:
            self.workdir.mkdir(parents=True, exist_ok=True)
            with open(self.workdir / "progress.log", "a", encoding="utf-8") as f:
                f.write(line + "\n")
            print(line, flush=True)

    def read_inbox(self, key: str) -> str:
        p = self.workdir / key / "INBOX.md"
        try:
            return p.read_text(encoding="utf-8")
        except OSError:
            return ""

    def status_of(self, key: str) -> str:
        try:
            return (self.workdir / key / "STATUS").read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    def stop_reason(self, profile: str) -> str | None:
        with self.lock:
            if self.halt_all:
                return f"stopped after a protect violation ({self.halt_all})"
            if profile in self.halted:
                return f"profile {profile} stopped after a quota message ({self.halted[profile]})"
        return None

    def protect_paths(self, st: dict, get: Callable[[str], Any], where: str) -> list[Path]:
        items = self.render_list(self.cfg.get("protect"), get, "config protect") + \
            self.render_list(st.get("protect"), get, f"{where} protect")
        return [self.path(p).resolve() for p in items]

    def job_env(self, key: str, st: dict, job_name: str, sdir: Path, expect: list[Path],
                report: Path | None) -> dict[str, str]:
        return {"ENSLOP_UNIT": key, "ENSLOP_STAGE": st["name"], "ENSLOP_JOB": job_name, "ENSLOP_STAGE_DIR": str(sdir),
                "ENSLOP_EXPECT": json.dumps([str(e) for e in expect]), "ENSLOP_REPORT": str(report or "")}

    def run_agent(self, key: str, st: dict, profile: str, job, label: str) -> Any:
        lim = st.get("limit", "writer" if st["kind"] == "write" else "reviewer")
        with self.sems[lim]:
            reason = self.stop_reason(profile)
            if reason:
                return Result("stopped", message=reason)
            self.log(key, st["name"], f"{label} start (profile {profile})")
            res = agent_cli.run_job(job, note=lambda m: self.log(key, st["name"], f"{label}: {m}"))
        if res.status == "quota":
            with self.lock:
                self.halted.setdefault(profile, res.message)
        elif res.status == "protect":
            with self.lock:
                self.halt_all = self.halt_all or f"{key}/{st['name']}"
        return res

    LABELS = {"quota": "QUOTA or rate limit", "protect": "PROTECT VIOLATION", "failed": "FAILED",
              "stopped": "STOPPED"}

    def failed(self, key: str, stage: str, res: Any) -> bool:
        return self.fail(key, stage, f"{self.LABELS.get(res.status, res.status.upper())}: {res.message}")

    def fail(self, key: str, stage: str, msg: str) -> bool:
        self.log(key, stage, msg)
        self.outcome.setdefault(key, (stage, msg))
        return False

    @staticmethod
    def _copy_tree(src: Path, dst: Path, exclude: list[str]) -> int:
        n = 0
        for root, dirs, files in os.walk(src):
            rel = Path(root).relative_to(src)
            dirs[:] = [d for d in dirs if not make_packet._excluded(d, str(rel / d), exclude)]
            for name in files:
                if make_packet._excluded(name, str(rel / name), exclude):
                    continue
                target = dst / rel / name
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(Path(root) / name, target)
                    n += 1
        return n

    def copy_inputs(self, key: str, idx: int, sdir: Path, get: Callable[[str], Any]) -> None:
        st = self.stages[idx]
        if st.get("from"):
            src = self.workdir / key / st["from"]
            if not src.is_dir():
                raise StageError(f"'from' stage {st['from']} has no directory {src}")
            self._copy_tree(src, sdir, DRIVER_FILES + ["INBOX-received.md"])
        for s in self.render_list(st.get("seed"), get, f"{key}/{st['name']} seed"):
            p = str(self.path(s))
            matches = sorted(glob.glob(p)) if glob.has_magic(p) else ([p] if os.path.exists(p) else [])
            if not matches:
                raise StageError(f"seed not found: {p}")
            for m in matches:
                m = Path(m)
                if m.is_dir():
                    self._copy_tree(m, sdir / m.name, [])
                elif not (sdir / m.name).exists():
                    shutil.copy2(m, sdir / m.name)

    def run_checks(self, cmds: list[str], sdir: Path, n: int, out_name: str | None = None) -> tuple[bool, str]:
        """Run shell commands in sdir; save their output as check-N.txt (or out_name); ok if every exit is 0."""
        outputs, ok = [], True
        for cmd in cmds:
            try:
                r = subprocess.run(cmd, shell=True, cwd=str(sdir), capture_output=True, text=True, timeout=1800)
                outputs.append(f"$ {cmd}\n{r.stdout}{r.stderr}[exit {r.returncode}]")
                ok &= r.returncode == 0
            except subprocess.TimeoutExpired:
                outputs.append(f"$ {cmd}\n[timed out after 1800 s]")
                ok = False
        text = "\n\n".join(outputs)
        (sdir / (out_name or f"check-{n}.txt")).write_text(text + "\n", encoding="utf-8")
        return ok, text

    def archive_inbox(self, key: str, stage: str, delivered: str) -> None:
        if not delivered.strip():
            return
        inbox = self.workdir / key / "INBOX.md"
        current = self.read_inbox(key)
        if current.startswith(delivered):
            with open(self.workdir / key / "inbox-archive.md", "a", encoding="utf-8") as f:
                f.write(f"\n<!-- delivered to stage {stage} on {utc()} -->\n{delivered}")
            inbox.write_text(current[len(delivered):], encoding="utf-8")
            self.log(key, stage, "inbox delivered and archived")
        else:
            self.log(key, stage, "INBOX.md changed while the stage ran; not archived (check it by hand)")

    @staticmethod
    def report_valid(report: Path, min_chars: int, require: str | None) -> bool:
        try:
            text = report.read_text(encoding="utf-8")
        except OSError:
            return False
        return len(text.strip()) >= max(1, min_chars) and (not require or re.search(require, text, re.M) is not None)

    @staticmethod
    def write_done(sdir: Path, data: dict) -> None:
        (sdir / ".done").write_text(json.dumps(dict(data, finished_utc=utc()), indent=1) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------ stages

    def run_write(self, key: str, idx: int) -> bool:
        st = self.stages[idx]
        name, profile = st["name"], st["profile"]
        sdir = self.workdir / key / name
        if (sdir / ".done").exists():
            self.log(key, name, "skip (done)")
            return True
        reason = self.stop_reason(profile)
        if reason:
            return self.fail(key, name, f"STOPPED: {reason}")
        sdir.mkdir(parents=True, exist_ok=True)
        get = self.lookup(key, idx)
        where = f"{key}/{name}"
        expect = [sdir / e for e in self.render_list(st.get("expect"), get, f"{where} expect")]
        prof = self.profiles[profile]
        report = sdir / f"{name}.md" if prof.get("stdout") == "report" else None
        job = agent_cli.Job(profile=prof, prompt_file=sdir / "prompt.md",
                            cwd=Path(agent_cli.render(st["cwd"], get, f"{where} cwd")) if "cwd" in st else sdir,
                            log=sdir / "agent.log", report=report, variables=get, expect=expect,
                            protect=self.protect_paths(st, get, where),
                            protect_exclude=agent_cli.DEFAULT_PROTECT_EXCLUDE + list(self.cfg.get("protect_exclude", [])),
                            env=self.job_env(key, st, "write", sdir, expect, report), name=where)
        received = sdir / "INBOX-received.md"
        try:
            if agent_cli.pending(job):
                delivered = received.read_text(encoding="utf-8") if received.exists() else ""
                self.log(key, name, "resuming a job started by an earlier run")
            else:
                self.copy_inputs(key, idx, sdir, get)
                delivered = self.read_inbox(key) if st.get("inbox", True) else ""
                text, raw = self.render_prompt(st["prompt"], get, where)
                if delivered.strip() and "inbox" not in agent_cli.placeholders_in(raw):
                    text += (f"\n{INBOX_HEADER}\n\nAnswer each request in your response table: applied, declined "
                             f"with a reason, or forwarded to the section that owns it.\n\n{delivered}")
                if delivered.strip():
                    received.write_text(delivered, encoding="utf-8")
                (sdir / "prompt.md").write_text(text, encoding="utf-8")
        except (StageError, TemplateError, OSError) as e:
            return self.fail(key, name, f"FAILED before the agent ran: {e}")
        res = self.run_agent(key, st, profile, job, "writer")
        if not res.ok:
            return self.failed(key, name, res)
        checks = self.render_list(st.get("check"), get, f"{where} check")
        check_state = "none"
        if checks:
            ok, out = self.run_checks(checks, sdir, 1)
            check_state = "passed"
            if not ok:
                self.log(key, name, "check failed (check-1.txt); one retry with the check output quoted")
                quoted = out if len(out) <= 8000 else "...\n" + out[-8000:]
                retry = (sdir / "prompt.md").read_text(encoding="utf-8") + (
                    f"\n\n{CHECK_HEADER}\n\nYour deliverables did not pass the automatic check below. Fix every "
                    f"problem it reports, then finish. An allowance overrun means cut; do not explain it away. "
                    f"Check output:\n\n```text\n{quoted}\n```\n")
                (sdir / "prompt-retry.md").write_text(retry, encoding="utf-8")
                job.prompt_file = sdir / "prompt-retry.md"
                res = self.run_agent(key, st, profile, job, "writer (check retry)")
                if not res.ok:
                    return self.failed(key, name, res)
                ok, out = self.run_checks(checks, sdir, 2)
                if not ok:
                    return self.fail(key, name, "CHECK FAILED after the retry: see check-2.txt (not done)")
                check_state = "passed after one retry"
        self.archive_inbox(key, name, delivered)
        self.write_done(sdir, {"stage": name, "kind": "write", "attempts": res.attempts, "adopted": res.adopted,
                               "check": check_state})
        self.log(key, name, f"writer done (check: {check_state})")
        return True

    def freeze_packet(self, key: str, idx: int, get: Callable[[str], Any]) -> Path:
        st = self.stages[idx]
        pdir = self.workdir / key / st["name"] / "packet"
        if (pdir / "manifest.json").exists():
            return pdir
        entries = st.get("packet") or ["proposal={{prev_dir}}"]
        specs = []
        for e in self.render_list(entries, get, f"{key}/{st['name']} packet"):
            dest, src = make_packet.split_spec(e)
            specs.append((dest, str(self.path(src))))
        note = f"unit {key}, stage {st['name']}"
        builds = self.render_list(st.get("build"), get, f"{key}/{st['name']} build")
        if builds:
            specs.append((BUILD_LOG, str(pdir.parent / BUILD_LOG)))
            note += "; before freezing, the driver ran: " + " ; ".join(builds)
        repos = [str(self.path(r)) for r in self.render_list(self.cfg.get("packet_repos"), get, "packet_repos")]
        exclude = DRIVER_FILES + list(self.cfg.get("packet_exclude", [])) + list(st.get("packet_exclude", []))
        m = make_packet.freeze(pdir, specs, repos=repos, exclude=exclude, note=note, force=True)
        self.log(key, st["name"], f"packet frozen: {len(m['files'])} files")
        return pdir

    def run_review(self, key: str, idx: int) -> bool:
        st = self.stages[idx]
        name = st["name"]
        sdir = self.workdir / key / name
        if (sdir / ".done").exists():
            self.log(key, name, "skip (done)")
            return True
        sdir.mkdir(parents=True, exist_ok=True)
        try:
            jobs = self.review_jobs(key, idx)
            if not jobs:
                self.write_done(sdir, {"stage": name, "kind": "review", "jobs": {}})
                self.log(key, name, "no review jobs (empty foreach list); done")
                return True
            get = self.lookup(key, idx)
            builds = self.render_list(st.get("build"), get, f"{key}/{name} build")
            if builds and not (sdir / "packet" / "manifest.json").exists():
                ok, _ = self.run_checks(builds, sdir, 0, out_name=BUILD_LOG)
                if not ok:
                    return self.fail(key, name, f"BUILD FAILED before freezing (see {name}/{BUILD_LOG}); "
                                                f"no review ran")
                self.log(key, name, f"build done ({len(builds)} command(s); output in {BUILD_LOG})")
            self.freeze_packet(key, idx, get)
        except (TemplateError, make_packet.PacketError, OSError) as e:
            return self.fail(key, name, f"FAILED before the reviews ran: {e}")
        results: dict[str, Any] = {}
        threads = [threading.Thread(target=self._review_job, args=(key, idx, j, results), daemon=True) for j in jobs]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        bad = {n: r for n, r in results.items() if not r.ok}
        if bad or len(results) < len(jobs):
            detail = "; ".join(f"{n}: {r.status} {r.message}" for n, r in sorted(bad.items()))
            return self.fail(key, name, f"REVIEWS INCOMPLETE: {detail or 'a review thread died'}")
        self.write_done(sdir, {"stage": name, "kind": "review",
                               "jobs": {n: ("kept" if r.message == "kept" else r.status) for n, r in results.items()}})
        self.log(key, name, f"reviews done ({len(jobs)})")
        return True

    def _review_job(self, key: str, idx: int, j: ReviewJob, results: dict) -> None:
        st = self.stages[idx]
        sdir = self.workdir / key / st["name"]
        try:
            prof = self.profiles[j.profile]
            report = sdir / f"{j.name}.md"
            need = j.min_chars if j.min_chars is not None else prof.get("min_chars", 0)
            get = self.lookup(key, idx, job=j)
            job = agent_cli.Job(profile=prof, prompt_file=sdir / f"prompt-{j.name}.md",
                                cwd=Path(agent_cli.render(st["cwd"], get, "cwd")) if "cwd" in st else sdir,
                                log=sdir / f"{j.name}.agent.log", report=report, variables=get, min_chars=need,
                                require=j.require, protect=self.protect_paths(st, get, f"{key}/{st['name']}"),
                                protect_exclude=agent_cli.DEFAULT_PROTECT_EXCLUDE
                                + list(self.cfg.get("protect_exclude", [])),
                                env=self.job_env(key, st, j.name, sdir, [], report), name=f"{key}/{st['name']}/{j.name}")
            if not agent_cli.pending(job) and self.report_valid(report, need, j.require):
                results[j.name] = Result("ok", message="kept")
                self.log(key, st["name"], f"{j.name} kept (valid report exists)")
                return
            if not agent_cli.pending(job):
                text, _ = self.render_prompt(j.prompt, get, f"{key}/{st['name']}/{j.name}")
                job.prompt_file.write_text(text, encoding="utf-8")
            res = self.run_agent(key, st, j.profile, job, j.name)
            results[j.name] = res
            if res.ok:
                size = len(report.read_text(encoding="utf-8")) if report.exists() else 0
                self.log(key, st["name"], f"{j.name} done ({size} chars)")
            else:
                self.log(key, st["name"], f"{j.name} {self.LABELS.get(res.status, res.status.upper())}: {res.message}")
        except Exception as e:  # noqa: BLE001 - a thread must always report
            results[j.name] = Result("failed", message=f"{e.__class__.__name__}: {e}")
            self.log(key, st["name"], f"{j.name} ERROR {e!r}")

    def run_verdict(self, key: str, idx: int) -> bool:
        st = self.stages[idx]
        name = st["name"]
        udir = self.workdir / key
        sdir = udir / name
        get = self.lookup(key, idx)
        report = Path(agent_cli.render(st["report"], get, f"{key}/{name} report"))
        report = report if report.is_absolute() else udir / report
        if not report.is_file():
            return self.fail(key, name, f"FAILED: no report {report}")
        digest = hashlib.sha256(report.read_bytes()).hexdigest()
        try:
            done = json.loads((sdir / ".done").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            done = {}
        if done.get("report_sha256") == digest:
            self.log(key, name, f"skip (done; verdict {done.get('status')} for an unchanged report)")
            return True
        line_re = re.compile(st.get("verdict_line", DEFAULT_VERDICT_LINE))
        lines = [ln for ln in report.read_text(encoding="utf-8", errors="replace").splitlines() if line_re.search(ln)]
        if not lines:
            (udir / "STATUS").write_text("NO VERDICT\n", encoding="utf-8")
            return self.fail(key, name, f"FAILED: no verdict line in {report.name}")
        status = st.get("pass", "PASS") if re.search(st["pattern"], lines[-1]) else st.get("fail", "FAIL")
        (udir / "STATUS").write_text(status + "\n", encoding="utf-8")
        sdir.mkdir(parents=True, exist_ok=True)
        self.write_done(sdir, {"stage": name, "kind": "verdict", "status": status, "line": lines[-1].strip(),
                               "report": str(report), "report_sha256": digest})
        self.log(key, name, f"verdict {status}: {lines[-1].strip()[:160]}")
        return True

    # ------------------------------------------------------------------ driving

    def run_unit(self, key: str, stage_names: set[str]) -> None:
        try:
            for idx, st in enumerate(self.stages):
                if st["name"] not in stage_names:
                    continue
                if "when_status" in st:
                    status = self.status_of(key)
                    if status not in st["when_status"]:
                        self.log(key, st["name"], f"skip (STATUS {status or 'none'} not in {st['when_status']})")
                        continue
                run = {"write": self.run_write, "review": self.run_review, "verdict": self.run_verdict}[st["kind"]]
                if not run(key, idx):
                    self.outcome.setdefault(key, (st["name"], "failed"))
                    return
            self.outcome[key] = (None, "done")
        except Exception as e:  # noqa: BLE001
            with open(self.workdir / "errors.log", "a", encoding="utf-8") as f:
                f.write(f"{utc()} {key}\n{traceback.format_exc()}\n")
            self.fail(key, "-", f"ERROR {e!r} (traceback in errors.log)")

    def run(self, keys: list[str], stage_names: set[str]) -> int:
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.log(None, None, f"rollout start: {self.config_path.name}; units {','.join(keys)}; stages "
                             f"{','.join(s['name'] for s in self.stages if s['name'] in stage_names)}")
        for w in self.warnings:
            self.log(None, None, f"WARNING {w}")
        threads = [threading.Thread(target=self.run_unit, args=(k, stage_names), daemon=True) for k in keys]
        for t in threads:
            t.start()
        try:
            for t in threads:
                while t.is_alive():
                    t.join(0.5)
        except KeyboardInterrupt:
            self.log(None, None, "interrupted; running agents continue and a restart adopts them")
            return 1
        stopped = [f"{k}@{self.outcome.get(k, ('?', ''))[0]}" for k in keys if self.outcome.get(k, (None, ''))[1] != "done"]
        summary = (f"rollout: {len(keys) - len(stopped)}/{len(keys)} units finished their stages"
                   + (f"; not finished: {', '.join(stopped)} (see progress.log)" if stopped else ""))
        self.log(None, None, summary)
        return 1 if stopped else 0

    def dry_run(self, keys: list[str], stage_names: set[str]) -> int:
        out = self.workdir / ".dry-run"
        shown: set[str] = set()
        n_prompts = 0
        print(f"plan: config {self.config_path}; workdir {self.workdir}; limits {self.limits}")
        for w in self.warnings:
            print(f"WARNING {w}")
        for key in keys:
            for idx, st in enumerate(self.stages):
                if st["name"] not in stage_names:
                    continue
                d = out / key / st["name"]
                d.mkdir(parents=True, exist_ok=True)
                get = self.lookup(key, idx)
                cond = f" when STATUS in {st['when_status']}" if "when_status" in st else ""
                if st["kind"] == "write":
                    text, raw = self.render_prompt(st["prompt"], get, f"{key}/{st['name']}")
                    inbox = self.read_inbox(key)
                    if inbox.strip() and st.get("inbox", True) and "inbox" not in agent_cli.placeholders_in(raw):
                        text += f"\n{INBOX_HEADER}\n\n{inbox}"
                    (d / "prompt.md").write_text(text, encoding="utf-8")
                    n_prompts += 1
                    expect = self.render_list(st.get("expect"), get, "expect")
                    checks = self.render_list(st.get("check"), get, "check")
                    print(f"{key:>8} {st['name']:<10} write   profile={st['profile']}{cond} from={st.get('from', '-')} "
                          f"expect={','.join(expect) or '-'} checks={len(checks)} prompt={d / 'prompt.md'}")
                    for c in checks:
                        print(f"{'':>20}check: {c}")
                    profiles = [(st["profile"], get)]
                elif st["kind"] == "review":
                    jobs = self.review_jobs(key, idx)
                    profiles = []
                    for j in jobs:
                        jget = self.lookup(key, idx, job=j)
                        text, _ = self.render_prompt(j.prompt, jget, f"{key}/{st['name']}/{j.name}")
                        (d / f"prompt-{j.name}.md").write_text(text, encoding="utf-8")
                        n_prompts += 1
                        profiles.append((j.profile, jget))
                    packet = self.render_list(st.get("packet") or ["proposal={{prev_dir}}"], get, "packet")
                    print(f"{key:>8} {st['name']:<10} review  jobs={','.join(j.name for j in jobs) or '(none)'}{cond}")
                    for c in self.render_list(st.get("build"), get, "build"):
                        print(f"{'':>20}build: {c}")
                    print(f"{'':>20}packet: {' '.join(packet)}")
                else:
                    profiles = []
                    print(f"{key:>8} {st['name']:<10} verdict report={agent_cli.render(st['report'], get, 'report')} "
                          f"pattern={st['pattern']!r} -> {st.get('pass', 'PASS')} / {st.get('fail', 'FAIL')}{cond}")
                for prof, pget in profiles:
                    if prof in shown:
                        continue
                    shown.add(prof)
                    res = agent_cli.run_job(self._job_stub(prof, pget, idx, key), dry_run=True)
                    print(f"{'':>20}command ({prof}): {res.message}")
        print(f"rollout --dry-run: {len(keys)} unit(s), {len(stage_names)} stage(s), {n_prompts} prompt(s) rendered "
              f"under {out}; nothing run")
        return 0

    def print_status(self, keys: list[str]) -> int:
        names = [s["name"] for s in self.stages]
        rows = [["unit"] + names + ["STATUS"]]
        for key in keys:
            row = [key]
            for n in names:
                d = self.workdir / key / n
                if (d / ".done").exists():
                    row.append("done")
                elif any(d.glob("*.running")) if d.is_dir() else False:
                    row.append("running?")
                elif d.is_dir():
                    row.append("started")
                else:
                    row.append("-")
            row.append(self.status_of(key) or "-")
            rows.append(row)
        widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
        for r in rows:
            print("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())
        print(f"rollout --status: {len(keys)} unit(s), workdir {self.workdir}")
        return 0


def _split(values: list[str]) -> list[str]:
    return [x.strip() for v in values for x in v.split(",") if x.strip()]


def _kv(items: list[str], what: str, as_int: bool = False) -> dict:
    out: dict[str, Any] = {}
    for item in items:
        if "=" not in item:
            raise ConfigError(f"{what} expects NAME=VALUE, got {item!r}")
        k, v = item.split("=", 1)
        if as_int:
            try:
                out[k] = int(v)
            except ValueError:
                raise ConfigError(f"{what} {k}: not an integer: {v!r}") from None
        elif v.startswith("["):
            try:
                out[k] = json.loads(v)
            except json.JSONDecodeError as e:
                raise ConfigError(f"{what} {k}: bad JSON list: {e}") from None
        else:
            out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Run write, review and verdict stages for several units in parallel, resumably, through "
                    "agent_cli.py. The config format is documented in references/driver.md.",
        epilog="examples:\n"
               "  rollout.py section-cycle.json --dry-run            render every prompt, print the plan\n"
               "  rollout.py section-cycle.json --only F,C           run two sections through the cycle\n"
               "  rollout.py section-cycle.json --stages w1,r1       run only these stages\n"
               "  rollout.py fixup.json                              fix-up for the units whose STATUS is NOT YET\n"
               "  rollout.py section-cycle.json --status             one line per unit: stage states and STATUS",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("config", help="rollout config (JSON)")
    ap.add_argument("--dry-run", action="store_true", help="render every prompt and print the plan; run nothing")
    ap.add_argument("--only", action="append", default=[], metavar="KEY[,KEY]", help="units to run (default all)")
    ap.add_argument("--stages", action="append", default=[], metavar="NAME[,NAME]",
                    help="stages to run (default all); the others are left as they are")
    ap.add_argument("--var", action="append", default=[], metavar="NAME=VALUE",
                    help="override a config variable (a value starting with [ is read as a JSON list)")
    ap.add_argument("--workdir", help="override the config's workdir")
    ap.add_argument("--agents", help="override the agent profiles file")
    ap.add_argument("--limit", action="append", default=[], metavar="NAME=N", help="override a semaphore limit")
    ap.add_argument("--status", action="store_true", help="print the state of every unit and stage, then exit")
    a = ap.parse_args(argv)
    try:
        agents = str(Path(a.agents).resolve()) if a.agents else None      # relative to the current directory
        ro = Rollout(a.config, workdir=a.workdir, agents=agents, var_overrides=_kv(a.var, "--var"),
                     limit_overrides=_kv(a.limit, "--limit", as_int=True))
        keys = _split(a.only) or list(ro.units)
        bad = [k for k in keys if k not in ro.units]
        if bad:
            raise ConfigError(f"unknown unit(s) {bad}; known: {', '.join(ro.units)}")
        names = _split(a.stages) or [s["name"] for s in ro.stages]
        bad = [n for n in names if n not in {s["name"] for s in ro.stages}]
        if bad:
            raise ConfigError(f"unknown stage(s) {bad}; known: {', '.join(s['name'] for s in ro.stages)}")
        if a.status:
            return ro.print_status(keys)
        ro.validate_jobs(keys, set(names))
        if a.dry_run:
            return ro.dry_run(keys, set(names))
    except (ConfigError, TemplateError) as e:
        print(f"rollout: {e}", file=sys.stderr)
        return 2
    return ro.run(keys, set(names))


if __name__ == "__main__":
    sys.exit(main())
