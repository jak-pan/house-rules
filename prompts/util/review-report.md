### Report format

Report format (mandatory; each item must stand on its own):

```text
VERDICT: APPROVE or REQUEST_CHANGES (REQUEST_CHANGES when any item is under Blocking)

**Blocking · <count>**
1. [B1] <one-line title>
   - Location: <file:line[-line]> (every location involved)
   - Kind: correctness | security | data-loss | spec-contradiction | internal-inconsistency | waste | cost | design
   - Trigger: <the concrete input, interleaving or call sequence that reaches it>
   - Actual: <what the code does>
   - Expected: <what it should do>
   - Requirement: <verbatim quote of the spec line, settled decision or declared boundary, with
     its file:line; or "none written">
   - Introduced by this change: yes | no (pre-existing) | unknown
   - Confidence: high | medium | low (high = traced in the code; low = suspected, not traced)
   - Smallest fix: <apply No fortification for the repair order>
2. [B2] ...

**Spec issues · <count>**
1. [S1] <title>, with Location, Problem, Proposed resolution, Operator decision needed: yes | no

**Follow-ups · <count>**
1. [F1] <title>, with Location, Scenario, Why it does not block

**Non-blocking · <count>**
1. [N1] <title>, with Location and the note

**Coverage**
List every changed file or section you reviewed and anything you could not review.
```

Keep the exact verdict and prior-resolution lines unformatted for the parser. Use the
bold section labels shown above, with the actual finding count. Use bold finding titles,
not Markdown headings. Omit empty section bodies; combine the names of empty sections
in one short line, for example "No findings in Blocking, Spec issues or Follow-ups."
Keep Coverage even when there are no findings. Render claim labels in inline code,
for example `FACT`: <evidence> and `ASSESSMENT`: <interpretation>.
Number items within each section; the bracketed label
(B1, S1, F1, N1) is unique in the report. One finding per item: never merge two mechanisms
into one item, and never repeat one finding under two headings.
