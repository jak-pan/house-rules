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

- Run `scripts/prepare.py fix <checkout> --reviews <files...>` before fixing, or
  `scripts/prepare.py pr <checkout>` before preparing a PR. It fetches the base and
  checks ownership with `upstream-contribution/scripts/repo-ownership.sh`. For external
  repositories it reports how many commits the branch is behind and leaves the update
  method to the operator; `--update` forces a base merge. Owned repositories (and unknown
  ownership) keep the default base merge, never rebase, and stop on conflicts. It prints
  context and targeted test commands without running them. `--base REF` overrides remote
  default detection.
- Use the repository's declared gates (its `AGENTS.md`, or the CI workflow when none are
  declared) in CI's build profile. Rust: skill `rust-canon` §Gates.
- Run formatting, lint/compile checks, fast guard tests, and **targeted** tests: the
  modules or packages the diff touches, their direct tests, and every new regression.
  Widen the target to dependents when a shared type, trait, schema or public contract
  changes. When toolchains, lockfiles or build scripts change, leave the matrix to CI.
- Report the exact commands, filters and pass/fail counts.

## 2. Push and CI

- Open PRs as drafts (`gh pr create --draft`) while work is in progress; mark them ready
  (`gh pr ready`) only once the local gate passes. Ready means "review this": a server-side
  review gate reviews each new head of a ready PR and ignores drafts. To push unfinished
  work without a review, convert back to draft (`gh pr ready --undo`).
- Push; wait for CI to finish green on the exact head commit.
- On a CI failure, reproduce only the failing tests locally. Before attributing a failure
  to the change, compare it against the default branch under the same conditions.

## 3. Review rounds

**Where reviews run.** If the repository has a server-side review gate (a review app
running in CI), pushing triggers the review and only its result counts for merging; a
local panel is optional pre-push feedback. Otherwise the agent runs the panel locally.
External repositories always get local review rounds (skill `upstream-contribution`).

**Review bar.** [`reviewers/common.md`](reviewers/common.md) holds the bar and the review
canon: correctness and security, performance, code quality, waste as a blocking class, and
the House Rules a reviewer enforces. It is inlined into every reviewer prompt, so reviewers
load no other rules.

- Give the reviewer the spec sections, previous review and round task as needed
  ([review template](references/review-prompt.md)). `scripts/review-panel.sh` runs
  `scripts/prepare.py review` per lens and CLI: stable rules and lens first, then the
  base-prompt file as summary/task, PR/issue context, requirements and change. Requirements
  are indexed as R1, R2, … with source links, most authoritative first: design/spec
  sections and acceptance-test rows, linked issues (title, labels, body), non-bot
  OWNER/MEMBER/COLLABORATOR comments oldest first, then the PR description (author claims).
  Without a PR or issue, range commit messages supply the task. Standalone use accepts
  `--pr`, repeatable `--issue`, `--spec PATH[#SEC,SEC]`, `--tests ID,ID`,
  `--test-prefix PREFIX` (default `PT`) and `--summary FILE`. Section references, ranges
  such as `§3A.2.5–§3A.2.6` (also `-`), and test IDs are collected from PR/issue bodies
  and range commit messages; ranges expand in document order. Inline reference titles
  (`§10.2 Actions` or `§10.2 (Actions)`) must match the heading title; mismatches omit
  that section and are reported at the top. Sections selected without a title, including
  range members, are marked in the index and individually at the top as
  "matched by number only; verify" to expose potentially stale numbering. `--spec` wins, then a
  path named in PR/issue text (including the exact `Design: <path> [§...]` form), then
  an edited Markdown design/spec, then the best heading match under `docs/`, preferring
  `design/`, `spec/` and `specs/` on ties. Linked issues come from PR-body
  `Refs/Closes/Fixes/Resolves #N`, `owner/repo#N`, issue URLs and `--issue`.
  GitHub reads use optional `gh`; unavailable GitHub sources and unresolved references
  are reported at the top. Comments are capped at 4,000 characters with a cut notice.
  Codex defaults to `structured` (full diffs), others to `pack` (file index and hunk
  headers); `--format diff` omits spec content. `--format` overrides defaults; Codex
  prompts over 800,000 characters fall back to pack for the change, then trim comments,
  issue bodies and spec sections in that order (largest first within each source type).
  Notices identify every trim and any remaining excess from retained context.
- Run a panel of one generalist per model family, adding focused lenses where warranted
  ([review panels](references/review-lenses.md)), and loop until a full panel round finds
  no blockers. The reviewer reviews statically and runs at most one targeted test, only
  to confirm or refute a specific finding.
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
