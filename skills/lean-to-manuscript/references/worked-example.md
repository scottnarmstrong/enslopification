# Worked example: the Yang–Mills campaign (2026)

In October 2026 OpenAI announced a proof, formalized in Lean 4, that four-dimensional quantum Yang–Mills theory can be
constructed as a scaling limit of Wilson lattice gauge theory. The Lean source
([`yang-mills-group/OpenAI-YM-20261028`](https://github.com/yang-mills-group/OpenAI-YM-20261028), pinned at commit
`3456e5e`) was released on 11 November 2026 without an informal proof: about one million lines in 9,477 files,
Lean 4.32.0, seventeen headline results, a verification log (type comparison, axiom check, kernel replay of 100,168
declarations), and a usage record of the declarations those results reach. The code names its objects by nicknames,
and its folders record the history of its development.

The campaign produced, in public at
[`yang-mills-informalization`](https://github.com/scottnarmstrong/yang-mills-informalization): a map of the proof at
five levels of detail and a manuscript (second draft, 265 pages), written by AI agents under the direction of a
project lead. Its process page,
[`manuscript/PROCESS.md`](https://github.com/scottnarmstrong/yang-mills-informalization/blob/main/manuscript/PROCESS.md),
is the public account of the method; this collection is the generic version of it. Everything below is taken from
that repository: its pages, data, changelog and commit history.

## Timeline (UTC, from the public history)

| when | what |
|---|---|
| 11 Nov 06:34 | Public repository opened; the statement page (formal statement, commentary, precise statement, correspondence) nine minutes later, before any outline. |
| 07:45–11:05 | 32 unit outlines drafted, compared with the Lean and edited, published as each round finished. |
| 08:56 | Compiled build released for readers. |
| 09:23 | Unit pages moved to the dependency graph read from the compiled Lean. |
| 09:50 | Manuscript skeleton published, marked as under construction. |
| 13:15 | First drafts of the opening part rejected for their shape ([L9](lessons-learned.md#l9)); statements fixed first, in natural form, with length limits. |
| 14:51 | Part I rewritten: definitions by formula where they are used, short statements in natural form. |
| 15:39–16:03 | Part I revised after the owner, fresh-reader, prose-truth and final reviews. |
| 17:10–17:45 | Two pilot sections integrated for review and handed to the project lead. |
| 19:58–20:50 | The other eight proof sections written and through their review cycle. |
| 20:44 | Main theorem restated as five clauses; its first version listed about forty labels ([L10](lessons-learned.md#l10)). |
| 20:56–21:14 | Introduction and abstract; first complete draft, 226 pages. |
| 21:42–23:31 | Second and third rounds of cross-section repairs; the referees' suggestions applied after adjudication and confirmation; a typographic pass over every page. |
| 12 Nov 11:38–12:11 | Second draft, 265 pages: Part I rebuilt around the main theorem and the strategy of the proof (the main theorem on page 14), the literal formal statement and the constants at the end of Part I, Part II revised after expert and independent reviews; the correspondence table of the whole manuscript (3,232 rows) published. |

The speed is a property of the tools, not evidence of quality. Each speed-up (parallel writers, a driver that runs
whole review cycles unattended) produced a failure that only a later check found: Lean-shaped statements, a main
theorem that listed labels, parallel sections citing each other for more than was stated
([L21](lessons-learned.md#l21)).

## Phase by phase

**Map.** The compiled graph: 2,263,533 reference pairs between project declarations; 74,093 declarations in the
closure of the seventeen roots, against 74,115 in the authors' record after attribution of auxiliaries; 50
differences explained ([L4](lessons-learned.md#l4)). The earlier text graph had about 57,000 wrongly resolved
references and missed 1.36 million implicit ones ([L3](lessons-learned.md#l3)).

**Coarse-graining.** Ownership by dominators, scales from 100 to 3,200 lines, shared machinery grouped, then 8 parts
and 32 units cut along the mathematics. The ultraviolet construction is about 70% of the code. 2,424 candidate
statements in 106 groups were read by two independent readers (κ = 0.72 on their importance labels); 989 key
statements cover the 413,085 attributed lines. Each unit has an outline of 3 to 10 pages, detailed notes, and a Lean
map with links to exact lines; a glossary translates the nicknames, with confidence labels; a provenance page says
which components follow which earlier programme, which are standard and which appear new.

**Spine.** Before any prose, every statement of Part I was fixed in one document and approved by the project lead;
the first version copied the Lean's shape and was rejected, and the statements were restated in natural form, as
fifteen principal statements, with a clause map ([L9](lessons-learned.md#l9)).

**Writing.** Part I (setting, renormalization, the continuum limit, stress and rotations, phases and
reconstruction, trace and products, the main theorems, constants and the order of their choice) and Part II
(Sections 10–19). Each section: proposal, integration, frozen snapshot, owner and mathematical, fresh-reader and
prose-truth reviews, response table, re-check, delivery review. The process page planned Part II at about 120 pages;
the first draft had about 190 and the second about 220, most of the growth in the ultraviolet sections
([L23](lessons-learned.md#l23)).

**What the reviews caught.** A main theorem weaker than the Lean ([L11](lessons-learned.md#l11)); a pilot assuming
two unproved inputs and another missing a hypothesis ([L19](lessons-learned.md#l19)); the editor's own integration
errors ([L18](lessons-learned.md#l18)); fluent false sentences ([L20](lessons-learned.md#l20)); citations between
sections that asked more of the cited statements than they said ([L21](lessons-learned.md#l21)); real gaps found by
the referees and filled from the Lean ([L25](lessons-learned.md#l25)). None would have been caught by compiling the
text.

**Publication.** Each level of the map and each section carries a status with a published meaning; the process page
says what the checks establish and what they do not; the abstract names the three kinds of checking separately
([L30](lessons-learned.md#l30)). The correspondence table of Part I had 657 rows and 807 Lean names, all in the closure
of the main theorem; the table for the whole manuscript (3,232 rows) was published with the second draft.

## What remained open at the time of writing

The project lead's reading of each part before any section is marked *checked*, and the removal of the
under-construction markers. The manuscript's own status page is the current record.
