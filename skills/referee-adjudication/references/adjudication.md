# The referee round: reports, adjudication, application, confirmation

The Yang–Mills campaign (2026) ran this round on its complete first draft: three referees, adjudication of every
suggestion against the text and the Lean, application by the section writers, and confirmation before
integration.

## 1. Referee reports

- **One frozen snapshot.** Freeze the whole draft, compiled PDF and sources, with `make_packet.py` of
  `writing-workflow` (a manifest of SHA-256 hashes). Every report and every adjudication names that snapshot.
  Writers who apply the results later locate places by quoted content, not only by line number.
- **Scopes.** Give each referee a scope that one reading can cover completely: in the campaign, Part I
  (Sections 1–9), the ultraviolet Sections 10–14, and Sections 15–19. Each referee has the whole snapshot, to
  check what its scope cites, and reports on its scope only.
- **Models.** Use a model family other than the writers' and, where you can, more than one model.
- **Format** (`assets/prompts/referee.md`): first the sources consulted and a coverage statement; an overall
  assessment; numbered suggestions, each with category, location, problem, why it matters and the exact change;
  what the referee recomputed and found consistent; the last line `Suggestions: N`, which feeds the completeness
  check below.
- **Coverage statements matter.** A referee reads what lies outside its scope only through spot checks of what
  its scope cites, and says so. A text that every referee spot-checked has been read closely by nobody in the
  round.
- **Reviewers print their reports.** Read-only reviewers that are asked to write a file fail silently; the
  driver saves standard output and checks a minimum length
  ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)). Run with
  `assets/rollout.referee.example.json`.

## 2. Adjudication

