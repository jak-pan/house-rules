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
  `scripts/prepare.py pr <checkout>` before preparing a PR (Python 3.11+). It fetches the base and
  checks ownership with `upstream-contribution/scripts/repo-ownership.sh`. For external
  repositories or unknown ownership it reports the ownership status and how many commits
  the branch is behind, and leaves the update method to the operator; `--update` forces
  a base merge. Only confirmed owned repositories merge by default, never rebase, and
  stop on conflicts. It prints
  context and targeted test commands without running them. `--base REF` overrides remote
  default detection. An explicit local base requires no fetch. Failed remote discovery
  uses the cached remote-tracking default branch; a failed fetch keeps the selected
  cached base. Both report stale context and skip merging. `--no-fetch --base REF`
  uses an already resolved base.
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
  the base resolver once, then `scripts/prepare.py review --base REF --no-fetch` per
  lens and CLI. Preparation failures, reviewer CLI failures, and reports without a
  `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` line are recorded in `summary.txt`
  and make the panel exit nonzero. Each run resets `summary.txt` and removes each selected
  reviewer's previous report, raw logs and prompt before preparation; cleanup failures
  also make the panel exit nonzero. Before any output changes, reviewer names must match
  `[a-z0-9-]+` and an existing file stem in `reviewers/`; all cleanup paths and the summary
  must resolve beneath the panel directory, including through symlinks, or the panel refuses
  to run. Prompt order: stable rules and lens first, then the
  base-prompt file as summary/task, PR/issue context, requirements and change. Requirements
  are indexed as R1, R2, … with source links, most authoritative first: design/spec
  sections and acceptance-test rows, linked issues (title, labels, body), non-bot
  OWNER/MEMBER/COLLABORATOR comments oldest first, then the PR description (author claims).
  Without a PR or issue, range commit messages supply the task. Standalone use accepts
  `--pr`, repeatable `--issue`, `--spec PATH[#SEC,SEC]`, `--tests ID,ID`,
  `--test-prefix PREFIX` (default `PT`, the acceptance-test ID prefix, e.g. `PT1`)
  and `--summary FILE`. Use the repository's prefix, such as `--test-prefix AT` for `AT1`.
  Section references, ranges
  such as `§3A.2.5–§3A.2.6` (also `-`), and test IDs are collected from PR/issue bodies
  and range commit messages; ranges expand in document order. Inline reference titles
  (`§10.2 Actions` when the words match the heading's leading words, or an explicit
  parenthesized title `§10.2 (Actions)`) are compared with the heading. Trailing prose
  on a bare reference need not match. Title mismatches are reported at the top; the
  section is still included and flagged for verification. Nested ranges include each
  section body only once. Sections selected without a title, including
  range members, are marked in the index and individually at the top as
  "matched by number only; verify" to expose potentially stale numbering. `--spec` wins, then a
  existing tree path named in PR/issue text (including the exact `Design: <path> [§...]` form), then
  an edited Markdown design/spec, then the best heading match under `docs/`, preferring
  `design/`, `spec/` and `specs/` on ties. Linked issues come from PR-body
  `Refs/Closes/Fixes/Resolves #N`, `owner/repo#N`, issue URLs and `--issue`.
  GitHub reads use optional `gh`; unavailable GitHub sources and unresolved references
  are reported at the top. A later GitHub read failure names the failed source and
  preserves already fetched context. Comments are capped at 4,000 characters with a cut notice.
  Codex defaults to `structured` (full diffs), others to `pack` (file index and hunk
  headers); `--format diff` omits spec content. `--format` overrides defaults;
  diff reads are bounded before prompt construction, using numstat first and streaming
  hunk headers for pack mode. Changed paths are literal Git pathspecs. Codex prompts
  over 800,000 characters fall back to pack for the change, then trim comments,
  issue bodies and spec sections in that order (largest first within each source type).
  Notices identify every trim. If the prompt still exceeds the limit after all trim
  steps, preparation exits nonzero without emitting a prompt; the error names the limit,
  final size and completed trims. The panel reports this as a preparation failure.
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
