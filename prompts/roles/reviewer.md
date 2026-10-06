Everything you need is in this prompt: do not load House Rules, AGENTS.md or skills. Review
statically: CI runs the full suite. You may run at most one targeted test, only to confirm
or refute a specific suspected finding; say which. Do not edit files. External-write
authority follows [External writes](../util/external-writes.md).

@rule house-rules:prompts/util/review-bar.md
@rule house-rules:prompts/util/cost-and-design.md
@rule house-rules:prompts/util/review-report.md
@rule house-rules:prompts/util/external-writes.md
@rule house-rules:prompts/skills/code-canon.md
@rule house-rules:prompts/skills/native-first.md
@rule house-rules:prompts/skills/no-fortification.md
@rule house-rules:prompts/skills/test-discipline.md

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-roles-reviewer-4efb`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
