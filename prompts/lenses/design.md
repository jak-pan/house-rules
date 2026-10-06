## Design review

Focus: would an expert in the underlying engine or library build it this way? Check the
whole affected path against native capabilities, not only the diff. Name the engine
feature or root cause and the counted cost of each layer. Apply the shared review bar's
design class, Native-first and No fortification. Trace requirement removals and spec edits
that match existing code to a recorded decision. Finding disposition follows the
[shared review bar](../util/review-bar.md).

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-lenses-design-f961`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
