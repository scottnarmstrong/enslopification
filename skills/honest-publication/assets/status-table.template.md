# Status table template

Put the table on the manuscript's page, dated, with one line on what changed and what comes next. Every status word
used anywhere in the repository has a row in the meanings table, and nowhere else is a status word used.

## Status

*Updated {{date}}. {{one sentence: what changed since the last update, with the page count}}.*

| | section | pages | status |
|---|---|---:|---|
| Part I | 1. {{title}} | {{n}} | {{status}}; {{last event, e.g. "revised after an independent referee review"}} |
| | 2. {{title}} | {{n}} | {{status}} |
| Part II | {{k}}. {{title}} | {{n}} | {{status}} |

**Next:** {{the next step, e.g. "a final cross-section check; then the author's reading"}}.

## What each status means

| status | review recorded by the label | what it does not mean |
|---|---|---|
| *draft* | a writer's proposal, integrated by the editor; automatic checks pass | that any review has run |
| *reviewed* | the full review cycle ran: owner of each principal statement, mathematical review against the Lean, fresh reader, prose truth, re-check, delivery review | that a human has read it; a referee's report |
| *checked* | the author read it and the changes it led to were made | an independent human referee's report |

Only the author moves a section to *checked*, and the word means nothing else anywhere in the repository (the
Yang–Mills map also used it for outlines, with another meaning; here outlines are *compared*). The
under-construction markers stay until every section is *checked* and the author removes them.

## Other status vocabularies (if the repository has outlines or a glossary)

| word | records | does not mean |
|---|---|---|
| outline *draft* | first account written from the source and the key statements | that the next reviews ran |
| outline *compared* | a second model compared the numbered statements with the linked Lean and read the main steps | that subsidiary estimates were read |
| outline *edited* | a third model compared again and edited the exposition | an independent human proof review |
| glossary *certain* / *probable* / *tentative* | the strength of the interpretation of a code name | a review status, or correctness |

A status of an explanation never implies that the corresponding formal result is unproved.
