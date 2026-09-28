---
name: agent-lanes
description: Parallel multi-agent orchestration — lane ownership, non-colliding file sets, worktrees, per-lane cargo target dirs, GPU serialization, subagent git limits, cross-repo etiquette. Use when fanning out subagents, workflows, teammates, or background jobs.
license: MIT
---

# Agent Lanes

Mechanics for the parallel-work invariants in AGENTS.md §Parallel work. The main thread
stays interactive for the operator; heavy work goes to detached agents/workflows with
explicit goals.

## Lane rules

- **Ownership.** Each lane's work item lists its explicit file set; before merging a
  lane's work, check its diff against that list.
- **Isolation.** Lanes work in worktrees/branches; the main repo checkout stays untouched.
  Rust lanes pass `--target-dir .tmp/cargo-target/<lane>` so parallel cargo doesn't deadlock
  on `target/` or leak artifacts.
- **Git limits.** Lanes push only their own task branches, within the delivery authority
  recorded in the bible (policy: AGENTS.md §Git). Commits follow the repo's canon; lanes
  report exactly which files they touched.
- **Multi-repo work (owned repos) is normal.** One work item, a branch per repo touched
  (named per the workspace convention; the file tracker uses `task/NNN-slug/<agent>`),
  and every repo+path in the item's lane declaration. Flag shared-kit impacts for owner
  review — flag, don't block.
- **Audits have round boundaries.** An audit-only request produces findings and proposed
  fixes. Repair and confirmation belong to the round when the operator requested them;
  do not infer mutation authority from a request to inspect or explain. What counts as a
  new round: AGENTS.md §Resource envelopes.

## Resource budgets

- Respect global provider concurrency across ALL lanes combined (e.g. "provider A under
  500 total, provider B under 2000 in total") — budgets are fleet-wide, not per-lane.
  ⚒ Make one lane the budget owner when several hit the same provider.
- Record the intended concurrency and measurement conditions before launch (bounds and
  isolation: AGENTS.md §Parallel work).
- Cleanup follows AGENTS.md §Security.
- Finishing a lane includes removing what it created to be disposable. When its PR merges or
  the work is abandoned, the lane owner removes its worktree and its build/target directory in
  the same step, after confirming the worktree holds no uncommitted or unpushed work. Shared
  caches (compiler cache, model caches) stay. Operator direction: 2026-09-28, after merged-PR
  worktrees and per-lane build directories cut free disk to 56 GB.
- Never build `--release` in a shared tree while a paused run may depend on the existing
  binary — release builds clobber it; use your lane's target dir.

## Orchestration patterns

- **Recon sweep → design → build → proportional critique → gate → fix.** When to add an
  adversarial verifier: AGENTS.md §Parallel work.
- **Decision handling.** Lanes decide and escalate per skill `operator-protocol`
  §Decisions.
- **Background monitors.** Every detached run has a watcher that surfaces failures instantly
  and feeds concrete counters into status lines. Prove work is running: process name, output
  path, dashboard link.
- **Handoff on saturation.** A lane near context limits writes a handoff and dies; a fresh
  agent with a handoff beats a saturated one every time (skill `handoff-continuity`).