Referees find real gaps; their fixes are often wrong in detail
([L25](../../lean-to-manuscript/references/lessons-learned.md#l25)), so expect many suggestions to be accepted
only with corrections.

**Who.** One adjudicator per report, separate from the referee and from the writers, fresh context, read-only, with
the snapshot, the referee report, the Lean at the pinned commit and the compiled graph. Test the profile's
permissions before the round: the adjudicator must be able to run its database queries.

**The questions, for every suggestion and sub-item** (`assets/prompts/adjudicator.md`):

1. Is the diagnosis true of the text? Quote it, by file and line.
2. Does the proposed change say exactly what the Lean proves, never more? Only declarations with `used = 1`
   count ([L5](../../lean-to-manuscript/references/lessons-learned.md#l5)); a stronger statement needs a named
   declaration that proves it.
3. Does it break anything: cross-references, the main theorems, a statement elsewhere that relies on the old
   wording, the shape caps?
4. Verdict.

**Verdicts, with examples.**

| verdict | meaning | example |
|---|---|---|
| `ACCEPT` | correct and safe as proposed | a missing citation of a choice made in an earlier lemma |
| `ACCEPT MODIFIED` | the diagnosis is right, the change is not; the adjudication gives the corrected text | a new proposition requested in norms that the Lean does not use: the adjudication states it where the Lean proves it, and adds the other places (a table row, a sentence of the introduction) that need the same change |
| `REJECT` | the diagnosis is false, or the change claims more than the Lean, or breaks something named | moving rows of a table that the text cites by row; deleting a convention that the transcription of the formal statement needs |
| `AUTHOR` | the change alters a main theorem or another approved statement, the scope of the result, removes a proved result, or touches authorship | deleting a proved lemma; restructuring the opening part; any change inside an approved main theorem, even a grammatical one |

A split verdict goes in one cell: `ACCEPT MODIFIED (a-c); REJECT (d)`. Some suggestions ask for more than the Lean
proves, such as a law for every case where the Lean proves it only for a selected one: the adjudication says so and
rejects them, and the author is told that they were declined.

**Output, in this order.**

1. *Sources consulted*, first, with every source the adjudicator could not use: a verdict that rests on a blocked
   query must say so where the reader starts ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)).
2. *Lean facts the verdicts rely on*: each with declaration names, file and line, and whether `used = 1` was
   confirmed by a query. Verdicts rest on a few facts (for instance, what a formal definition does not require);
   listing them first lets the confirmation reviewer and the author check each fact once.
   `adjudication_summary.py --strict` enforces this order.
3. *Verdicts*: one table `| # | Verdict | Reason | Where to edit |`, one row per suggestion or sub-item.
4. *Exact edits* for every `ACCEPT` and `ACCEPT MODIFIED` item, located by file, line and quoted phrase.
5. *Interactions*: items that must land together, items owned by another section.

**Completeness check.** Run

```
adjudication_summary.py adjudication/*/adjudicate/adjudication.md \
    --expect part1=<N> --expect uv=<N> --expect rest=<N> --tsv verdicts.tsv
```

with each N taken from the referee's `Suggestions: N` line; each report is named after its unit. Exit 1 means a
suggestion has no verdict, a verdict is unknown or an item has two verdicts. Count numbered suggestions and decided
items separately: with their sub-items, the suggestions of a report can need many more decisions. Run with
`assets/rollout.adjudication.example.json` (one adjudicator per report).

## 3. AUTHOR items

Each `AUTHOR` item goes to the morning list ([L35](../../lean-to-manuscript/references/lessons-learned.md#l35)):
the question in one sentence, the adjudicator's recommendation, the provisional default (not applied) and how to
revert it. `adjudication_summary.py --part author` prints the list, including the AUTHOR part of a split verdict,
and warns about notes such as "(final wording: author)" that hide one. A provisional default keeps the text
reversible; it does not predict the ruling. Never let the text of an accepted item decide an AUTHOR item in
passing.

## 4. Application by section

- **One writer per section**, in its own directory, on copies of the section's files
  (`assets/prompts/apply-adjudication.md`, stage `f1` of `assets/rollout.apply.example.json`).
- **Exactly as adjudicated.** `ACCEPT` as the referee proposed it; `ACCEPT MODIFIED` with the adjudication's exact
  text; never `REJECT` or `AUTHOR`. `adjudication_summary.py --part writers` lists each section's items.
- **Other sections' items** are written as proposals to the owner (a cross-edits file) and routed by the editor
  (`cross-section-consistency`). Edits that depend on each other land in one commit: a Part I table row and the
  Part II lemma that cites it.
- **Repairs from the Lean's own argument.** In the Yang–Mills ultraviolet sections the round filled real gaps
  this way: a single-valued step map, the convergence of the free forms, the leading map of the marked expansion,
  the block-to-fine comparison, the torus localization, and a per-step period requirement missing from the table
  of constants.
- **Word caps never move hypotheses.** Split the statement or define objects earlier
  ([L13](../../lean-to-manuscript/references/lessons-learned.md#l13)).
- **Response table**: one row per item: applied (exact edit), not in this section, or could not apply (reason).

## 5. Confirmation review

A separate reviewer reads a frozen packet of the proposal files and the live files they replace
(`assets/prompts/confirmation-reviewer.md`, stage `c1`), lists its sources first, runs five checks (edits
against the adjudication; statements against the Lean; explanatory sentences; references and mechanics;
cross-section proposals) and ends with `Verdict: INTEGRATE` or `Verdict: NOT YET`; a `verdict` stage (`v1`) reads
that line.

The problems a confirmation finds are of a kind that compiles and reads well:

- a lemma stronger than the Lean because a hypothesis, a quantifier ("there is N₀") or a clause was moved after
  `\end{lemma}` to meet the word cap ([L13](../../lean-to-manuscript/references/lessons-learned.md#l13));
- a new definition narrower than the Lean's, the narrowing coming from the adjudication's own wording;
- a new sentence claiming that a row of a table gives a bound it does not state, which would settle an AUTHOR
  item without the author;
- `\input` paths rewritten by the copy step and kept by the writer.

A fix-up writer applies the exact fixes, and the editor integrates after the re-check. A reviewer whose lookups
were blocked says so in its sources and confirms `used = 1` by query only for the names it could; run the
remaining queries before sign-off ([L22](../../lean-to-manuscript/references/lessons-learned.md#l22)).

**Fix-up and re-check.** The apply config runs them for every unit marked NOT YET: `f2` copies the proposal of
`f1` and applies the fixes of `c1/confirm.md` (`assets/prompts/apply-fixup.md`); `c2` confirms again, with the
first report in its packet and a table of the required fixes, RESOLVED or NOT RESOLVED (`reconfirmation.md`
appended to the confirmation prompt); `v2` writes the status. A unit still NOT YET goes to the editor, or to
another round under new stage names (a stage with a `.done` marker never runs again).

## 6. Integration

The editor integrates the confirmed proposals (`writing-workflow`), compiles, runs the shape and vocabulary
checks of `exposition-standards`, and compares the main theorems with the approved text:

```
compare_statements.py approved/ manuscript/ --labels thm:main,thm:formal --allow-label-changes
```

Check the main theorems byte for byte after every pass. Update the status table and the changelog in the words
`honest-publication` prescribes: say that every suggestion was adjudicated against the text and the Lean before
being applied, and that a separate agent review compared the applied changes with the adjudication before
integration; never that the text was "refereed" in the sense of a journal.
