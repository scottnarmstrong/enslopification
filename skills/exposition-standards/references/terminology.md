# Terminology from the literature

A formal development names its objects for its authors' convenience, and writers who read the
code reuse those names ([L28](../../lean-to-manuscript/references/lessons-learned.md#l28)): the
Yang–Mills Lean, for instance, speaks of molecules, seeds, tokens and readouts. The literature has
words for most such objects (a polymer, a Borchers algebra, Wick ordering), and a reader who knows
the field reads those without effort. Translate before the editorial pass, with a table, and make
the check enforce it.

## The table

Start from `assets/terminology-header.tsv`:

| # | current term | proposed term | sources (n) | recommendation | note |
|---|---|---|---|---|---|

- **current term:** the word or symbol as the text uses it, with every meaning it has (a word
  with several meanings keeps at most one, defined; the others are renamed).
- **proposed term:** the literature's term, with a reference where it is not standard; or "keep".
- **sources (n):** every review that proposed a change or used the term, with a count. Mark the
  human readers.
- **recommendation:** adopt, keep, merge (two names for one object), or author (the change touches
  an approved statement).
- **note:** the gloss added at the definition, the index entry, what the change must not break.

Collect the rows from every review: ask each exposition reviewer to end with a list of
manuscript-wide renamings, and take the terms the human readers used from their notes.

## Rules

- **Human readers outrank agents** ([L26](../../lean-to-manuscript/references/lessons-learned.md#l26)).
  Every term a human reader uses is kept, even when agents propose a better one; it gets a gloss
  at its definition ("we call such a block *good*: the field on it is small"). Every row records
  its sources, human readers marked as such.
- **Adopt the literature's term** when one exists and no human reader uses the code's word.
- **One symbol, one meaning.** Rename where a symbol has two meanings, where a local name clashes
  with a name of the opening part, or where hypothesis labels clash with axiom labels (hypotheses
  (A1)–(A3) of a lemma in a paper whose axioms are also labelled (A1)–(A3)).
- **Approved statements need approval.** A renaming inside a frozen statement goes to the author,
  and the word stays until the author rules.
- **Tags are not words.** In prose, cite "Theorem 4.2 (fixed-volume limit)", not a bare tag; tags
  stay in statement titles, where the reader learns them.

## Make it stick

Apply the table in one pass over the whole manuscript, with the glosses and the index of notation.
Then put every retired word into a pattern file for the vocabulary check, as its own category, for
example `retired-terms.txt` with one line `\bmolecules?\b` per word, and run
`check_vocabulary.py --patterns retired-terms=retired-terms.txt`. A rule enforced by the check is
followed; a table that nobody checks is forgotten by the next writer
([L1](../../lean-to-manuscript/references/lessons-learned.md#l1)).
