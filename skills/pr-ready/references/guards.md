## Guard upkeep

Each rule has one home. Prompts reference it with
`@rule house-rules:<path>`; the prompt builder resolves and includes the
whole file at build time. Prompts never keep copied rule text. A missing file
fails the run visibly. Product targets stay in the repository's spec; private extensions
stay in `custom/`.

Use deterministic checks first for facts code can establish. Agent reviewers judge design
fit, root causes and spec intent. Test logging, pruning and testing constraints:
[prompts/skills/test-discipline.md §Test discipline](../../../prompts/skills/test-discipline.md). Review-round reassessment:
[pr-ready §3](../SKILL.md#3-review-rounds).

There are no fixed caps on blocking findings or filed issues. The triager decides by
severity and deduplication; all critical findings block. Capacity never skips or degrades
a guard. Only token exhaustion stops guard work, and it goes to the operator with the
unfinished work identified. This does not waive safety controls or operator stop requests.

## Daily whole-system audit

Run an independent, read-only whole-system audit daily per repository through the audit
scheduler (for example Warden), using that repository's scope file. Examine the whole
system from first principles, including native capabilities, layers and their costs,
fortification, and spec/code drift; include the design lens. A missing scope file is a
visible failure, never an excuse to skip the audit.

Apply [Guard upkeep](#guard-upkeep) for filing policy. The triager deduplicates findings
by fingerprint against tracked findings. Comment on a known finding only when
materially new evidence changes it. The audit opens no PRs; it reports findings for the
lead to adjudicate and assign.
