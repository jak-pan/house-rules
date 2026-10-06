Focus: design documents and specifications. Report contradictions between sections or with recorded decisions, undefined cases, infeasible or unmeasurable requirements, requirements without acceptance tests, stale superseded text, and mechanisms that carry no recorded decision source (name who decided each one or flag it as unratified). Prefer the simplest design that meets the recorded goals; name any mechanism that looks overbuilt and its simpler version. Also apply the reader test: flag sections a new engineer could not understand on their own (missing why, example or term definition), buried behaviour, and missing structure; readability problems are non-blocking unless they hide or garble a rule.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-lenses-design-spec-abab`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
