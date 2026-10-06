# GitHub text: issues, PRs, review comments, replies, fix commits

Forms for every issue, PR body, review comment, reply to review and fix-commit message.
The language rules of skill `operator-writing` apply to all of them. Examples are adapted
from a public upstream durability report and its fix; names are shortened.

## 1. Rules for all GitHub text

- Lead with the observable behavior and its effect. Implementation history comes last, or
  not at all.
- Every claim has evidence: a commit SHA, a version, a command, a count, a log line or a
  permalink.
- Name the commit or version every observation was made on.
- Code references are full-SHA permalinks. Put the one that proves the claim on its own
  line, so it renders as a snippet.
- Label each claim that no test covers as "From code reading" or "Hypothesis".
- State limits: what was not run, not built or not covered, and why.
- An internal label, code or ID may follow its plain description, never replace it. Never
  cite a file the reader cannot open; link it or state its content.
- Omit empty sections. Never write "N/A" sections.
- Table cells hold a few words, such as a test name and PASS or FAIL. Details go in
  bullets below the table.
- Size work per [AGENTS.md prime rule 13](../../../AGENTS.md#prime-rules).
- No ceremony. A "found by" line is allowed at the end, with a link to
  the report or review.
- Issues filed automatically by review or audit tools follow the issue form too. Titles
  never carry internal labels and never stop mid-phrase.

## 2. Issue

Title: `<area>: <observable wrong behavior> [when <trigger>]`, in plain words.

Labels: one priority label (`P0`–`P3`, skill `work-tracking`) and one type label (`bug`,
`enhancement`, `documentation`) where the repository defines them.

```markdown
<One paragraph: what goes wrong, for whom, and the consequence.>

## Reproduction
Seen on <full SHA or version>. <Other builds checked.>
1. <step>
2. <step>

Expected: <behavior>.
Actual: <behavior, with the verbatim log line or error>.

## Evidence
- <measurement with its unit and population>

<permalink, on its own line>

## Cause
<Mechanism, one sentence per step. Label untested parts.>

## Proposed change
<Smallest change that fixes the behavior. Optional for a pure report.>

## Acceptance criteria
- <test that fails before the fix and passes after>

## Out of scope
- <related problem>: <link to its issue>
```

Rules:

- One problem per issue. An audit with several findings numbers them; each fix PR names
  its finding number.
- The first paragraph alone tells the reader what breaks.
- The issue body contract is [Issue report](../../../prompts/util/issue-report.md).
- A feature or follow-up issue replaces Reproduction with "Current behavior" and "Wanted
  behavior". It keeps Acceptance criteria.
- Work-item sections (Scope, Decisions, Lane, Design; skill `work-tracking`) follow
  Acceptance criteria when the item has them.

Example:

```markdown
Title: Recovery: a truncated newest manifest makes a writable open delete every segment

A writable open trusts the newest manifest even when it is truncated. It deletes every
segment the manifest does not list, then crashes. A power loss or a full disk during
flush() can therefore delete data that was already on disk.

## Reproduction
Seen on 8321c131. main (98aa126) has the same code on this path.
1. Create a collection with 2,600 documents in segments 0, 1 and 2.
2. Truncate the newest manifest to 0 bytes.
3. Open the collection writable.

Expected: open fails and deletes nothing.
Actual: the log shows "Recovery removed orphan segment directory" for 0, 1 and 2, then
SIGSEGV. Every later open crashes.

## Evidence
- Of all 439 truncation lengths, the five cuts on a field boundary crash. Three delete
  every segment; two delete some.
- Disk full (HFS+ 30 MiB image, 52 KiB free): flush() returns OK, and the only remaining
  manifest is cut at 8,192 bytes.

https://github.com/OWNER/REPO/blob/<full-sha>/src/db/collection.cc#L2086-L2108

## Cause
The manifest is written in place, and the stream close is never checked. A cut at a
field boundary still decodes. Orphan cleanup trusts the decoded segment list.

## Acceptance criteria
- Truncating the manifest at every length never makes open delete a file.
- A short manifest write makes flush() fail and keeps the previous manifest.

## Out of scope
- Syncing segment data before the manifest: finding 1.
```

## 3. PR body

Title: `type(scope): <imperative change, as behavior>`. The issue number goes in the body,
not the title.

```markdown
<One paragraph: what changes for the user or caller, and why.> Closes #<n>.

Goal: <plain description of the recorded goal> (#<goal issue>).

## Problem on <base branch>
- <mechanism, one sentence each>

## Changes
- **<label>:** <what it does>. <why>.

## Tests
| Test | <base> | this PR |
|---|---|---|
| <name> | FAIL | PASS |

- <name> on <base>: <failure mode>.
- Commands: <exact commands, totals passed/failed>. Full log: <CI link>.

## Compatibility and cost
<Format, API and upgrade effect. Extra work per operation.>

## Rejected alternatives
- <alternative>: <reason>.

## Out of scope
- <item>: <link>.

## Not covered
- <what was not run or not tested, and why>.

<closeout checklist, skill design-flow §6>
```

Rules:

- Every new regression test appears with its result on the base branch and on the PR
  head.
- A defect that a review round found and fixed stays listed under Tests as "failed on an
  earlier head: <behavior>". This shows the tests detect it.
- A failure that also happens on the base branch is reported with that control, never
  hidden.
- Gate output in the body is commands plus totals. Per-binary counts belong in the CI
  log.
- Name each concession: "This is a concession: <what is not guaranteed>."

Example:

```markdown
Title: fix(recovery): publish manifests atomically and fail closed on a damaged manifest

Publishes the manifest atomically and validates it on open, so a crash or a full disk can
no longer make recovery delete segment data. Addresses finding 2 of #789.

## Problem on main
- Version::Save writes manifest.N in place; the stream close is never checked.
- Decode accepts a file cut at any field boundary, including 0 bytes.
- A writable open then deletes every unlisted segment and crashes.

## Changes
- **Atomic publish:** write manifest.N.tmp, check every write, the sync and the close,
  rename, sync the directory. A failure leaves the old manifest in place.
- **No fallback to an older manifest:** the checkpoint already removed the older
  generation's WAL, so loading that manifest would drop acknowledged writes.
- **Unsupported directory sync:** EINVAL, ENOTSUP and EOPNOTSUPP count as success. This
  is a concession: the rename is not proven durable on such file systems.

## Tests
| Test | main | this PR |
|---|---|---|
| EveryTruncationFailsClosed | FAIL | PASS |
| ShortWriteKeepsPrevious | FAIL | PASS |

- EveryTruncationFailsClosed covers all 433 lengths from 0 bytes. On main it removes 3
  segment directories, then crashes with SIGSEGV.
- ShortWriteKeepsPrevious forces a short write with RLIMIT_FSIZE. On main, flush()
  returns OK and the previous manifest is removed.
- Failed on an earlier head: a batch acknowledged 286 documents after a failed publish,
  and they were missing after a reopen.

## Compatibility and cost
On-disk format unchanged. Each publish adds two syncs and one rename.

## Out of scope
- Syncing segment data files before the manifest: finding 1 of #789.

## Not covered
- Windows: not built or run.
```

## 4. Review comment

```markdown
**<Blocking | Non-blocking>: <observable defect in one sentence>.**

Where: <permalink at the reviewed head SHA>
What happens: <mechanism, one sentence per step>.
Why it matters: <requirement, spec line or user effect>.
Expected: <correct behavior>.
Suggested fix: <smallest fix>. Test: <regression test that fails today>.
```

Rules:

- One finding per comment, anchored on the line when the host allows it.
- The bold first line makes sense alone. A finding code may follow it, never replace it.
- "Blocking" uses the review bar of skill `pr-ready` (`prompts/util/review-bar.md`).
- Label untested claims "From code reading".
- An approval names the head SHA it covers and what was checked.

Example:

```markdown
**Blocking: documents written after an uncertain publish are acknowledged, then lost.**

Where: <permalink to the batch write loop at the reviewed head>
What happens: an automatic buffer flush hits a failed directory sync and raises the
fence. The writing block moves on, but its WAL does not. The rest of the batch is still
written and acknowledged.
Why it matters: an acknowledged write must survive a reopen. In the test, 286
acknowledged documents were missing after the reopen.
Expected: once the fence is raised, the rest of the batch fails.
Suggested fix: check the fence after taking the write lock and before each document.
Test: raise the fence mid-batch; every acknowledged document survives a reopen.
```

## 5. Reply to review

```markdown
Fixed in <short SHA>.
Before: <the defect, as observed>.
Now: <the new behavior>.
Test: <name> fails on <previous head> and passes on <new head>.
Limit: <what the fix does not cover, if anything>.
```

or

```markdown
Not changed: <one-sentence reason>.
Evidence: <test, measurement, spec line or permalink>.
<What would change the decision, or a follow-up issue link.>
```

Rules:

- Reply to every review thread before merge, then resolve it (skill `pr-ready` §3).
- Answer the finding in the reviewer's terms. Do not restate the review.
- A deferred finding gets a tracked issue, and the reply links it.
- Thanks and offers are one sentence each, at most.
- A reply to a maintainer's general comment states why the work matters to us and what
  we can do next.

Example:

```markdown
Fixed in 1e5c2e2.
Before: a directory sync that failed with EINVAL fenced the collection, so every writable
open on that file system failed.
Now: EINVAL, ENOTSUP and EOPNOTSUPP mean "cannot sync directories". The publish logs it
once and succeeds. Other errors still fence.
Test: UnsupportedDirectorySyncIsNotAFailure fails on the previous head and passes.
Limit: on such file systems the rename is not proven durable. PostgreSQL's
fsync_fname_ext() makes the same concession.
```

## 6. Fix-commit message

```text
type(scope): <imperative change, as behavior>

<Old behavior, past tense. Its consequence.>

<The change, one fact per sentence or one bullet per change. Why.>

<Compatibility, if any: format, API, upgrade.>

Test: <regression test name(s)>.
Fixes #<n> | Refs #<n>
<attribution trailers>
```

Rules:

- The subject names the behavior, not the review round. Never "address review findings".
- A review-round commit lists each fixed finding as before → now.
- No gate logs. Commands and totals go in the PR body; full logs stay in CI.
- No reference to a file outside the repository. State the finding itself.
- A commit that changes a test's expectation explains why the old expectation was wrong.
- Write a body unless the subject alone explains the change and its reason.

Example:

```text
fix(recovery): report a failed directory close after an unsupported sync

SyncDirectory treated EINVAL from the sync as "directory sync unsupported" and returned
success. It returned success even when the close that followed failed. Before, a close
EIO after a sync EINVAL was reported as success.

Normalize only the sync result. Check the close separately and always report its
failure, as PostgreSQL's fd.c does.

Test: CloseFailuresAreNotMasked.
Refs #789
```
