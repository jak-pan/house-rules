# Retrieval evaluations

- Oracle first, backwards: gold-path/full-context ceiling runs isolate reader ceiling
  from retrieval before you tune retrieval. State the floor (no-op baseline) and ceiling
  before interpreting anything between them.
- **Validate the judge/grader against the primary source** (the benchmark's own spec) by
  inspecting actual runtime prompts, and audit the dataset itself when scores plateau
  (variant? distractors present? gold labels sane?) before tuning further.
- **Detect sub-noise levers by subset isolation**: a real lever changes a deterministic
  subset — compare on that subset with a ≈0 noise-check on the untouched remainder.
- When it fits the resource envelope, cross-check prompt changes on a cheaper/weaker
  model too — improvements that only help the strongest reader are fragile.
- Triage every miss by mechanism: model bug / retrieval miss / broken data / shaky gold /
  judge-strict → compute the honest reachable ceiling. Never accept "ceiling" while a
  competitor scores higher; quantify headroom instead.
