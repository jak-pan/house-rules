---
name: task-protocol
description: Git-native multi-agent/multi-person task management — single-writer task files, immutable handoff events, generated board. Replaces the shared NEXT.md pattern. Use when starting/claiming/finishing work in any repo using tasks/, when coordinating multiple agents or people, or when the operator asks about task state.
license: MIT
compatibility: Optional House Rules CLI requires Node.js 22 or later; Git task files can also be maintained directly.
---

# Task Protocol

**The default implementation** of AGENTS.md §Work tracking & continuity. An explicitly
selected alternative tracker (orchestrator, hosted issues) must implement the same
contract. This one applies the architecture canon to PM itself: **raw
canonical shards, one writer per file, aggregates are rebuildable caches, history is an
append-only event log**. Everything is plain files + git, so a future orchestrator can
ingest the whole history as a raw event log.

Why not one shared status file (NEXT.md-style): many writers on one mutable file means
contention, conflicts, and stale state the moment two sessions run — fine solo, wrong for
a fleet.

## Layout

```
tasks/
  TASKS.md                    # GENERATED board — never hand-edit (task index)
  NNN-slug/
    task.md                   # canonical state; ONE writer: the owner in frontmatter
    handoffs/
      YYYYMMDD-HHMMSS-<agent>-000001.md   # IMMUTABLE; sequence avoids timestamp collisions
    PRE-FLIGHT.md                   # multi-phase work only (2+ phases): verified facts,
                                    #   wrong assumptions to avoid, phase status —
                                    #   maintained and pruned, deleted when stale
```

`task.md` frontmatter (machine-readable): `id, title, status, owner, priority, depends_on,
lane, design, pr, created, updated`. Body: Scope, Acceptance criteria, Decisions (settled +
rejected, with why). `lane:` lists the file paths this task owns while active; `design:`
links the design doc (enables the `task done` migration gate); `pr:` records the PR.

Long-running campaigns that use external resources also carry an optional `Execution
constraints` body section: Outcome, Acceptance criteria, Explicit exclusions, Resource
envelope, Approved external providers, Review-round expectations, and Actual resource
usage. Ordinary small tasks do not gain this ceremony. The recorded envelope governs
orchestration as AGENTS.md §Resource envelopes describes.

## The tool

Invoke `node <HOUSE_RULES_ROOT>/bin/house-rules.mjs task ...` from inside the target
repository. The helper finds `tasks/` at the Git top level (the nearest folder containing
`.git`, else the current folder), so it works from any subdirectory; `TASKS_DIR` overrides
the tasks folder, and `design:` paths resolve from the same root. Quote paths containing
spaces. This works with Node on Windows, macOS, and Linux; no Unix utilities are needed.
The examples below use `task` as shorthand for that invocation, and the helper's own
messages write it as `house-rules task`; neither is an assumed system command.

```bash
task new "title" [P0-P3]   # scaffold next NNN
task claim NNN [owner] [--force]   # owner defaults to your identity (below); refuses if owned by someone else; --force takes over
task status NNN <state>    # pending | active | review | blocked  (done goes through `task done`)
task done NNN [--check] [--force]   # closeout GATE: requires the owner's filled latest handoff
                           # and a migrated linked design doc (design: → status: implemented or superseded);
                           # prints a closeout reminder; --check reports without writing (CI use)
task handoff NNN           # new immutable handoff file (Objective/Completed/Pending/Blockers/Decisions)
task release NNN           # require the owner's filled handoff, clear owner, set pending, regenerate board
task index                 # regenerate tasks/TASKS.md (deterministic, idempotent; refuses duplicate IDs)
task board                 # print live board, writes nothing (refuses duplicate IDs)
```

