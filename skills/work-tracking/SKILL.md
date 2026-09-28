---
name: work-tracking
description: Track work in Git with a Git-host view — claims, handoffs, and campaign attempts are empty commits with trailers on the work branch (so tracking works offline), mirrored to issues on a project board with one assignee, a Status field, `<issue>-<slug>` branches, and PRs that close their issue. Use when creating, claiming, handing off, or closing work, when coordinating several agents or people, when asked about work state, when working offline, or when migrating a Markdown task ledger (tasks/, NEXT.md).
license: MIT
---

# Work Tracking

The default implementation of AGENTS.md §Work tracking & continuity. **Git is the record:**
each work item's claim, handoffs, and campaign attempts are commits on its work branch, so
they travel with the code, work offline, and can be read by any Git-native orchestrator.
**The Git host is the shared view:** issues, assignees, a project board, and pull requests,
synchronized whenever the host is reachable. Examples use GitHub Issues, a GitHub Project,
and the `gh` CLI; on another host or orchestrator, map the view and keep the record.

## Work item and owner

- A work item has a work branch and, once the host is reachable, an issue. Branches follow
  `STRUCTURE.md`: `<issue>-<slug>`, or `<slug>` until the issue exists.
- The owner holds the branch; on the host, the issue's single assignee is the same owner.
- **Claim:**
  1. When the host is reachable, `git fetch` and confirm no remote branch exists for the
     item and the issue has no assignee.
  2. Create the branch in your lane's worktree (`git worktree add -b`), which refuses a
     branch that already exists on this machine: an existing branch means the item is
     taken here.
  3. Record a claim (below).
  4. On the host: assign yourself, re-read the assignees (anyone else listed means
     coordinate first), set Status to In progress, and mirror the claim.
- **Takeover** is explicit: a claim record on the existing branch saying from whom and
  why, then reassign on the host.
- **Release** unfinished work: a handoff record, then Status Todo and unassign on the host.
- Agents that share one host account tell lanes apart by the `Agent` trailer and the
  agent name in mirrored headings.
- Priority (AGENTS.md §Autonomy) is a `P0`–`P3` label; dependencies are the host's
  blocked-by links.

## The Git record

A record is a commit with no file changes on the work branch, carrying trailers:

```
Work-Item: 42          # the issue number, or the slug before the issue exists
Record: handoff        # claim | handoff | attempt
Agent: claude-1
```

- **claim** — a snapshot of the item's definition: Scope, Acceptance criteria, Decisions,
  and, when present, Lane, Design, Execution constraints, and Pre-flight (§Issue body).
  The branch alone then holds everything needed to work.
- **handoff** — contents and immutability: skill `handoff-continuity`. The latest handoff
  record on the branch is the continuation state. Decisions made during work are recorded
  here first.
- **attempt** — one per campaign attempt: tried → result → verdict (the campaign ledger).

Records are never amended, squashed, or rebased away; a correction is a new record. Merge
work branches with a merge commit so the records stay in the default branch's history;
where a repository requires squash merges, every record is mirrored before the merge.

## The host view

- **Issue body** — only the owner edits it. It holds Scope, Acceptance criteria, Decisions
  (settled and rejected, with why), Lane (paths this item owns while active; skill
  `agent-lanes`), Design (link to the design doc; `STRUCTURE.md`), Execution constraints
  (campaigns that use external resources: outcome, acceptance criteria, explicit
  exclusions, resource envelope, approved external providers, review-round expectations,
  actual resource usage; AGENTS.md §Resource envelopes), and Pre-flight (multi-phase work:
  verified facts, wrong assumptions to avoid, phase status; maintained and pruned).
  Decisions from handoff records are copied in when the host is reachable.
- **Mirroring** — each record is posted as an issue comment headed with its kind and agent
  (`## Handoff — claude-1`) and ending with `Record: <commit sha>`. A record whose SHA is
  in no comment is unposted.
- **Status** — the project's Status field: Todo, In progress, In review, Blocked, Done.
  Only the assignee sets it; everyone else comments. Set In review when the PR opens, and
  Blocked with a comment naming the blocker. When the merge closes the issue, the
  project's built-in "item closed" workflow sets Done; if that workflow is off, the
  assignee does.
- **Pull requests** — the PR body says `Closes #<issue>` and carries the closeout
  checklist (skill `design-flow` §Closeout); merging into the default branch closes the
  issue. Work spanning repositories uses one branch per repository; PRs in the other
  repositories reference the issue as `OWNER/REPO#<issue>` without a closing keyword.
- **Board** — the project view, plus local branches for work not yet synced; answer status
  questions from them, never from memory or a status file.

## Session loop: fetch, update, reconcile

The tracker is worked every session, not only written to at the end.

1. **Fetch at start.** Read local work branches and each one's latest handoff record. When
   the host is reachable, `git fetch` and read the board for the repositories you will
   touch: items assigned to you, anything In progress or Blocked, and open items that
   match the operator's request. Continue items you own before starting new ones; when a
   request matches an existing item, work under that item instead of creating a duplicate.
2. **Update as it happens.** Record each transition in Git and, when reachable, set Status
   and mirror. File each accepted finding, deferral, scoped-out piece, or follow-up as a
   work item in the owning repository when it arises, not at the end, and link it from the
   item, PR, review, or document that set it aside. A line such as "deferred", "not done
   here" or "belongs to the other side" in any document, PR, or handoff carries that
   item's link.
3. **Reconcile before stopping** (session end, compaction, handoff): every item you touched
   has a current handoff record and, when the host is reachable, the right Status and
   mirrored records. Go through the operator's requests from the session: each is done,
   or it has a work item, existing or new. The final report lists the items created,
   updated, and closed.
