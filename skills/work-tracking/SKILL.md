---
name: work-tracking
description: Track work as Git-host issues on a project board — one assignee per issue, the project Status field as single-writer state, handoffs and campaign attempts as issue comments, `<issue>-<slug>` branches, and PRs that close their issue. Use when creating, claiming, handing off, or closing work, when coordinating several agents or people, when asked about work state, or when migrating a Markdown task ledger (tasks/, NEXT.md).
license: MIT
---

# Work Tracking

The default implementation of AGENTS.md §Work tracking & continuity: work lives on the Git
host, never in tracked status files. Examples use GitHub Issues, a GitHub Project, and the
`gh` CLI; on another host, map each step onto its issues, assignees, board, and pull or
merge requests.

## Work item and owner

- A work item is an issue; its owner is its single assignee.
- **Claim:** confirm the issue has no assignee, assign yourself, and set Status to
  In progress. An existing assignee means the item is taken: coordinate before touching it.
- **Takeover** is explicit: comment why, then reassign.
- **Release** unfinished work: post a handoff, set Status to Todo, then unassign yourself.
- Agents that share one host account tell lanes apart by name: the claim is also a comment
  `Claimed by <agent>`, each handoff is headed `## Handoff — <agent>`, and an issue assigned
  to your login but last claimed by another agent is taken. After assigning, re-read the
  assignees; anyone else listed means coordinate first.
- Priority (AGENTS.md §Autonomy) is a `P0`–`P3` label; dependencies are the host's
  blocked-by links.

## State

The project's Status field is the state: Todo, In progress, In review, Blocked, Done. Only
the assignee sets it; everyone else comments. Set In review when the PR opens, and Blocked
with a comment naming the blocker. When the merge closes the issue, the project's built-in
"item closed" workflow sets Done; if that workflow is off, the assignee does.

## Issue body

Only the owner edits the body. It holds:

- **Scope** and **Acceptance criteria**;
- **Decisions** — settled and rejected, with why;
- **Lane** — the paths this item owns while active (skill `agent-lanes`);
- **Design** — the link to the design doc (`STRUCTURE.md`), when there is one;
- **Execution constraints** — campaigns that use external resources only: outcome,
  acceptance criteria, explicit exclusions, resource envelope, approved external
  providers, review-round expectations, and actual resource usage (AGENTS.md §Resource
  envelopes);
- **Pre-flight** — multi-phase work only: verified facts, wrong assumptions to avoid, and
  phase status; maintained and pruned, not appended.

## Handoffs and campaign ledger

- A handoff is an issue comment headed `## Handoff` (contents and immutability: skill
  `handoff-continuity`). The latest handoff comment is the continuation state.
- A campaign ledger is one issue comment per attempt, headed `## Attempt`: tried → result →
  verdict.

## Branches and PRs

Branch names follow `STRUCTURE.md` (`<issue>-<slug>`, for example `42-rerank-stage2`). The
PR body says `Closes #<issue>` and carries the closeout checklist (skill `design-flow`
§Closeout); merging into the default branch closes the issue. Work spanning repositories
uses one branch per repository; PRs in the other repositories reference the issue as
`OWNER/REPO#<issue>` without a closing keyword.

## Board

The project view is the board (AGENTS.md §Work tracking); answer status questions from
it, never from memory or a status file.

## Commands

Project operations (`gh project …` and the `--project` flags) need the `project` token
scope (read-only use needs `read:project`); the operator grants it with
`gh auth refresh -s project`. Without it, record the pending grant (INSTALL-AGENTS.md)
and do not claim. Before first use, the operator adds In review and Blocked to the Status
field in the project settings (`gh` cannot edit an existing field's options), and the
`P0`–`P3` labels are created with `gh label create`. Look up the project's ID and the Status field and option IDs
once, and record them with the project number in the bible:

```sh
gh project view 7 --owner OWNER --format json --jq .id
gh project field-list 7 --owner OWNER --format json --jq '.fields[] | select(.name == "Status")'
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
# take over
gh issue comment 42 --body "Taking over from @alice: <reason>"
gh issue edit 42 --remove-assignee alice --add-assignee @me
# hand off; read the latest handoff
gh issue comment 42 --body-file .tmp/handoff.md
gh issue view 42 --json comments \
  --jq '[.comments[] | select(.body | startswith("## Handoff"))] | last | .body'
# branch and PR, in the lane's worktree
git switch -c 42-rerank-stage2
git push -u origin 42-rerank-stage2
gh pr create --title "Rerank stage 2" --body-file .tmp/pr.md
# board
gh project item-list 7 --owner OWNER --query "-status:Done" --limit 500
```

Bodies are drafted in `.tmp/` (`STRUCTURE.md`); `--body-file -` reads standard input
instead. `gh project item-add` returns the item ID, adding the issue first if it is not on
the project yet. Never use `gh issue comment --edit-last` or `--delete-last` on a handoff
or attempt comment.

## Repository without a Git host

Record work in branch names and commit messages. A handoff is an empty commit on the work
branch (`git commit --allow-empty -F .tmp/handoff.md`); design docs and prototypes use the
branch slug in place of an issue number. Add a host before parallel or multi-agent work.

## Migration from Markdown ledgers

For a repository still tracking work in `tasks/`, `NEXT.md`, or dated handover files:
create one issue per live item, copying its body sections (scope, acceptance criteria,
decisions, lane, design link, execution constraints, pre-flight) into the issue body, its
latest handoff as the first comment, and any campaign ledger as one `## Attempt` comment
linking the ledger at the last commit before deletion. Rename its design doc and prototype
folder to the issue number, and promote finished items' unpromoted decisions to the bible.
Then delete the ledger and its mentions in repository canon in the same commit. Until that commit the existing ledger stays authoritative; the
two never run as writable trackers side by side (AGENTS.md §Applicability and loading).
