Focus: a traceability pass over the referenced spec sections. For each requirement and acceptance test, cite where the code implements it and which test proves it; report every requirement that is missing, partial, contradicted, or claimed without a test. Name the section for every finding.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-lenses-spec-7d43`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
