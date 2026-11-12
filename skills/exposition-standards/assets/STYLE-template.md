# Style: binding rules for <manuscript>

Adopted <date>. Every writer and every reviewer reads this file before any other. Rules marked
[measured] are enforced by scripts after every integration; the others by a dedicated reviewer.
General prose and typesetting follow the `latex-math-writing` skill (writing rules, house style);
this file adds what the formal source makes necessary and overrides nothing in it.

## 0. The author's calibration (binding; newest first)

Turn every comment of the author on a pilot or a draft into a general rule here the same day,
with the example it came from, and say what enforces it. Paraphrase; do not paste private remarks.

- <date>, on <section, page>: <the comment, paraphrased> → rule: <...> → enforced by <check | reviewer>.

## 1. Model

- Exemplar: <paper(s)>; patterns to copy and features not to copy in `EXEMPLAR.md`. Copy
  patterns, never statements.
- Order of the opening part: <objects by formula → the step → the iteration → the limit → the
  deduction of the main theorem → the constructions>.
- Detail: `DETAIL-STANDARD.md` (named reader; one line or a citation / written out / never).

## 2. Statements

- One idea per statement, in its natural form, not the shape of its proof or of the Lean.
- [measured] Words: target 100, cap 150 (theorem, proposition, lemma, corollary). Over the cap =
  not done: split it, or set the objects up before it.
- [measured] At most 4 cross-references or tags per statement; a range counts once.
- [measured] Main theorems: at most 250 counted tokens, formulas included, and at most 8
  references. Their conclusions are clauses with formulas, never a list of labels; the map to the
  supporting results goes in the text after the theorem.
- Setup outside: objects, notation and standing hypotheses in the prose before the statement.
- Quantifiers first, conclusion displayed, every constant declared with its dependence; no
  trailing conditions; no commentary inside the statement.
- No packaging statements ("there is a family such that the following assertions hold").
- A statement carries every hypothesis its users rely on. A cap is met by splitting or by
  defining objects earlier, never by moving a hypothesis into the prose.
- A principal statement gets one or two sentences on its role before it and a precise pointer to
  its proof after it.

## 3. Definitions

- [measured] Words: target 120, cap 200; at most 6 references.
- Only what the reader needs at that point; machinery is defined where it is used.
- Concrete, by formula, with one sentence of purpose and one to three interpreting sentences.
  Never a translation of a Lean structure, never a list of types.
- Trace every chain: a sum has its index set and summands, a recursion its initialization and
  update. Each item of a property list has its own label.
- A symbol is introduced only if a displayed definition, statement or identity uses it.

## 4. Proofs

- A long proof opens with "Idea of the proof. Step 1 … Step k", one display per step.
- Dependency sentences: "By Lemma~\ref{...}, which bounds <what>, <consequence>." Never "Use
  Definitions … and Lemmas …", never a sentence that is a list of references.
- One interpreting sentence after a dense estimate: what is small, and which loss it pays for.
- About one numbered lemma per page. A proof longer than three pages is split at a genuine
  intermediate statement, or its allowance is renegotiated before drafting.
- Standard results are cited exactly: name, hypotheses, numbering, checked against the source.
- Repeated cases: one representative, the reason the others are identical; never for a main
  estimate.

## 5. Vocabulary [measured]

- No Lean names, Lean syntax, file paths or process words in the TeX, comments included. One
  bounded exception: the source-disclosure paragraph(s), between `% BEGIN-DISCLOSURE` and
  `% END-DISCLOSURE` <or the project's markers>.
- No word from the banned-word list of `latex-math-writing`, nor from the habitual-phrasing list.
- Terminology from the literature, from `TERMINOLOGY.tsv`; every term a human reader uses is kept.
- In prose, cite a result by number and name ("Theorem~\ref{...} (fixed-volume limit)"); tags
  stay in statement titles.

## 6. Numbering [reviewer and compile check]

- Never redefine counters or `\the...` macros. Numbering is global.
- Refer to every numbered item with `\ref`, `\eqref` or `\cref`, never by a typed number.
- Keep reader-facing tags in statement titles; remove only internal codes.

## 7. Figures

- A figure expresses one mathematical idea in the paper's notation (editable TikZ), is referenced
  from the text, counts against its section's pages, and is reviewed for truth (`math-figures`).

## 8. Length [measured]

- Allowances per section in `allowances.tsv`: caps, or guides where completeness is binding.
  Over a cap = not done; over a guide = the measured length and the reason, reported.
- An addition is offset by cuts in the same section; an addition over one page needs a reason.

## 9. Checks after every integration

```
check_section.sh -m main.tex -V "<vocabulary options>" -S "<shape options>" <section.tex>
check_vocabulary.py --root main.tex <options>
check_shape.py --root main.tex <options>
latexmk -pdf main.tex && page_report.py --toc main.toc --allowances allowances.tsv
```
