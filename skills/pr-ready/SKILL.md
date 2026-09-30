---
name: pr-ready
description: The repeated change loop — local fast gate, push, CI as the full gate, review rounds, merge and cleanup. Use before pushing or marking a PR ready, when writing or running a review round (human or agent reviewer), when fixing review findings, and when merging a PR.
license: MIT
---

# PR Ready

One loop per change: local gate → push → CI → review round → fix → … → merge → cleanup.
Where CI runs the complete gate on every push and merges wait for it, CI owns the full
suite (AGENTS.md §Verification); everything below keeps local work small.

## 1. Local gate (implementer or fixer)

- Use the repository's declared gates (its `AGENTS.md`, or the CI workflow when none are
  declared) in CI's build profile. Rust: skill `rust-canon` §Gates.
- Run formatting, lint/compile checks, fast guard tests, and **targeted** tests: the
  modules or packages the diff touches, their direct tests, and every new regression.
  Widen the target to dependents when a shared type, trait, schema or public contract
  changes. When toolchains, lockfiles or build scripts change, leave the matrix to CI.
- Update the branch by merging the default branch into it (no rebase, no force-push),
  resolve conflicts, then rerun the local gate.
- Report the exact commands, filters and pass/fail counts.

## 2. Push and CI

- Push; wait for CI to finish green on the exact head commit.
- On a CI failure, reproduce only the failing tests locally. Before attributing a failure
  to the change, compare it against the default branch under the same conditions.

## 3. Review rounds

**Where reviews run.** If the repository has a server-side review gate (a review app
running in CI), pushing triggers the review and only its result counts for merging; a
local panel is optional pre-push feedback. Otherwise the agent runs the panel locally.
External repositories always get local review rounds (skill `upstream-contribution`).

**Review bar.** Every finding cites a concrete scenario. Reviewers check:
- **Correctness and security:** invariants on every path, authorization and
  confidentiality, failure, crash and replay paths, and input handling.
- **Performance:** request-path cost against the declared bound, and no proportional
  scans or unbounded memory, backed by measured numbers where the change claims a bound.
- **Code quality:** the smallest change that works, in the surrounding code's style, with
  one way to do each thing and names that say what things do.
- **Waste, as a blocking class:** tests that do not guard a real behavior or defect,
  duplicate or tautological checks, speculative abstractions, dead code, drive-by
  refactors, and docs longer than the fact they carry.

- Give the reviewer the diff range, the spec sections, the previous round's review, and
  [the review template](references/review-prompt.md). Run a panel of one
  generalist per model family, adding focused lenses where warranted
  ([review panels](references/review-lenses.md)), and loop until a full panel round finds
  no blockers. The reviewer reviews statically and
  runs at most one targeted test, only to confirm or refute a specific finding.
- The fixer closes every blocking item with the reviewer's smallest fix and a regression
  test, in one commit per round. The next review names that commit and marks each prior
  blocker RESOLVED or NOT. A fixer never approves its own fix.
- When a fix meets a genuine design choice, the fixer stops and reports the options; the
  lead decides (skill `operator-protocol` §Decisions).
- When rounds keep finding the same class of defect, stop patching and reassess the
  design (AGENTS.md §Three-occurrence reassessment).

## 4. Merge and cleanup

- Merge only when the reviewer approves the exact head, CI is green on that head, and the
  closeout checklist holds (skill `design-flow` §6). Pin the head
  (`gh pr merge <n> --match-head-commit <sha>`) in the repository's merge style. No
  auto-merge unless the operator asked.
- Then update the tracking item, delete the branch, and remove the lane (skill
  `agent-lanes` §Lane cleanup).
