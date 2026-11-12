# Disclosure wordings

Templates for every place that says who wrote the text and what was checked. Fill the `{{...}}` placeholders once,
in a shared file, and copy the **same** sentences everywhere: the abstract, the introduction, the title page, the
manuscript README, the repository description and `CITATION.cff`. The author approves the wording and the author
line; agents never choose either.

Placeholders: `{{source}}` (the formal source, e.g. "OpenAI's Lean code for the construction of four-dimensional
quantum Yang–Mills theory"), `{{source_url}}`, `{{commit}}` (short hash), `{{commit_full}}`, `{{axioms}}` (as the
verification log reports them), `{{log_url}}` (verification log at the pin), `{{usage_url}}` (the source's usage
record, if any), `{{table_url}}` (the published correspondence table), `{{process_url}}`, `{{status_url}}`,
`{{section}}` (the introduction's subsection on sources), `{{date}}`, `{{collaboration}}` (optional sentence).

## 1. Abstract, last sentences

**While under construction**

> This paper was written entirely by AI agents from {{source}} (commit `{{commit}}`). The Lean proof is
> kernel-checked, with only the standard axioms. The agents compared every numbered statement here with the Lean
> declarations used by the main theorem; the correspondence table is published separately. The prose arguments
> were written and reviewed by AI agents. They are not machine-checked and have not been refereed by human
> mathematicians (Section {{section}}).

**Finished** (only after the author removes the markers)

> This paper was written entirely by AI agents from {{source}} (commit `{{commit}}`). Three kinds of checking are
> involved. The Lean kernel checks the formal proof. AI agents compared each numbered statement here with the Lean
> declarations it rests on. The prose proofs are not machine-checked and remain subject to mathematical review.
> Section {{section}} gives details.

Preconditions: the table at `{{table_url}}` is public before "published separately" appears; "compared every
numbered statement" only when the table has a row for every numbered statement (`check_correspondence.py --tex`)
and no label is missing from the review reports (`check_coverage.py` of `writing-workflow`); "only the standard
axioms" matches the log at `{{log_url}}`; Section {{section}} exists. If people have since refereed or read the
text, add who read what, in the author's words.

## 2. Introduction: the paragraph on sources

Mark it as the vocabulary check's exception region: a line `% BEGIN-DISCLOSURE` before it and a line
`% END-DISCLOSURE` after it (the default markers of `check_vocabulary.py` in exposition-standards).

```latex
\subsection{Source of the result and of this text}\label{sec:intro-source}
The mathematical result is due to {{source}}, at commit~\texttt{{{commit}}} of
\href{{{source_url}}}{the source repository}. Three kinds of checking are involved, and they should be kept apart.
\begin{itemize}
\item The Lean kernel checks the formal proof. Its \href{{{log_url}}}{verification log} reports no unproved
  placeholders and only {{axioms}} as axioms.
\item AI agents compared every numbered statement of this text with the Lean declarations used by the main theorem:
  hypotheses, definitions, quantifier order, normalizations and conclusions, with usage determined from the
  compiled dependencies. The correspondence table is published at \url{{{table_url}}}.
\item The prose arguments were written and reviewed by AI agents. They are not machine-checked and have not been
  refereed by human mathematicians.
\end{itemize}
A correct formal declaration does not by itself show that an English statement has kept its hypotheses and
quantifiers, or that a prose proof proves that statement. This text was written entirely by AI agents, by the
method described in \href{{{process_url}}}{\emph{How the manuscript is written}}. {{collaboration}}
```

(In TeX, `\texttt{{{commit}}}` is the macro's brace followed by the placeholder; fill it as `\texttt{3456e5e}`.)

## 3. Title page

- Author line: as the author decides (it may stay blank).
- While under construction: `\date{Draft of {{date}}}`, optionally with a short note linking `{{status_url}}`.

## 4. README banner of the manuscript (while under construction)

> **{{state}} ({{date}}).** {{what is written and reviewed}}. {{what review is under way}}, and sections may still
> change until they are marked *checked* in the [status table]({{status_url}}). Do not cite it as a finished proof.

## 5. Repository description and links from companion pages

- Description: "{{title}}: a natural-language proof written by AI agents from {{source}} (under construction)".
- Link text on companion pages: "the full manuscript (under construction)".

## 6. CITATION.cff abstract

End the abstract with the first sentence of section 1, unchanged, and list the formal source under `references`.

## 7. Wordings never to use

- "written by checking every statement against the Lean" (merges three kinds of checking);
- "verified", "proved correct", "machine-checked" for the prose; "refereed" for agent reviews;
- "complete proof" or "finished" while the markers are up.
