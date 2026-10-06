### Cost and design findings

Name the supported native feature or root cause, the counted cost
(calls, rows, writes, retained state or layers), and why the proposed mechanism does not
earn that cost. Apply [Native-first](../skills/native-first.md) and
[No fortification](../skills/no-fortification.md). A design finding questions whether the
approach or mechanism is right. A design finding stays Blocking and stops for a lead decision; it never becomes a follow-up or starts another
fix round. The lead may refer that decision to the council. Cost defects and design findings
cannot be reclassified to escape review reassessment. Cost-defect classification and the
cost-defect definition follow [Triage classes](triage-classes.md); settled-decision
disagreements follow [Code canon](../skills/code-canon.md).

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-util-cost-and-design-e1ab`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
