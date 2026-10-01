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
  `scripts/prepare.py pr <checkout>` before preparing a PR (Python 3.9+). It fetches the base and
  checks ownership with `upstream-contribution/scripts/repo-ownership.sh`. For external
  repositories or unknown ownership it reports the ownership status and how many commits
  the branch is behind, and leaves the update method to the operator; `--update` forces
  a base merge. Only confirmed owned repositories merge by default, never rebase, and
  stop on conflicts. It prints
  context and changed files grouped as source/test/docs, pointing to the repository's
  declared gates; it neither derives nor runs stack-specific test commands. `--base REF`
  overrides remote default detection. An explicit local base requires no fetch. Failed remote discovery
  uses the cached remote-tracking default branch; a failed fetch keeps the selected
  cached base. Both report stale context and skip merging even with `--update`.
  `--no-fetch --base REF` uses an already resolved base without fetching and still merges
  on owned repositories or with `--update`. Git and gh run non-interactively.
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
  ([review template](references/review-prompt.md)). `scripts/review-panel.sh` builds each
  reviewer's prompt with `scripts/prepare.py review`: stable rules and lens first, then the
  task, PR and issue context, requirements (spec sections, linked issues, maintainer
  comments, PR description) and the change. A reviewer without a verdict, a preparation
  failure or a CLI failure fails the panel. Exact behaviour, limits and safety rules:
  [preparer reference](references/preparer.md).
- **Quick review** (`scripts/quick-review.sh`): one reviewer from family a, for small,
  well-understood changes: fix-diff check-backs after a full round, docs and configuration
  edits, CI and build fixes, small refactors. Never for a first review of a feature, access
  control, confidentiality, durability, storage, security-sensitive paths or new mechanisms.
  It refuses changes above 300 changed lines by default; a blocker or spec issue it raises
  sends the change back to the full panel after the fix. For an eligible change its approval
  completes review; for a check-back it completes the round the full panel opened.
- Run a panel of one generalist per model family, adding focused lenses where warranted
  ([review panels](references/review-lenses.md)), and loop until a full panel round finds
  no blockers. The full panel reviews the first head and the final head, and any fix that
  touches a shared mechanism or a large diff; check-backs in between may be quick reviews. The reviewer reviews statically and runs at most one targeted test, only
  to confirm or refute a specific finding.
- The fixer closes every blocking item from all reviewers in one run, with the smallest fix
  and a regression test each, in one commit per round, and searches the code for the same
  pattern so every instance is fixed, not only the cited line. The next review names that commit and marks each prior
  blocker RESOLVED or NOT. A fixer never approves its own fix.
- When a fix meets a genuine design choice, the fixer stops and reports the options; the
  lead decides (skill `operator-protocol` §Decisions).
- **Hosted review bots.** Review threads from bots the host runs on the PR (for example
  GitHub Copilot) are reviewer input for the next fix round, judged by the same bar. Before
  merging, the lead replies to each with the fix or the reason it is not one, and resolves it.
- **Done and mergeable.** A change is mergeable when every reviewer of the latest full
  panel returned no Blocking items (reviewers/common.md) on the final head, or on an earlier
  head whose later commits only resolve those reviewers' own blockers and pass a quick
  check-back, and CI is green. Follow-ups are filed as tracked issues before merging; they
  never hold the merge. A slower reviewer's findings on an older head feed the next fix
  round; its fixer never pushes onto a head that moved. After three consecutive full rounds
  that each surface new blockers, stop iterating: simplify, split the change or escalate a
  decision instead of another round.
- **Same class twice: change the mechanism.** When one class of defect blocks two
  consecutive rounds, stop patching call sites. First ask whether the spec is unclear and,
  if so, get the decision; otherwise the next fix introduces one shared mechanism that
  makes the class impossible (AGENTS.md §Three-occurrence reassessment).
- **No idle gaps.** A fix run pushes and starts its review in the same job; a review that
  needs a fix starts the fix in the same job. The lead intervenes only for decisions.
- **Slow reviewers never block.** When one family is much slower, the fixer starts as soon
  as the faster reviewers report. The slow reviewer keeps reviewing a snapshot of its head
  in the background. When it reports, a second fixer starts at once in that snapshot for
  the findings that do not overlap the running fixer's reports, checks each against the
  code, and merges the branch before pushing; anything left goes to the next fix round.
  At the final head the slow reviewer still reviews, but only
  the diff since its last reviewed head; a merge needs every reviewer's approval.
- **Current base before the final round.** Merge the default branch into the PR branch
  before its final review, so the reviewed head is what CI and the merge see.
- **Spec check before implementing.** Before a work package's first code, a design-spec
  reviewer reads the spec sections it implements, with the recorded decisions attached,
  and every open question goes to the operator first; implementation starts on settled
  text.

## 4. Merge and cleanup

- Merge only when the reviewer approves the exact head, CI is green on that head, and the
  closeout checklist holds (skill `design-flow` §6). Pin the head
  (`gh pr merge <n> --match-head-commit <sha>`) in the repository's merge style. No
  auto-merge unless the operator asked.
- Then update the tracking item, delete the branch, and remove the lane (skill
  `agent-lanes` §Lane cleanup).