Set `AGENT_NAME` so handoffs and claims carry the lane identity; the fallback is the
operating-system user (`USER`, `USERNAME`, then the OS account). If that name is not a
valid owner (for example `John Smith`), commands stop, name the value and its source, and
ask you to set `AGENT_NAME`. The recorded owner must match that identity for `status`, `handoff`, `done`, and
`release`. An unclaimed task must be claimed first. `done --check` is read-only and
available to anyone. `done --force` explicitly bypasses the handoff and design gates,
including an unreadable design doc, but never the owner check or a board that cannot be
regenerated; record why in the final handoff. Takeover remains explicit
with `claim --force`.

The handoff gate checks the latest regular `.md` file by filename. Its author, the
`<agent>` in `YYYYMMDD-HHMMSS-<agent>-000001.md`, must be the current owner (`done --check`
compares with the recorded owner). After a takeover or release, the new owner writes a new
handoff before `done` or `release`. Each standard
section (Objective, Completed, Pending, Blockers, Decisions) needs content beyond
headings and HTML comments; write `None` when appropriate. An untouched scaffold,
empty file, or unstructured text does not satisfy the gate. This is a structural
check, not proof that the work or its evidence is adequate. Release has no force
override and preserves every handoff.
IDs are positive decimal strings of 3–18 digits, padded to at least three digits;
allocation continues from 999 to 1000. Wherever a command takes an ID, the full
`NNN-slug` directory name also works. Titles are single-line text and must not start with
`--`; owners use letters, digits, dots, underscores, or hyphens, starting with a letter or
digit. Tasks created in parallel on different branches can share an ID after a merge; then
commands given only that ID refuse, and `board`, `index`, `done` and `release` stop until
the duplicate is resolved: rename one directory to the next free ID, update its `id:`
field and run `task index`; until then, refer to each task by its full directory name.
`done` and `release` check that the board can be regenerated before changing `task.md`.
Existing handoff names remain readable; new handoffs reserve a unique
sequence suffix even when created by the same agent in the same second.

## Rules (the contract)

1. **One writer per file.** Only the owner edits `task.md`. Never edit another lane's task
   file, another agent's handoff, or the generated TASKS.md. This is a cooperative
   protocol: Git conflicts help detect competing edits across branches but do not prevent
   simultaneous claims. Claims are not locks, even within one checkout, where two agents
   claiming at once can both succeed; run parallel lanes in separate worktrees (skill
   `agent-lanes`). Coordinate ownership before parallel work; a pushed branch advertises a lane,
   not an exclusive distributed lock. The helper checks recorded ownership for task
   mutations; direct file edits still depend on cooperation.
2. **Handoffs are events.** When skill `handoff-continuity` calls for one, run `task
   handoff NNN`, fill it in, never touch it again. Continuation state = the latest handoff file, per
   task — not a global file. Corrections go in a NEW handoff.
3. **The board is derived.** After any frontmatter change: `task index`, commit `task.md` +
   `TASKS.md` together. If TASKS.md ever disagrees with frontmatter, frontmatter wins;
   regenerate.
4. **Claim before touching.** `task claim NNN` before working a task; check `depends_on`
   and the lane's file list to avoid colliding with active lanes (skill `agent-lanes`).
   Status `review`/`done` retains the recorded owner. To relinquish unfinished work,
   fill a handoff and run `task release NNN`; it clears owner and returns the task to
   `pending`. Status alone is not a release operation.
5. **Decisions land in task.md** (Decisions section) while the task lives; promotion to
   the bible follows AGENTS.md rule 11.
6. **Humans are lanes too.** Same protocol, same files; a person claims with their name.
   Status questions get answered from `task board`, not from memory.

## Session flow

```
start:   AGENTS.md §Session start (the board is `task board`)
work:    claim → execute (file findings into the task dir as you go)
pause:   handoff → index → commit (task.md + handoff + TASKS.md, one commit)
finish:  final handoff → done → commit (done regenerates the board)
release: final handoff → release → commit (release regenerates the board)
```

## Migration from NEXT.md

Incremental, per repo: `task new` for each live thread in the current NEXT.md, paste the
relevant state into each task's first handoff, then delete NEXT.md and its mentions from
repo canon in the same commit. Until a repo migrates, its existing NEXT.md law stays
binding there (repo canon wins over House Rules).
