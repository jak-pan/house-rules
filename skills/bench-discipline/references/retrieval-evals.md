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

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-skills-bench-discipline-references-retrieval-evals-6500`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
