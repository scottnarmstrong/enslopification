# Author decisions, when to ask, overnight mode

The author owns the mathematics the manuscript claims, its shape, its length and its name. The editor proposes,
with a recommendation and measured consequences, and records each ruling with its date in `BRIEF.md`. Everything
else the editor decides and records.

## Decisions for the brief

Propose each with a recommended option; the Yang–Mills choice is given as an example.

| # | decision | Yang–Mills choice |
|---|---|---|
| D1 | **Principal results.** Which theorems the paper states, and in which form. | Theorem A: the existence statement exactly as formalized. Theorem B: the detailed construction as far as the Lean proves it. In the second draft: Theorem B first, the formal statement in a section of its own at the end of Part I ([L15](lessons-learned.md#l15)). |
| D2 | **Authority and the formal artefacts.** The pinned commit and the closure that counts as "the Lean"; whether Lean names may appear in the text. | The closure of the headline results at the pinned commit. No Lean names or formal artefacts in the text; one paragraph on the formal verification; a correspondence table published separately. |
| D3 | **Citation policy.** What is cited rather than proved. | Standard results cited exactly (statement, hypotheses, numbering checked against the source), even where the Lean proves them itself. |
| D4 | **Workers.** Models, reasoning effort, parallelism. | Writers from one family, reviewers from another, never the same family for writer and reviewer of a packet. |
| D5 | **Authorship and disclosure.** Author line; how the formal source and the AI systems are credited. | Author line blank; the abstract ends by saying the paper was written by AI agents from the Lean code ([L31](lessons-learned.md#l31)). |
| D6 | **Visibility.** Written in public or private; where the working files live. | Written in public; the working records kept in a separate private repository. |
| D7 | **Pilots.** Which two sections calibrate the rest. | One section on each side of the proof (the ultraviolet construction, the infinite-volume limit). |
| D8 | **Reader and detail.** The named reader and the detail standard. | A mathematician in constructive field theory or probability, checking each step with pen and paper in reasonable time. |
| D9 | **Length.** Total pages, share per part; who may exceed. | Planned on the process page: Part I about 30 pages, Part II about 120; the first draft had 226 pages and the second 265 ([L23](lessons-learned.md#l23)). |
| D10 | **Markers.** Under-construction markers and when they come off. | A README banner, a title-page note and a running header; removed only when the whole text is checked. |

## Later decisions that are always the author's

- Approving the spine and its structural decisions; every change to a frozen statement (drift), including
  rewordings meant only for readability.
- The wording of the main theorems.
- The scope of the result: anything that adds, removes or weakens a conclusion, a quantifier or a uniformity.
- Removing a proved result from the text.
- The level of detail and the length after reading the pilots and each finished part; any overrun of an allowance by
  more than a page, with measured options ([L23](lessons-learned.md#l23)).
- Adopting another draft's architecture; renaming a term the author or a human reader uses.
- Authorship, disclosure wording, publication, and removal of markers.
- Expensive or risky resource use: compiling a very large development, long multi-agent runs.

Do not ask about what the Lean settles (look it up, `used = 1` only), routine repairs, or reversible editorial
choices: take the choice, record it, and list it in the morning list if the author might disagree.

## How to put a decision

One message per decision, standing on its own: the question, the options with their measured consequences (pages,
statements affected, risk), a recommendation, and what happens by default. Keep the evidence in a file the author can
open (a diff of the statement, the page counts). Ask several independent questions at once rather than one per
turn.

## Overnight mode and the morning list

Overnight mode starts when the author says so and ends when the author replies. In it:

- Work through every step that is reversible: reviews, adjudications, repairs on proposals, integration of
  delivered sections, typography, measurements, status pages.
- Take a provisional default for each author decision and record how to revert it; do not apply a decision that
  cannot be reverted.
- Never change a frozen statement or a main theorem, delete a proved result, change the authorship or disclosure,
  make a repository public, or publish a new kind of claim.
- Keep main theorems byte-for-byte identical to the approved text; check after every pass.
- Commit at green boundaries if commits are authorised; push only what the author has authorised to be public.
- Write the morning list as you go, not at the end.

`MORNING.md` has four parts, in this order:

```markdown
# Morning list (overnight mode, <start date> → <end date>)

## Summary (written at <time>)
State of the manuscript in three to six lines: pages (measured), build status, automatic checks, the public
commit, what changed overnight and in which order.

## Rulings needed
1. **<question in one line>.** Context in two lines; the options; the provisional choice already taken (or "not
   done"); how to revert it. Evidence: <file>.
2. …

## For information
- Items resolved overnight that the author may want to know about, each with its evidence.

## Overnight log
- <time> <event, one line>
```

When the author replies, record each ruling in `BRIEF.md` with its date, apply it, and move the list to an archive
section.

## When the author's rule and a check disagree

The author's latest explicit ruling wins over the style file and over any check, and is then written into the style
file so that the checks agree with it. Example: an author may rule that page figures for the hardest sections are
guides, not caps; the style file then records the rule and the reason, and writers report measured length with
reasons instead of cutting ([L23](lessons-learned.md#l23)).
