Focus: user experience of the changed flows. Walk each flow the change touches: empty, loading, error and success states; copy that is unclear, inconsistent or blames the user; destructive or irreversible actions without confirmation or undo; consistency with the product's existing patterns. When screenshots or a preview link are provided, review them; otherwise review from the code and spec and say so.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-lenses-ux-90ca`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
