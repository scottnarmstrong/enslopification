# enslopification

**Lean → mathematics.** Agent skills that turn a completed Lean formalization into a proof written in natural
language: a paper that a mathematician can read, check by hand and learn from, which claims nothing the Lean does not
prove and says exactly what was checked and how.

The skills work with Claude Code and OpenAI Codex. They grew out of the campaign that turned OpenAI's Lean
construction of four-dimensional quantum Yang–Mills theory, about one million lines released without an informal
proof, into a [readable manuscript](https://github.com/scottnarmstrong/yang-mills-informalization).

## The name

*Formalization* takes mathematics written by people and turns it into Lean. *Enslopification* goes the other way. It
starts from a Lean development, today often written by an AI system and hundreds of thousands of lines long, and turns
it back into mathematics: definitions, statements and proofs in natural language.

The writing is done by AI agents, and AI-written text has an unflattering name: *slop*. The name is a joke at our own
expense, and it is also the statement of the problem. An agent simply asked to explain a formal proof produces
exactly that: statements shaped like the code, a main theorem that lists forty labels, fluent sentences that nobody
checked. Everything in these skills exists so that the result is not slop. The Lean is the authority for every
statement; statements are measured by programs; every section is reviewed by agents of a different model family from
its writers; and the publication says precisely what was verified, and by whom.

## Why it matters

AI systems now produce kernel-checked proofs of research-level theorems, and they are released faster than anyone can
read them. In 2026 alone, OpenAI has published these Lean developments:

| | Lean development | released with |
|---|---|---|
| June | [cdc-lean](https://github.com/openai/cdc-lean): the cycle double cover theorem for bridgeless multigraphs | no paper in the repository |
| August | [ten-proofs](https://github.com/openai/ten-proofs): ten results, from sphere-packing bounds and binary codes to a non-sofic group and multicolor Ramsey numbers | a paper and reasoning walkthroughs |
| September | [LongGapsBetweenPrimes](https://github.com/openai/LongGapsBetweenPrimes) and [PrimeGaps186](https://github.com/openai/PrimeGaps186) | a paper; a numerical certificate, with the second development conditional on three stated input axioms |
| September | [NavierStokesAndEuler](https://github.com/openai/NavierStokesAndEuler): finite-time blowup for the Navier–Stokes and Euler equations | two papers |
| October | [math](https://github.com/openai/math): 721 manuscripts in 373 families | a Lean library for some of them |
| October | [the construction of four-dimensional quantum Yang–Mills theory](https://github.com/yang-mills-group/OpenAI-YM-20261028), about one million lines | no informal proof at all |

A kernel check settles one question, and settles it completely: the formal proof proves the formal statement. It does
not say why the theorem is true, which ideas carry the proof, whether the formal definitions mean what mathematicians
mean by the same words, or how the method might be used on the next problem. Mathematics advances through
understanding, and a proof that nobody can read cannot be taught, judged for its ideas, generalized or built upon.

Reading the Lean directly does not scale. The Yang–Mills development has about a million lines. Its declarations carry
the code's own nicknames (`Repeat.Meadow.flights`, `Repeat.Trio.frost`, `Almanac.cards`) instead of the terms of the
literature; it contains alternative routes that the main theorem never uses; and its statements have the shape the
proof assistant needs, not the shape a mathematician would choose. When a paper accompanies the code, the two can
drift apart, and then the Lean, not the paper, is the record of what was proved.

Someone has to turn these artifacts back into mathematics. These skills are a method for doing it with agents, at the
scale of a million lines, without giving up the guarantee that made the artifact worth reading.

## Examples

### Yang–Mills: the worked example

OpenAI's Lean construction of four-dimensional quantum Yang–Mills theory appeared at the end of October 2026 with no
informal proof. The campaign described in these skills produced
[yang-mills-informalization](https://github.com/scottnarmstrong/yang-mills-informalization), in collaboration with
Martin Hairer's [humanise-yang-mills](https://github.com/hairer/humanise-yang-mills) project:

- the compiled dependency graph of the development and the closure of the main theorem, about 410,000 lines of the
  development's own code;
- a public map of the proof at five levels of detail, from a one-page statement of the theorem to outlines of every
  unit with links into the Lean;
- a manuscript ([second draft](https://github.com/scottnarmstrong/yang-mills-informalization/blob/main/manuscript/main.pdf),
  265 pages): Part I states the main theorem on page 14 and explains the architecture of its proof, Part II gives the
  proofs;
- a [correspondence table](https://github.com/scottnarmstrong/yang-mills-informalization/blob/main/manuscript/correspondence.tsv)
  of 3,232 pairs, each numbered statement against the Lean declarations it rests on;
- a [process page](https://github.com/scottnarmstrong/yang-mills-informalization/blob/main/manuscript/PROCESS.md)
  recording every stage.

Each skill uses this campaign as its example, with numbers: what was measured, what failed, and what fixed it.

### Navier–Stokes

OpenAI's [NavierStokesAndEuler](https://github.com/openai/NavierStokesAndEuler) release accompanies a 166-page paper
on finite-time blowup for the Navier–Stokes equations. An earlier campaign, run before these skills existed, rewrote
that paper for specialists in partial differential equations with the Lean as the authority: it extracted the closure
of the two final theorems (about 31,500 declarations), matched each of the paper's 78 numbered statements to Lean
declarations, audited the load-bearing statements against the code, and wrote the new text from proof notes taken on
the Lean. Two of its lessons became rules here: build the outline from the dependency structure of the Lean, not from
the paper's citation graph; and keep the correspondence with the Lean in a separate table, out of the text of the paper.

### Smaller developments

Most releases are much smaller than Yang–Mills, and most come with a paper. The campaign skill
[sizes the work](skills/lean-to-manuscript/references/phases.md#sizing-the-campaign) by the closure of the main theorem:
a development of up to about 50,000 lines calls for a statement page, a manuscript of up to about 60 pages, one referee
and a correspondence table, not five public levels and three referees. What is never dropped, whatever the size: the
compiled graph, natural statements checked against the Lean, reviewers from a different model family, and an exact
account of what was checked. When a release comes with a paper, the paper is treated as a draft to be checked against
the Lean, not as the authority.

## Principles

- **The Lean is the authority.** The manuscript claims nothing the Lean does not prove: weaker or more natural forms
  are allowed, stronger never. Only declarations in the closure of the main theorem count as evidence.
- **Natural statements, measured.** Statements are written for a mathematician, not transcribed from the code, and
  their shape and length are checked by programs after every round.
- **Writers propose, one editor integrates, others review.** Reviewers read frozen snapshots, come from a different
  model family than the writers, and never edit.
- **Every finding gets a decision.** Nothing is applied unadjudicated; nothing is deleted from a response table.
- **Say exactly what was checked.** The kernel checks the formal proof; agents compared statements with
  declarations; the prose is not machine-checked, and it is not a referee's report until a human referee reads it.

## The skills

| Skill | Use it for |
|---|---|
| [`lean-to-manuscript`](skills/lean-to-manuscript/) | **start here**: the whole campaign — phases, roles, the author's decisions, budgets, when to stop and ask, overnight mode with a morning list; the shared [lessons learned](skills/lean-to-manuscript/references/lessons-learned.md) |
| [`lean-dependency-graph`](skills/lean-dependency-graph/) | compiling the development and releasing the compiled build; extracting declarations and references from `.olean` files; the closure of the headline results; comparison with the authors' usage record; a SQLite graph and how to query it |
| [`coarse-graining`](skills/coarse-graining/) | parts and units owning every declaration, key statements, unit outlines with measured length budgets, Lean maps with exact links, summary and architecture pages, glossaries of the code's nicknames, provenance |
| [`statement-spine`](skills/statement-spine/) | fixing every statement before prose: natural form instead of Lean shape, the clause map that proves nothing was lost, freezing with the author, the drift protocol, main theorems that state rather than list |
| [`exposition-standards`](skills/exposition-standards/) | the binding style rules with their numbers, the detail standard, terminology from the literature, and the automatic checks (shape, vocabulary, compilation, pages) |
| [`writing-workflow`](skills/writing-workflow/) | writers propose and one editor integrates; frozen review packets; owner, mathematical, fresh-reader, prose-truth and delivery reviews; response tables; pilots; the roll-out driver and the agent command-line layer |
| [`cross-section-consistency`](skills/cross-section-consistency/) | sections written in parallel: routed inputs, the routed-inputs check, repairs on both sides, convergence |
| [`referee-adjudication`](skills/referee-adjudication/) | independent referee reports, adjudication of every suggestion against the text and the Lean, confirmation reviews, typography passes, editorial plans merging human and agent reviews, comparison with other drafts |
| [`honest-publication`](skills/honest-publication/) | the public repository by levels of detail, disclosure of AI authorship, precise language for what was checked, status tables and markers, correspondence tables, what not to claim |

Each skill is a folder whose `SKILL.md` both Claude Code and Codex read, with `references/` for detail, `scripts/`
for tools and `assets/` for templates; `agents/openai.yaml` is Codex-only interface metadata.

## How they fit together

```
lean-to-manuscript (phases, decisions, budgets)
 ├─ 1 lean-dependency-graph ── 2 coarse-graining ── 3 statement-spine ── 4 exposition-standards
 ├─ 5–7 writing-workflow (opening part, pilots, roll-out) ── 8 cross-section-consistency
 ├─ 10–11 referee-adjudication (referees, typography, editorial pass)
 └─ 9, 12 honest-publication (introduction, disclosure, status, correspondence)
```

Every skill cites the shared [lessons learned](skills/lean-to-manuscript/references/lessons-learned.md) by ID: the
concrete failures of the Yang–Mills campaign (a main theorem that listed about forty labels and passed every
faithfulness review; outlines that grew 4.4 times past their template; Lean-shaped statements nearly a page long;
parallel sections citing each other for more than the cited statements said; …) and the fix adopted for each.

## Installation

Clone the repository and link each skill into your agent's skills directory:

```bash
git clone https://github.com/scottnarmstrong/enslopification.git
cd enslopification

# Claude Code
mkdir -p ~/.claude/skills
for s in skills/*; do ln -sfn "$(pwd)/$s" ~/.claude/skills/"$(basename "$s")"; done

# Codex
mkdir -p ~/.agents/skills
for s in skills/*; do ln -sfn "$(pwd)/$s" ~/.agents/skills/"$(basename "$s")"; done
```

Install the skills together: they link to each other's references, and the drivers in `writing-workflow` are used
by several of them. **Install [math-paper-skills](https://github.com/amelieloher/math-paper-skills) as well**: these
skills rely on its `latex-math-writing` (prose, typesetting and the banned-word list) and `math-paper-campaign` (the
general drift protocol, packets, the final audit and the completion test) instead of repeating them.
[LeanAutoformalizationSkills](https://github.com/scottnarmstrong/LeanAutoformalizationSkills) is optional (statement
audits of single declarations). Then ask your agent, for example, "use lean-to-manuscript to plan a paper from this
Lean development", "use lean-dependency-graph to build the compiled graph of this project", or "use writing-workflow
to run the review cycle on Section 12".

**Requirements.** The scripts use Python 3.10+ (standard library only), bash, SQLite, and for some steps Lean 4
with Lake, `latexmk`, `pdfinfo`/`pdftoppm` and `pandoc`. The drivers call agent command-line tools (Codex CLI,
Claude Code) through profiles you configure; nothing is hard-wired to one vendor. `tests/run_all.sh` runs every
script's smoke test.

## Companion collections

- [math-paper-skills](https://github.com/amelieloher/math-paper-skills): `latex-math-writing` for the prose of every
  section, `math-paper-campaign` for packets, the drift protocol and the final audit (its reference
  `from-formalization.md` is the short version of this collection), `math-figures`, `visual-paper`.
- [LeanAutoformalizationSkills](https://github.com/scottnarmstrong/LeanAutoformalizationSkills): the opposite
  direction, from a paper to Lean (`lean-orchestrator`, `lean-statement-audit`, `build-proof-dependency-graph`,
  `lean-public-release`).

## Licence

© 2026 Scott Armstrong. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); see
[LICENSE](LICENSE). The Lean developments cited as examples belong to their authors and are under their own licences.
