Focus: concurrency, restarts and bounds (two things at once, a crash or restart mid-step, retries, replay, resource and cost bounds).

Finding coverage follows the [shared review bar](../util/review-bar.md).

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-lenses-concurrency-restarts-60ba`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
