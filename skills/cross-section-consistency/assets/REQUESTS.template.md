# Requests from Section <number> (unit <key>), stage <stage>

One block per request; write the single line "None." instead of this file's body if there are none.
A request is for a result this section needs that no section states and whose proof would take more than about a
page here; a shorter proof goes into this section as a lemma. The editor decides on each request; accepted requests
reach the owning section's next writer through its INBOX.md (route_requests.py).

## R1
- To: <unit key of the section that should state and prove it>
- Needed by: <label of the statement whose proof uses it>, at <file:line of the use>
- Statement: <the exact statement, in the manuscript's notation, with every hypothesis and quantifier; LaTeX allowed;
  it may continue on the following lines>
- Lean: <declaration names (used = 1) with module:line, or "none found">
- Why no existing statement serves: <the closest existing statement, by label, and what it lacks>
- Until delivered: <what this section does meanwhile: for example, it lists the result in NOTES.md as an open
  dependency and does not present it as proved>
