# FAQ evidence table template

The last section of the FAQ. One row per check that any public page mentions; delete rows for checks that were not
run, and add the project's own. Each first cell links to the place that describes the check.

## What each check establishes

| Check | What it establishes | What it does not establish |
|---|---|---|
| [Lean kernel check of the source]({{method}}#kernel) | The released log records that the proof terms reachable from {{n}} named results passed the kernel and used only the reported axioms ({{axioms}}). | That the formal definitions capture the intended mathematics, or that any English text is correct. |
| [Statement page compared with Lean]({{statement}}) | A definition-by-definition interpretation of the main theorem, by AI agents, with explicit quantifiers and nonclaims. | An infallible translation, or an equally detailed unfolding of every additional clause. |
| [Correspondence table]({{table}}) | A script (`check_correspondence.py`) verified that every numbered statement has a row, that every listed declaration is in the closure of the main theorem at commit {{commit}}, that each relation is one of the five defined words, and the pinned lines. | That the declarations prove the statement, or that the relation word is right: those are agents' judgments. |
| [Agent reviews of the manuscript]({{process}}) | Reviewers that did not write a section were asked to compare each numbered statement clause by clause with the Lean and to mark each explanatory sentence true, false or unsupported; their reports and a decision on every finding are recorded. A script verified each report's length and verdict line{{, and that every label is mentioned in a report (check_coverage.py)}}. | That each comparison was in fact made, or is right; correctness in the sense of a human referee's report; the reviewers are AI models that can share blind spots. |
| [Outlines compared with Lean]({{method}}#outline-status) | The review described by each outline's status, with source references and local limitations. | A complete human proof review, or a finished informal proof of every estimate. |
| [Dependency graph compared with the authors' record]({{method}}#graph) | The reached declaration sets for the same roots agree up to {{difference}}, each class of difference explained. | Any individual edge, the mathematical role of a reference, or any English explanation. |
| [Agreement between AI readers]({{method}}#key-statements) | Cohen's κ = {{kappa}} between two readers' labels. | Accuracy; a probability that a summary or a theorem is correct. |
| [Typographic pass]({{process}}) | Reviewers were asked to inspect every page image at {{dpi}} dpi and reported each page as clean or listed its defects; a script (`check_coverage.py --pages`) verified that every page appears in a report; a response table answers each reported defect (fixed, or kept with a reason). | That every page was in fact looked at, or that a page reported clean has no defect; anything about the mathematics. |
| [Compiled build]({{readme}}#compiled-lean-files) | Precompiled files for loading the pinned source; the checksum tests the download against the published digest. | An independent rebuild, merely by loading the files or finding the build targets up to date. |
