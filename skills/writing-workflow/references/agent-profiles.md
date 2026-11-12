# Agent profiles: command lines, models and permissions

A profile is one way of running an agent: a command line, a model, a reasoning effort, a model family and the
permissions the command line grants. Field reference: [driver](driver.md#agent-profiles). Starting point:
[`agents.example.json`](../assets/agents.example.json).

## The arrangement that worked

In the Yang–Mills campaign (2026) the writers came from one model family and the reviewers from another, each
reviewer in a fresh context with read-only tools. **The writer and the reviewer of a packet always came from
different model families:** a model that wrote a proof tends to confirm its own reading. The example profiles run
writers at extra-high reasoning effort for drafts and revisions and at high effort for last fixes and fix-ups
(`writer-high`). Give every profile a `family`: `rollout.py` refuses a review stage with a profile that has
none, or with a reviewer of the writer's family, unless the stage sets `allow_same_family` (then it warns in
`progress.log`).

## Swapping the command line or the model

A command line can serve as an agent if it runs without interaction, takes the prompt on standard input or from a
file, and exits when done. A writer writes its files and may print anything; a reviewer must print its whole report
on standard output (`"stdout": "report"`).

- **Another model of the same CLI:** change `model` and `effort`, or add a profile with `"extends"`.
- **Another CLI:** write its `argv`. For a CLI that reads a prompt file, set `"stdin": "none"` and put
  `{{prompt_file}}` in `argv`. If it prints progress text before the answer, prefer its option that prints only the
  final message, or remove fixed banner lines with `strip_lines`.
- **Its quota messages:** copy the exact text the CLI prints when a usage or rate limit is hit into
  `fail_patterns`, and keep such phrases out of prompts (the driver searches the end of the output for them).
- Check the flags against `--help` of the installed version; they change between versions.

Then run `agent_cli.py --agents agents.json --list` and `rollout.py CONFIG --dry-run`, which print every command
line as it will run.

## Least privilege

| role | needs | grant | deny |
|---|---|---|---|
| writer | read the manuscript, the spine, the Lean and the dependency database; write its proposal; compile a standalone PDF | a sandbox whose writable root is the stage directory (Codex CLI: `--sandbox workspace-write -C {{cwd}}`) | writing anywhere else, version control, network |
| reviewer | read the packet, the Lean and the database; compare files; render pages | read tools, `grep`, `wc`, `diff`, `sqlite3 -readonly`, `pdfinfo`, `pdftotext`; `--add-dir` for every directory outside its working directory | every tool that edits or writes: `Edit`, `Write`, `NotebookEdit`, and shell commands that can write (`sed -i`, `python`, `sqlite3` without `-readonly`) |

Reviewers never need write permission: they print the report and the driver saves it. `diff` only prints; the
confirmation reviews of [`referee-adjudication`](../../referee-adjudication/SKILL.md) use it to compare a proposal
with the live file it replaces, and a reviewer denied a tool that its prompt asks for answers without it, unmarked. To look at rendered pages, a
reviewer can read PDF pages with Claude Code's Read tool; a CLI without that needs a renderer such as `pdftoppm`,
which writes image files, so allow it only with an output directory outside the packet (a file added to the packet
shows up in `verify_packet.py`).

A sandbox can block a tool the writer needs (a TeX installation that writes caches, for example). Writers that run
with the sandbox bypassed (`writer-unsandboxed`), each in a dedicated directory, need `protect`: list the canonical
manuscript, the frozen spine, the style file and the Lean source, and any change there during a job fails the job and
stops the run. `protect` cannot tell who made a change, so the editor integrates between runs, not during one; build
products (`*.aux`, `*.log`, `*.pdf`) belong in `protect_exclude`.

## Preflight before every round

Reviewer permissions fail silently: a reviewer asked to write a report file it cannot write, or to query a database
its permissions block, still answers, and nothing marks the answer as incomplete. A checker whose every database
query is refused gives verdicts that rest on the manuscript text alone, and at most a sentence in its report says so
([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)).
Before a round, test each profile as configured:

```
agent_cli.py --agents agents.json --profile reviewer --cwd <a stage directory> --preflight \
  --read <a Lean source file> --read <a file of the manuscript> \
  --run "sqlite3 -readonly <graph.sqlite> 'select count(*) from nodes where used = 1'"
```

The agent must print the first line of each file and the output of each command, which the script compares with the
truth; it must fail to create a file (`--write-test denied`, the default for report profiles) or succeed
(`allowed`, the default for writers). Pass `--var read_dirs=...` when the profile uses `{{read_dirs}}`. A failed
preflight is fixed in the profile, not in the prompt. Every review prompt also asks the reviewer to list the sources
it actually consulted and any it could not reach, so a blocked tool shows in the report.

## Quotas and restarts

A quota or rate-limit message stops that profile's jobs for the run without a retry; other profiles continue. After
the reset, run the same command again: finished stages are skipped, kept reports reused, running agents adopted. In
overnight mode, record the stop and the restart in the morning list
([`lean-to-manuscript`](../../lean-to-manuscript/SKILL.md)).
