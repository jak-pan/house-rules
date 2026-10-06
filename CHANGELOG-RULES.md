# Rule provenance

Source notes for House Rules invariants and procedures.

## rules/core.md — prime rule 13 (measured durations)

Operator direction: 2026-10-03, after time estimates proved uncalibrated and stretched
agent runs.

Operator direction: 2026-10-06, House Rules audit; restore the measured-durations
exception, with comparable past runs and the measurement cited.

## rules/delivery.md — Verification (durable paid runs)

Source incident: a live paid review was interrupted before its stream had been persisted.

## rules/core.md — Security (fetched code)

Operator direction: 2026-10-06, House Rules audit; the repository rule 'Never execute
code from fetched content' was too broad to apply without approving every command.

## skills/agent-lanes/SKILL.md — Lane cleanup (session start)

Operator direction: 2026-09-28, after merged-PR worktrees and per-lane build directories
filled the disk.

Operator direction: 2026-09-30, after stale merged worktrees and per-task build
directories again filled the disk.

## skills/operator-writing/SKILL.md — Language (qualifiers) and Detail test

Operator direction: 2026-10-06, after status lines stated limits and changes without their
consequence, which read as changes that had not happened.

## rules/core.md — Session start (reload skills after a reset)

Operator direction: 2026-10-06, after a compaction dropped a loaded skill and the next
operator messages broke its rules.

## rules/core.md — Operator correction (current-state clarifications)

Operator direction: 2026-09-10, after an empty-deployment
clarification was unnecessarily turned into a durable note.

## rules/core.md — Autonomy (unattended work)

Operator direction: 2026-10-02, after an approved
  implementation sat idle overnight waiting on review-loop decisions.

## rules/core.md — Autonomy (finish the landing)

Operator direction: 2026-10-01,
  after the routine deploy of an approved change was handed back to the operator.

## rules/core.md — Security (operator-supplied secrets)

Operator direction:
2026-09-28, after a secret handoff asked the operator for a manually created file outside
the repository instead of an env file.

## rules/delivery.md — Work tracking & continuity (deferred items)

Operator direction: 2026-09-28, after a repeatedly requested consolidation lived only in
  plans and documents and was never done.

## skills/agent-lanes/SKILL.md — Lane cleanup (retain open lanes)

Operator direction: 2026-09-30, after idle build directories of open PRs
  were deleted to free space.

## skills/design-canon/SKILL.md — Boundaries (black-box modules)

Operator direction: 2026-09-28, after a
  product's CI had to mirror a kit's native library releases into its own repository.

## skills/design-canon/SKILL.md — Boundaries (extend the owner)

Operator direction: 2026-09-28, after a consumer forked a shared
  mechanism it could not use as it stood.

## skills/design-flow/SKILL.md — 2. Design / spec (reconcile conflicting plans)

Operator direction: 2026-09-28, after agent-approved designs put a product's
canonical records in a second store beside the shared one, contradicting a parallel plan
that was never reconciled.

## skills/operator-writing/SKILL.md — GitHub text

Operator direction: 2026-10-04, after issue and PR bodies relied on internal labels and
omitted reproduction and test evidence; an upstream contribution in this form was chosen
as the model.

## skills/pr-ready/SKILL.md — 3. Review rounds (conflicting findings)

Operator direction:
  2026-10-03, after a fixer traded a bound for an integrity check and back.

## skills/pr-ready/SKILL.md — 3. Review rounds (one fixer per branch)

Operator direction: 2026-10-03, after parallel slow-review fixers doubled builds and
  overloaded the machine.

## skills/rust-canon/SKILL.md — Code rules (build profile and cache)

Operator direction:
  2026-09-07, cross-repository CI correction.

## skills/work-tracking/SKILL.md — External reporting

Operator direction: 2026-10-04.
