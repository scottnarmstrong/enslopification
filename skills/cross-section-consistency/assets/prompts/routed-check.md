You are a read-only checker with a fresh context. Do not create, edit or delete any file. Print your complete report
as your final answer; the runner saves it.

# Routed-inputs check: {{title}}

The sections of this manuscript were written in parallel, so where a proof in one section cites a statement of
another section, the citing writer may have used more than the cited statement says. For every routed citation of
your group, compare what the citing proof USES with what the cited statement SAYS. Compare with the statement, not
with its proof: a property that appears only inside the cited proof is a MISMATCH.

**Inputs** (the frozen snapshot {{packet}}; manifest.json lists the hashes):
- the integrated manuscript in {{packet}}/manuscript/ (main.pdf shows the printed numbers);
- your rows: {{rows}}, in {{packet}}/xref/by-pair/. One row per citation: the citing file:line, its context, the
  statement whose proof cites, the cited label, its kind, where it lives (`proof` means a display inside a proof,
  which no statement asserts), its file:line, its printed number, and its range id;
- the range citations {{packet}}/xref/ranges.tsv, and the candidate cycles {{packet}}/xref/cycles.tsv; yours to
  decide: {{cycles}};
- as evidence, the Lean at {{lean}}: {{graph_hint}}.

**For each row:**
1. Read the citing sentence and the proof step it supports. Write down exactly what the step uses: the hypotheses it
   must verify, the conclusion it takes, the quantifiers and their order, the range of parameters, the uniformity of
   constants, the objects (which inputs, how many points, which norm).
2. Read the cited statement itself and compare.
3. MATCH, or MISMATCH with what is used but not said and the exact repair, in this order of preference:
   (a) SAY SO: the cited statement's own proof already gives what is used: restate the statement (quote the line of
       its proof that gives it);
   (b) change the citing sentence so that it uses exactly what the statement says;
   (c) a new proof from the Lean (name the declaration);
   (d) a REQUEST to the section that should state and prove it.
   A repair that would change a frozen principal statement or a main theorem is marked DRIFT: it goes to the author.
4. Classify each mismatch: SUBSTANTIVE (a proof uses something no statement gives) or LOCAL (a pointer, a constant's
   name, a stale description, a range that prints wider than the statements used).

**Range citations of your rows:** which of the spanned statements does the proof actually use? Propose the list.
**Candidate cycles:** CLEARED (one edge is a forward pointer, a remark, or a use of a part that does not depend on the
cycle: say which) or CONFIRMED (a genuine logical loop: say which statement must change).

**Report, in this order** (sources first, so that a refused command shows at once):
- "Sources consulted:" and, in so many words, whether you could query the dependency database. If a command was
  refused, say so: your verdicts then rest on the text alone.
- A table: id | site (file:line, quoted) | cited label | verdict | used vs said | exact repair | side (citing,
  cited, both) | substantive or local.
- Cycles: id | CLEARED or CONFIRMED | reason.
- Counts: rows checked, MATCH, MISMATCH (substantive, local), cycles cleared and confirmed.
- What this check does not establish.
- Last line: "Verdict: ALL MATCH" or "Verdict: MISMATCHES" followed by the number.
