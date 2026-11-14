# The agent layer and the roll-out driver

Every agent job in this collection runs through three scripts in [`../scripts/`](../scripts/): `agent_cli.py`
(one job), `rollout.py` (stages for several units, in parallel, resumably) and `make_packet.py` with
`verify_packet.py` (frozen review packets). Other skills ship **config files and prompt templates** for this layer,
never their own drivers. Tests use a stand-in agent kept outside this skill (step 6 of "Writing a config"). This
page is the complete reference of the formats; keep configs to it, because unknown fields are an error.

## Agent profiles

A JSON object of named profiles (`--agents FILE`, the config's `agents`, or `$ENSLOP_AGENTS`). Keys starting with
`_` are notes, anywhere. Example: [`agents.example.json`](../assets/agents.example.json); choosing CLIs, models and
permissions: [agent profiles](agent-profiles.md).

| field | meaning | default |
|---|---|---|
| `argv` | the command, a list; placeholders allowed (`{{model}}`, `{{effort}}`, `{{cwd}}`, `{{prompt_file}}`, any job variable) | required |
| `model`, `effort` | values for `{{model}}` and `{{effort}}` | none |
| `family` | model family (`openai`, `anthropic`, ...); review stages require it of their reviewers and of the writer whose output they read, and refuse equal families | none |
| `stdin` | `prompt` (the prompt goes to standard input) or `none` (pass `{{prompt_file}}` in argv) | `prompt` |
| `stdout` | `report`: stdout is the deliverable and is saved as the report; `log`: the agent writes files, stdout is a log | `log` |
| `timeout_s` | the process group is killed after this many seconds | 14400 |
| `retries` | further attempts after a failure (never after a quota stop or a protect violation) | 1 |
| `fail_patterns` | quota or rate-limit texts (case-insensitive substrings; `re:` prefixes a regex) searched in the last `fail_scan_chars` characters that the current attempt wrote to stdout and stderr; after exit status 0 only an output of at most `fail_max_chars` characters (default 1000) is searched, so a finished report or summary that mentions a limit is not a quota stop | usage limit, rate limit, quota exceeded, ... |
| `min_chars` | minimum report length (report mode) | 0 (an empty report always fails) |
| `strip_lines` | regexes; matching lines are removed from a report (a CLI banner, a sign-in warning) | none |
| `env` | extra environment variables (placeholders allowed) | none |
| `vars` | default values for placeholders of this profile, e.g. `"read_dirs": ["{{cwd}}"]`; job variables override them | none |
| `extends` | name of a profile whose fields this one inherits (`vars` and `env` are merged) | none |

## Placeholders

Templates, config values and argv use `{{name}}`. Python `str.format` is never used, so LaTeX braces are safe. An
unknown name is an error (configs are checked before anything runs). Write `{{{{` for a literal `{{`. A list value
is joined with `, ` inside text; in argv and in list fields (`seed`, `packet`, `protect`, `expect`, `check`,
`build`), an element that is exactly one placeholder with a list value expands to several elements, none for an empty
list (`"--add-dir", "{{read_dirs}}"`).

## One job: `agent_cli.py`

`run_job` renders the profile's command, sends the prompt, waits, and accepts the job only if the exit status is 0,
no fail pattern appears, the report (report mode) has at least `min_chars` characters and matches `require`, and
every expected file exists and is not empty. Otherwise it retries once. A fail pattern stops at once (status
`quota`); a change under a protected path stops at once (status `protect`) and lists the changes in
`<job>.protect.txt`. A report that fails is kept as `<report>.rejected`.

The agent runs in its own process group, through a shell wrapper that records its exit status, with stdout going to
a file; it survives the death of its driver, and a restarted driver **adopts** it (waits, then checks its outputs)
instead of starting a second copy. `<job>.running`, `<job>.exit` and `<job>.protect.json` hold this state.

From the command line it runs one job from a prompt file (`--prompt`, `--var NAME=VALUE`, `--out` for a report,
`--expect`, `--protect`, `--dry-run`), lists profiles (`--list`), or runs the **permission preflight**
(`--preflight --read FILE --run COMMAND --write-test denied|allowed`). Run `--help` for examples.

## The rollout config

| field | meaning |
|---|---|
| `workdir` | state directory, relative to the config file (`--workdir` overrides) |
| `agents` | profiles: a path, a list of paths (the first that exists), or an inline object |
| `limits` | semaphores, e.g. `{"writer": 4, "reviewer": 6}` (the defaults); a stage may name another one |
| `vars` | variables for every unit (`--var NAME=VALUE` overrides; a value starting with `[` is read as a JSON list) |
| `units` | `{"<key>": {"title", "pages", "vars"}}`; keys use letters, digits, `_ . -` |
| `stages` | the list of stages, run in this order for every unit |
| `protect` | paths hashed before and after every write and review job |
| `protect_exclude` | name globs ignored by `protect` (always: `.git`, `.lake`, `__pycache__`); list build products here |
| `packet_repos` | repositories whose git HEAD (and dirty flag) every packet manifest records |
| `packet_exclude` | name globs left out of every packet (driver files are always left out) |
| `extends` | a base config: its fields are inherited; `vars`, `units` and `limits` are merged key by key; `stages` replace |

Relative paths are resolved against the directory of the config file that wrote them. A value containing `SET-ME`
is refused as soon as a template uses it, so example configs cannot run unedited.

**Stage fields.** Every stage has `name` (unique), `kind`, and optionally `when_status` (run only for units whose
STATUS is in this list) and `vars` (stage-level variables).

| field | kinds | meaning |
|---|---|---|
| `profile` | write, review | agent profile |
| `prompt` | write | template path, or a list of paths concatenated in order |
| `seed` | write | files, directories or globs copied into the stage directory first (never overwriting) |
| `from` | write, review | a stage (of this or another config): in a write stage its outputs are copied in first; in both kinds it sets `{{prev_dir}}` |
| `reports` | write, review | the stage that `{{reports_dir}}` and `{{packet}}` refer to (default: the last review stage) |
| `expect` | write | files (relative to the stage directory) that must exist and be non-empty afterwards; name at least one the stage creates (a response table), since copied files already exist |
| `check` | write | a shell command or a list of them, run in the stage directory with raw placeholder substitution; any non-zero exit gives the writer one retry with the outputs quoted; still failing, the stage is not done |
| `inbox` | write | append the unit's `INBOX.md` to the prompt (default true) |
| `cwd` | write, review | the agent's working directory (default: the stage directory) |
| `limit` | write, review | semaphore (default `writer` for write stages, `reviewer` for review stages) |
| `protect` | write, review | protected paths added to the config's |
| `reviews` | review | `{"name": TEMPLATE}`; a template is a path, a list of paths, or `{"prompt", "foreach", "profile", "min_chars", "require"}`; with `foreach` (a list variable) one job runs per item, named `name-<item>` |
| `packet` | review | `[DEST=]PATH` entries frozen into `<stage>/packet/` before the reviews (default `proposal={{prev_dir}}`) |
| `packet_exclude` | review | extra globs left out of this packet |
| `min_chars`, `require` | review | minimum report length; a regex every report must match, normally the verdict line |
| `build` | review | like `check`, but run before the packet is frozen (e.g. to recompile the PDF from the sources being frozen); the output is frozen as `build.txt`, the manifest note names the commands, and a non-zero exit stops the stage before any review |
| `allow_same_family` | review | permit a reviewer of the writer's model family, or a profile without `family` (default false); the driver then logs a warning in `progress.log` |
| `report` | verdict | the report to read, relative to the unit directory, e.g. `d/delivery.md` |
| `pattern` | verdict | regex tried on the report's last verdict line, anchored after "Verdict" (`(?i)verdict\W+deliver\b`): a bare `DELIVER` matches "NOT YET (do not DELIVER)" |
| `verdict_line` | verdict | regex that finds verdict lines (default: a line starting with "Verdict") |
| `pass`, `fail` | verdict | the STATUS written when the pattern matches or not (defaults PASS and FAIL) |

## Template variables

| variable | value |
|---|---|
| `{{key}}`, `{{title}}`, `{{pages}}` | the unit's key, title (default: the key) and page allowance |
| `{{stage}}`, `{{stage_dir}}` | this stage's name and directory |
| `{{unit_dir}}`, `{{workdir}}`, `{{config_dir}}` | `<workdir>/<key>`, the workdir, the config's directory |
| `{{driver_dir}}` | the directory of `rollout.py`: reach the collection's assets from it |
| `{{unit_keys}}` | one line per unit of the config, `KEY — title`: the addresses writers put in `- To:` of a request |
| `{{prev_dir}}`, `{{prev_stage}}` | the `from` stage, else the last write stage before this one |
| `{{reports_dir}}`, `{{reports_stage}}` | the `reports` stage, else the last review stage before this one |
| `{{packet}}` | in a review stage, its packet; in a write stage, the packet of `{{reports_dir}}` |
| `{{common}}` | the text of the file (or files) named by the variable `common`, itself rendered |
| `{{inbox}}` | the unit's `INBOX.md`, verbatim (if a template uses it, nothing is appended) |
| `{{name}}`, `{{review}}`, `{{item}}`, `{{item_slug}}` | in review jobs: the job name, the review name, the foreach item |
| any variable | stage `vars` over unit `vars` over config `vars` (`--var` replaces config `vars` only); a variable may use other variables |

Agents also receive `ENSLOP_UNIT`, `ENSLOP_STAGE`, `ENSLOP_JOB`, `ENSLOP_STAGE_DIR`, `ENSLOP_EXPECT` (JSON list),
`ENSLOP_REPORT` and `ENSLOP_ATTEMPT` in their environment.

## State, resuming, and failures

```
<workdir>/progress.log              one line per event: UTC time, unit, stage, event
<workdir>/<key>/STATUS              the last verdict (DELIVER, NOT YET, ...)
<workdir>/<key>/INBOX.md            requests for the unit's next writer; inbox-archive.md keeps delivered ones
<workdir>/<key>/<stage>/            prompt.md (prompt-<job>.md), outputs, agent.log or <job>.agent.log,
                                    check-1.txt, prompt-retry.md, build.txt, packet/ (with manifest.json), .done
```

A stage with `.done` is skipped. In an unfinished review stage, a report that already passes its checks is kept and
only the missing jobs run. A verdict stage is recomputed only when its report changed. Delivered inbox text is
removed from `INBOX.md` (requests appended meanwhile stay) and archived. `--status` prints one line per unit.

| event | what the driver does |
|---|---|
| agent exits non-zero, times out, or misses an `expect` file | retries once, then stops the unit |
| report too short or without its required line | the same; the output is kept as `.rejected` |
| quota or rate-limit text | no retry; no new job of that profile starts in this run; rerun after the reset |
| protected file changed | no retry; no new job of any profile starts; restore the file before rerunning |
| `check` fails | one retry quoting the check output; failing again, the stage is not done |
| `build` fails | no review runs and the stage is not done (`BUILD FAILED`); fix the sources and rerun |
| driver killed | running agents continue; the next run adopts them |
| template or config error | nothing runs (exit 2) |

Exit status: 0 when every selected unit finished its selected stages, 1 otherwise, 2 for config errors.

## Writing a config for another skill

1. One unit per independent piece of work (a section, an outline unit, a referee report, a group of citations).
2. Stages as the workflow's steps: `write` for anything that produces files, `review` for read-only reports on a
   frozen packet, `verdict` to turn a report into a STATUS that later stages can test with `when_status`.
3. Measurable rules go in `check`: `check_section.sh -k .` first, so that the PDF measured is compiled from the
   section, then `check_allowance.py --pdf standalone.pdf --pages {{pages}}` for page allowances,
   `check_allowance.py --words N FILE` for word allowances, the shape and vocabulary checks of
   [`exposition-standards`](../../exposition-standards/SKILL.md) for statements and vocabulary. What a reviewer must
   see measured (a recompilation, `check_coverage.py`) goes in the review stage's `build`.
4. Templates: shared rules in a file named by `common`; reviewers print their report and end with a verdict line
   that `require` tests; the vocabulary of verdicts is the template's, the pattern is the config's.
5. Put `SET-ME` in every value the user must supply. Ship the config and the templates as assets.
6. Test: `rollout.py CONFIG --dry-run` renders every prompt (under `<workdir>/.dry-run/`) and prints every command;
   then run with `fake_agent.py` (in the collection's `tests/`, not in this skill) as every profile: it writes the
   `ENSLOP_EXPECT` files, prints reports with a verdict line, and injects the failures its docstring lists. With only
   the skill installed, copy it from the repository, or write a stand-in that reads the prompt on standard input and
   writes the files named in `ENSLOP_EXPECT` or, when `ENSLOP_REPORT` is set, prints a report longer than `min_chars`
   ending with a verdict line.

Configs here: the section cycle, whose units cover the opening part, the proof sections and the introduction (a
unit sets its task with `w1_task`, its directory with `part_dir`, extra checks with `unit_checks`), and the fix-up
([`rollout.section-cycle.example.json`](../assets/rollout.section-cycle.example.json),
[`rollout.fixup.example.json`](../assets/rollout.fixup.example.json)). Other skills list theirs in their SKILL.md.

## What the layer does not do

It does not judge any content: a passed `check` means the measured rule holds, a saved report means a reviewer
answered with enough text and a verdict line, and a STATUS is a regex on that line. It does not edit the manuscript,
merge proposals or decide findings; that is the editor's work. Process groups and adoption assume a Unix system.
