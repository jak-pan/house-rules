Focus: correctness and security (wrong results, broken invariants, data loss, access without permission, secret leaks).

Finding coverage follows the [shared review bar](../util/review-bar.md).

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-lenses-correctness-security-aac8`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