4. **Surface stale work.** Whoever finds an In progress item with no handoff or activity
   for 7 days comments on it and asks the owner, or the operator if there is no owner,
   to resume, release, or close it.

## Offline and sync

Being offline (no network, host down, CLI missing or logged out, missing token scope)
changes nothing in the Git record: claim, record, and hand off as usual and skip the host
steps. Only local branches are visible offline, so an issue claimed on another machine may
look free: claim an existing issue offline only when the operator directs it. New work
starts on a `<slug>` branch with `Work-Item: <slug>`.

When the host is reachable again, sync each work branch:

1. Push it.
2. For a slug-only item, create the issue, rename the branch to `<issue>-<slug>` (push the
   new name; delete the old remote name if it was pushed), and record a claim with
   `Work-Item: <issue>` and `Replaces: <slug>`.
3. If the issue is assigned to someone else, stop and coordinate (AGENTS.md §Work
   tracking); otherwise assign yourself and set Status.
4. Post unposted records, oldest first.

A missing login or token scope is a pending operator action (INSTALL-AGENTS.md); being
offline is not.

## Commands

Git record, in the lane's worktree. Queries use `main..<branch>` (the default branch's
name) so merged records of other items are excluded:

```sh
git worktree add -b 42-rerank-stage2 ../repo-42-rerank-stage2    # claim; refuses a taken branch
git commit --allow-empty -F .tmp/handoff.md \
  --trailer "Work-Item: 42" --trailer "Record: handoff" --trailer "Agent: claude-1"
git log -1 --format=%B --grep='^Record: handoff$' main..42-rerank-stage2    # latest handoff
git log --reverse --format='%h%x09%(trailers:key=Record,valueonly,separator=)%x09%s' \
  main..42-rerank-stage2 | awk -F'\t' '$2 != ""'                          # all records
for b in $(git for-each-ref --format='%(refname:short)' refs/heads); do     # local board
  [ "$b" = main ] || git log -1 --grep='^Record: ' \
    --format="$b%x09%(trailers:key=Record,valueonly,separator=)%x09%cr" "main..$b"
done
```

Host view on GitHub. Project operations (`gh project …` and the `--project` flags) need
the `project` token scope (read-only use needs `read:project`); the operator grants it
with `gh auth refresh -s project`. Set up a project once, before any item has a status:
create the `P0`–`P3` labels with `gh label create`, set the Status options (the mutation
replaces the whole option list and changes option IDs), then record the project number,
project ID, and Status field and option IDs in the bible:

```sh
gh project view 7 --owner OWNER --format json --jq .id
gh project field-list 7 --owner OWNER --format json --jq '.fields[] | select(.name == "Status")'
gh api graphql -f f=STATUS_FIELD_ID -f query='mutation($f: ID!) {
  updateProjectV2Field(input: {fieldId: $f, singleSelectOptions: [
    {name: "Todo", color: GRAY, description: ""},
    {name: "In progress", color: YELLOW, description: ""},
    {name: "In review", color: BLUE, description: ""},
    {name: "Blocked", color: RED, description: ""},
    {name: "Done", color: GREEN, description: ""}]}) {
  projectV2Field { ... on ProjectV2SingleSelectField { options { id name } } } } }'
```

Everyday use, with issue 42 on project 7:

```sh
# create
gh issue create --title "Rerank stage 2" --label P2 --project "Board title" \
  --body-file .tmp/body.md
gh issue edit 42 --add-blocked-by 40
# claim: an empty assignee list means unclaimed
gh issue view 42 --json assignees --jq '.assignees[].login'
gh issue edit 42 --add-assignee @me
item=$(gh project item-add 7 --owner OWNER --url https://github.com/OWNER/REPO/issues/42 \
  --format json --jq .id)
gh project item-edit --project-id PROJECT_ID --id "$item" --field-id STATUS_FIELD_ID \
  --single-select-option-id IN_PROGRESS_OPTION_ID
# mirror a record; list posted record SHAs
gh issue comment 42 --body-file .tmp/record.md
gh issue view 42 --json comments --jq '.comments[].body' | grep -o 'Record: [0-9a-f]*'
# publish the branch and open the PR
git push -u origin 42-rerank-stage2
gh pr create --title "Rerank stage 2" --body-file .tmp/pr.md
# board
gh project item-list 7 --owner OWNER --query "-status:Done" --limit 500
```

Bodies are drafted in `.tmp/` (`STRUCTURE.md`); `--body-file -` reads standard input
instead. `gh project item-add` returns the item ID, adding the issue first if it is not on
the project yet. Never use `gh issue comment --edit-last` or `--delete-last` on a mirrored
record.

## Repository without a Git host

Use the Git record alone; design docs and prototypes use the branch slug in place of an
issue number. Add a host before work spans machines.

## Migration from Markdown ledgers

For a repository still tracking work in `tasks/`, `NEXT.md`, or dated handover files:
create one issue and work branch per live item. Copy its body sections (scope, acceptance
criteria, decisions, lane, design link, execution constraints, pre-flight) into the issue
body and a claim record, its latest handoff into a handoff record, and any campaign ledger
into one attempt record linking the ledger at the last commit before deletion; mirror
them. Rename its design doc and prototype folder to the issue number, and promote finished
items' unpromoted decisions to the bible. Then delete the ledger and its mentions in
repository canon in the same commit. Until that commit the existing ledger stays
authoritative; the two never run as writable trackers side by side (AGENTS.md
§Applicability and loading).
