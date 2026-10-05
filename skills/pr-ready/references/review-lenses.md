# Review panels

**Default panel:** one generalist reviewer per model family, in parallel: family A and
family B, plus family C when available. Different families miss different defects, so a
second family finds more than another round from the same one. Reviewer definitions live in
[`../reviewers/`](../reviewers/); the machine-local config maps each family to a CLI, model
and effort (House Rules keeps model choice out of the repository).

## Optional lenses

Add focused reviewers for changes that warrant them, for example
security on access-control code or durability on storage code: `security`, `durability`,
`performance`, `spec` (a requirement-by-requirement traceability pass) and `waste`. Each
reports only findings in its lens. Non-backend changes add their own reviewers, chosen by the
paths a change touches: `design-spec` for design documents and specifications, `frontend`
for user-interface code, and `ux` for user flows (with screenshots or a preview link when
available).

The lead spawns specialists when the operator asks or a finding warrants one. The
[`design`](../reviewers/design.md) lens is required for design changes (specs, new
mechanisms or layers), storage/read/search/native paths, a design smell flagged by another
reviewer or the triager, and the daily whole-system audit. It is not required on every PR.

Spec challenges and finding disposition follow the
[shared review bar](../reviewers/common.md#review-bar). The lead triages each one:
a clarification is proposed in the same PR.
Requirement removals and spec/code drift follow `design-flow` §Design changes.

**Loop:** follow [pr-ready §3](../SKILL.md#3-review-rounds). Merge eligibility is in
[pr-ready §4](../SKILL.md#4-merge-and-cleanup). Track confirmed findings per family.

Launch: `scripts/review-panel.sh <name> <checkout> <base-prompt> [reviewer ...]`
(default reviewers: the generalists of the configured families).
