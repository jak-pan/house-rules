# Review panels

**Default panel:** one generalist reviewer per model family, in parallel: family A and
family B, plus family C when available. Different families miss different defects, so a
second family finds more than another round from the same one. Reviewer definitions live in
[`../reviewers/`](../reviewers/); the machine-local config maps each family to a CLI, model
and effort (House Rules keeps model choice out of the repository).

**Optional lenses** add focused reviewers for changes that warrant them, for example
security on access-control code or durability on storage code: `security`, `durability`,
`performance`, `spec` (a requirement-by-requirement traceability pass) and `waste`. Each
reports only findings in its lens.

**Every reviewer challenges the spec too**, in a separate section: contradictions,
infeasible or unmeasurable requirements, undefined cases, evidently worse designs. A spec
issue blocks only when the code faithfully implements a wrong spec. The lead triages each
one: a clarification goes into the spec in the same PR; a genuine design choice goes to
the operator as a decision.

**Loop:** panel round → fixer confirms each finding (rejecting false ones with a reason) and
fixes the real ones → each flagging reviewer checks its own findings, and another family
reviews the fix diff → next full panel round. Stop when a full panel round finds no
blockers. Track per family how many findings were confirmed.

Launch: `scripts/review-panel.sh <name> <checkout> <base-prompt> [reviewer ...]`
(default reviewers: the generalists of the configured families).
