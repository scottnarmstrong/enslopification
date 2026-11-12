# Unit outline template

One unit is a mathematically coherent piece of the proof, typically 4,000 to 40,000 lines of Lean. Its outline is
written for a mathematician who will later write the full proof: faithful to the Lean, readable without it.

Two versions exist. The **detailed notes** follow this template with a proof sketch for every step and no length
limit. The **outline** follows the same headings within its allowance: one page (about 500 words) per 4,000 Lean
lines, at least 3 and at most 10 pages, measured with `outline_budget.py`. Markdown with `$...$` math that renders
on GitHub (check with `gh_math.py --check`).

---

# <unit id>. <title>

**Part:** <part number and name>. **Lean:** <folders or work items, linked at the pinned commit>. **Size:** <Lean
lines, with the counting rule of the data tables>.

## 1. What this unit proves

The results that other units use, and the results that matter in themselves. For each:

**Proposition <unit>.<k> (<short name>).** <Plain mathematical statement: objects, every hypothesis, quantifiers in
their order, the conclusion displayed.>
*Status:* theorem / definition (a specification shown to hold later, and where) / hypothesis carried as an
assumption (and where it is discharged, if known).
*Lean:* [`Full.Name`](<repo-url>/blob/<commit>/<path>#L<a>-L<b>) (several links if the statement is spread over
several declarations).

State every hypothesis inside the statement, so that a reader can tell what is proved here and what is assumed.

## 2. What it uses

- Inputs from other units, by unit id, each with a plain statement and its Lean link.
- Standard mathematics, named, with a reference where possible.
- Imported constants and assumptions: values or hypotheses that enter from outside without proof here, and where
  they are proved if known.

## 3. Strategy

One to three paragraphs: the idea of the proof in the language of the field. Name the known method it follows,
and say what differs here.

## 4. Steps

The proof as numbered steps. Each step: a precise statement; a proof sketch (the mechanism, the estimate, the key
inequality); its Lean link; and *(proof read)* or *(statement only)*, saying whether the Lean proof was read.

## 5. Where the difficulty lies

Short. What is hard or new and what is routine. Anything stronger or weaker than one would expect.

## 6. Notation

The objects the unit introduces, with their code names (linked) and the notation proposed for a written proof,
using the glossary's translations of the code's nicknames.

## 7. What remains unexplained

What could not be settled from the Lean: unclear roles, steps whose proof was not read, statements marked
(probable) or (tentative).

---

**Rules for every version**

- Cite only declarations in the closure of the main theorem (`used = 1`); an unused alternative route is not
  evidence for the proof.
- Every Lean link is pinned to the commit and to the exact lines (`lean_links.py`); a declaration without a range
  is linked to its file.
- No Lean syntax in statements; code names only in links and in section 6.
- Mark every statement you are unsure of: (probable) or (tentative).
- No `\operatorname` (use `\mathrm{tr}`), no `#` or `\#` inside math (use `\sharp A` or `\mathrm{card}\,A`), no
  `\newcommand`, `\label` or `\ref`; in a table, write `\vert` for a bar inside math.
