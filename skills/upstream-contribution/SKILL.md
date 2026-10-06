---
name: upstream-contribution
description: Contributing reports or fixes to externally owned repositories — prove the defect against unmodified upstream, sweep existing issues and PRs, fix and review locally over several rounds, carry a local patch meanwhile, post only when the operator says ready, and follow through until the patch can be dropped. Use when a dependency bug or gap blocks us, before filing or commenting upstream, and when handling maintainer feedback.
license: MIT
---

# Upstream Contribution

External means any repository not owned by the authenticated GitHub user or an
organization where their membership is active. A fork counts as its parent, where its
PRs, issues and comments land. Our own fork's push exception is in §3. Check with
`scripts/repo-ownership.sh [owner/name]`.

Internal changes follow skill `pr-ready`. External repositories are different: their
maintainers own the flow, their CI runs only after we post, and every post is public and
permanent. Nothing is pushed, opened or commented upstream until the operator says ready
(rules/delivery.md §Git).

## 1. Prove it is upstream's

Reproduce on unmodified upstream: its current default branch and the version we pin. A
bug needs a failing test in upstream's own test framework. A failure that exists only with
our patches is ours (rules/outcome.md §Prove necessity before expanding the critical path).

- Follow rules/outcome.md §Prove necessity before expanding the critical path for the
  supported-API, configuration and simpler-design check.

## 2. Sweep what already exists

- Search open and closed issues and PRs by symptom, error text, and affected files and
  functions; include forks and related repositories when the code is shared.
- Test any candidate fix PR against our reproduction. Check whether open PRs touching
  the same code would conflict with, supersede, or be broken by our change.
- Read `CONTRIBUTING`, CLA/DCO requirements, code style, test conventions, and recent
  maintainer review comments.
- Choose one outcome: new issue, comment on an existing one, test or review an existing
  PR, new PR, or wait.

## 3. Fix and review locally

- Branch from upstream's default branch in our fork. Keep the fix minimal and in
  upstream's style; split unrelated fixes into separate PRs.
- Red→green tests in upstream's framework. Before posting, run the upstream CI
  equivalent that covers the change; its CI cannot run for us earlier.
- Run review rounds as in skill `pr-ready` §3, applying its review bar strictly and adding
  compatibility for upstream's other users, until reviewers approve.
- Agents push to our own fork only after local review rounds that apply the same rules
  as Warden. House Rules review and Warden stay fully aligned on rules. This does not
  authorize upstream pushes, PRs, issues or comments.
- Contribute only what the fix needs. Tests prove the defect and guard the fix; add no
  speculative coverage, no extra checks, no refactors or reformatting outside the change,
  and no new dependencies unless they are required.

## 4. Carry the fix meanwhile

Consume the fix as a pinned patch or fork branch with provenance: upstream revision,
patch hash, and link to the upstream thread. Record it in the work item so it is dropped
later, not forgotten.

## 5. Draft, approve, post

`../pr-ready/scripts/prepare.py pr <checkout>` works on external forks and plain clones,
without a PR or GitHub access. It fetches the base (upstream preferred to origin), prints
changed files grouped as source/test/docs, points to the repository's declared gates,
and checks ownership when available. It derives no stack-specific test commands. For
external repositories or unknown ownership, `fix` and `pr` report how many commits the branch is behind without merging;
the operator chooses the update method, and `--update` forces a base merge. Only confirmed
owned repositories merge by default. A failed remote discovery or fetch skips merging
even with `--update`; `--no-fetch --base REF` uses an already resolved base and still
merges on owned repositories or with `--update`. Unknown ownership keeps the
operator-approval reminder; preparing a brief posts nothing.

- Draft the text in `.tmp/` in the forms of skill `operator-writing` §GitHub text. One
  problem per issue or PR. Write in upstream's own terms for a maintainer with no knowledge
  of our context: short and complete, with measured numbers where relevant, no filler and
  no speculation. Follow upstream's PR template and title convention when it has one.
  Propose a design only for the reported defect, never an unrelated redesign, and offer to
  split the work the maintainer's way. Code references use full-SHA permalinks on their
  own line, so they render as snippets.
- Review the draft text itself before showing it: every claim is verified, and every
  sentence either helps the maintainer act or goes.
- Keep provenance generic: no internal product names, private data, hosts, customers, or
  internal links.
- Show the operator the exact text and target, then post once they say ready. Link
  issue ↔ PR. The same approval applies to comments on existing threads.

## 6. Follow through

Watch the thread. Handle maintainer feedback with the same local review loop before
pushing again. Once merged and released, bump the pin and drop the local patch. If it
is rejected, decide whether to keep the patch or redesign, and record why.
