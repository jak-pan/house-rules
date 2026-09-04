---
name: agent-lanes
description: Parallel multi-agent orchestration — lane ownership, non-colliding file sets, worktrees, per-lane cargo target dirs, GPU serialization, subagent git limits, cross-repo etiquette. Use when fanning out subagents, workflows, teammates, or background jobs.
---

# Agent Lanes

Parallelize independent primary and supporting work whenever delegation is available,
permitted, and useful. The main thread stays interactive for the operator. Parallelism is
autonomous inside the campaign's resource envelope and never broadens the campaign by
itself; heavy work goes to detached agents/workflows with explicit goals.

## Lane rules

- **Disjoint ownership.** Each lane owns an explicit file set; shared code is additive-only.
  Before merging a lane's work, verify its diff touched only its assigned files.
- **Isolation.** Lanes work in worktrees/branches; the main repo checkout stays untouched.
  Rust lanes pass `--target-dir .tmp/cargo-target/<lane>` so parallel cargo doesn't deadlock
  on `target/` or leak artifacts.
- **Git limits.** Subagents never push main. On owned repos, lanes push their own task
  branches freely — remote branches are crash insurance and the live lane registry.
  Commits follow the repo's canon; lanes report exactly which files they touched.
- **Multi-repo work (owned repos) is normal.** One work item, a branch per repo touched
  (named per the workspace convention; the file tracker uses `task/NNN-slug/<agent>`),
  and the item's lane declaration lists every repo+path. Changes to a shared
  kit that other consumers depend on get flagged in the handoff
  for owner review — flag, don't block. Surprise landings in a repo the task didn't
  declare are the actual sin.
- **Externally-owned repos are read/fork-only.** No pushes, PRs, issues, or comments until
  the operator explicitly says ready — anti-spam is a hard rule.
- **Audits have round boundaries.** A requested audit round includes the audit, repair of
  its material outcome-relevant findings, and confirmation of those repairs. A new
  independent auditor, new broad pass, or different work category is another round unless
  the resource envelope explicitly includes it. Audit lanes surface opportunistic
  findings, but those findings enter the queue rather than automatically preempting the
  primary path.

## Resource budgets

- Respect global provider concurrency across ALL lanes combined (e.g. "provider A under
  500 total, provider B under 2000 in total") — budgets are fleet-wide, not per-lane.
  ⚒ Make one lane the budget owner when several hit the same provider.
- One memory-heavy local process at a time: two 20GB Python lanes once killed the machine.
  GPU/latency benchmarks are strictly sequential — parallel runs invalidate them.
- Prune disk (old runs, stale datasets) proactively; large artifacts live outside the repo.
- Never build `--release` in a shared tree while a paused run may depend on the existing
  binary — release builds clobber it; use your lane's target dir.

## Orchestration patterns the operator expects

- **Recon sweep → design → build → proportional critique → gate → fix.** Use an adversarial
  verifier when required by an acceptance criterion or included in the approved review
  plan. Verification stays inside its approved agent, round, and resource boundary.
- **STOP-at-fork agents.** A lane that hits a design decision stops and reports options +
  recommendation instead of forcing a change; the operator picks one.
- **Background monitors.** Every detached run has a watcher that surfaces failures instantly
  and feeds concrete counters into status lines. Prove work is running: process name, output
  path, dashboard link.
- **Handoff on saturation.** A lane near context limits writes a handoff and dies; a fresh
  agent with a handoff beats a saturated one every time (see `handoff-continuity`).
- Parallelize preparation, then launch the matrix at once.
