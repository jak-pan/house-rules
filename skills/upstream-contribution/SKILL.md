---
name: upstream-contribution
description: Contributing reports or fixes to externally owned repositories — prove the defect against unmodified upstream, sweep existing issues and PRs, fix and review locally over several rounds, carry a local patch meanwhile, post only when the operator says ready, and follow through until the patch can be dropped. Use when a dependency bug or gap blocks us, before filing or commenting upstream, and when handling maintainer feedback.
license: MIT
---

# Upstream Contribution

External means any repository not owned by the authenticated GitHub user or an
organization where their membership is active. A fork counts as its parent, where its
PRs, issues and comments land. Check with `scripts/repo-ownership.sh [owner/name]`.

Internal changes follow skill `pr-ready`. External repositories are different: their
maintainers own the flow, their CI runs only after we post, and every post is public and
permanent. Nothing is pushed, opened or commented upstream until the operator says ready
(AGENTS.md §Git).

## 1. Prove it is upstream's

Reproduce on unmodified upstream: its current default branch and the version we pin. A
bug needs a failing test in upstream's own test framework. A failure that exists only with
our patches is ours (AGENTS.md §Prove necessity before expanding the critical path).

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
- Contribute only what the fix needs. Tests prove the defect and guard the fix; add no
  speculative coverage, no extra checks, no refactors or reformatting outside the change,
  and no new dependencies unless they are required.

## 4. Carry the fix meanwhile

Consume the fix as a pinned patch or fork branch with provenance: upstream revision,
patch hash, and link to the upstream thread. Record it in the work item so it is dropped
later, not forgotten.

## 5. Draft, approve, post

- Draft the text in `.tmp/`. One problem per issue or PR. Lead with the observable
  failure and the smallest reproduction, then root cause, fix, tests, and performance and
  compatibility impact, with measured numbers where relevant. Write in upstream's own terms
  for a maintainer with no knowledge of our context: short, complete and
  polished, with no filler, no speculation, and no unrequested design proposals. Code
  references use full-SHA permalinks on their own line, so they render as snippets.
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
