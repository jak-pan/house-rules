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

- **Disjoint ownership.** Each lane owns an explicit file set; shared spine files are append-only.
  Before merging a lane's work, verify its diff touched only its assigned files.
- **Isolation.** Lanes work in worktrees/branches; the main repo checkout stays untouched.
  Rust lanes pass `--target-dir .tmp/cargo-target/<lane>` so parallel cargo doesn't deadlock
  on `target/` or leak artifacts.
- **Git limits.** Subagents never push main. On owned repos, lanes push their own task
  branches within the delivery authority recorded under AGENTS.md §Git.
  Commits follow the repo's canon; lanes report exactly which files they touched.
- **Multi-repo work (owned repos) is normal.** One work item, a branch per repo touched
  (named per the workspace convention; the file tracker uses `task/NNN-slug/<agent>`),
  and the item's lane declaration lists every repo+path. Changes to a shared
  kit that other consumers depend on get flagged in the handoff
  for owner review — flag, don't block. Surprise landings in a repo the task didn't
  declare are the actual sin.
- **Externally-owned repos are read/fork-only.** No pushes, PRs, issues, or comments until
  the operator explicitly says ready — anti-spam is a hard rule.
- **Audits have round boundaries.** An audit-only request produces findings and proposed
  fixes. Repair and confirmation belong to the round when the operator requested them;
  do not infer mutation authority from a request to inspect or explain. What counts as a
  new round: AGENTS.md §Resource envelopes. Audit lanes surface opportunistic
  findings, but those findings enter the queue rather than automatically preempting the
  primary path.

## Resource budgets

- Respect global provider concurrency across ALL lanes combined (e.g. "provider A under
  500 total, provider B under 2000 in total") — budgets are fleet-wide, not per-lane.
  ⚒ Make one lane the budget owner when several hit the same provider.
- Bound memory-heavy concurrency by verified host capacity and the approved envelope.
  Isolate competing GPU/latency measurements unless contention is the declared study;
  record the intended concurrency and measurement conditions before launch.
- Cleanup follows AGENTS.md §Security. Identify ownership and retention before pruning;
  old runs and datasets are not automatically disposable. Large artifacts live outside the repo.
- Finishing a lane includes removing what it created to be disposable. When its PR merges or
  the work is abandoned, the lane owner removes its worktree and its build/target directory in
  the same step, after confirming the worktree holds no uncommitted or unpushed work. Shared
  caches (compiler cache, model caches) stay. Operator direction: 2026-09-28, after merged-PR
  worktrees and per-lane build directories cut free disk to 56 GB.
- Never build `--release` in a shared tree while a paused run may depend on the existing
  binary — release builds clobber it; use your lane's target dir.

## Orchestration patterns

- **Recon sweep → design → build → proportional critique → gate → fix.** When to add an
  adversarial verifier: AGENTS.md §Parallel work. Verification stays inside its approved
  agent, round, and resource boundary.
- **Decision handling.** Lanes follow the collaboration mode in AGENTS.md §Autonomy.
  Escalate choices beyond delegated authority with options and a recommendation; continue
  ordinary implementation choices inside the recorded agreement.
- **Background monitors.** Every detached run has a watcher that surfaces failures instantly
  and feeds concrete counters into status lines. Prove work is running: process name, output
  path, dashboard link.
- **Handoff on saturation.** A lane near context limits writes a handoff and dies; a fresh
  agent with a handoff beats a saturated one every time (skill `handoff-continuity`).
- Parallelize independent preparation and launch only the planned, resource-bounded work.
