---
name: task-protocol
description: Git-native multi-agent/multi-person task management — single-writer task files, immutable handoff events, generated board. Replaces the shared NEXT.md pattern. Use when starting/claiming/finishing work in any repo using tasks/, when coordinating multiple agents or people, or when the operator asks about task state.
---

# Task Protocol

**The default implementation** of the tracker-agnostic invariants in AGENTS.md (one owner
per item, single-writer state, immutable handoff events, derived boards) — interim until a
dedicated orchestration system ships. Any other tracker (orchestrator, hosted issues) must
implement the same contract; this one applies the architecture canon to PM itself: **raw
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
      YYYYMMDD-HHMMSS-<agent>.md   # IMMUTABLE session handoffs (append-only dir)
    PRE-FLIGHT.md                   # multi-phase work only (2+ phases): verified facts,
                                    #   wrong assumptions to avoid, decision history —
                                    #   maintained and pruned, deleted when stale
```

`task.md` frontmatter (machine-readable): `id, title, status, owner, priority, depends_on,
lane, design, pr, created, updated`. Body: Scope, Acceptance criteria, Decisions (settled +
rejected, with why). `lane:` lists the file paths this task owns while active; `design:`
links the design doc (enables the `task done` migration gate); `pr:` records the merged PR.

Long-running campaigns that use external resources also carry an optional `Execution
constraints` body section: Outcome, Acceptance criteria, Explicit exclusions, Resource
envelope, Approved external providers, Review-round expectations, and Actual resource
usage. Ordinary small tasks do not gain this ceremony. Once recorded, the envelope allows
autonomous orchestration inside it without per-call approval.

## The tool

`forge/bin/task` (zsh, no deps):

```bash
task new "title" [P0-P3]   # scaffold next NNN
task claim NNN <owner> [--force]   # refuses if owned by someone else; --force takes over
task status NNN <state>    # pending | active | review | blocked | done
task done NNN [--force]    # closeout GATE: refuses if no handoff exists or the linked design
                           # doc isn't migrated (design: frontmatter → status: implemented); prints the
                           # judgment checklist (PR merged, decisions→bible, spikes killed)
task handoff NNN           # new immutable handoff file (Objective/Completed/Pending/Blockers/Decisions)
task index                 # regenerate tasks/TASKS.md (deterministic, idempotent)
task board                 # print live board, writes nothing
```

Set `AGENT_NAME` so handoffs and claims carry the lane identity.

## Rules (the contract)

1. **One writer per file.** Only the owner edits `task.md`. Never edit another lane's task
   file, another agent's handoff, or the generated TASKS.md. A concurrent double-claim
   surfaces as a git conflict — that IS the lock working, not a bug. (The claim commit on
   `task.md` is the lock; the pushed work branch advertises the live lane.)
2. **Handoffs are events.** Session end, context ~80%, or ownership change → `task handoff
   NNN`, fill it in, never touch it again. Continuation state = the latest handoff file, per
   task — not a global file. Corrections go in a NEW handoff.
3. **The board is derived.** After any frontmatter change: `task index`, commit `task.md` +
   `TASKS.md` together. If TASKS.md ever disagrees with frontmatter, frontmatter wins;
   regenerate.
4. **Claim before touching.** `task claim NNN` before working a task; check `depends_on`
   and the lane's file list to avoid colliding with active lanes (see `agent-lanes`).
   Release by setting status `review`/`done` or writing a handoff and clearing owner.
5. **Decisions land in task.md** (Decisions section) while the task lives; durable,
   repo-wide decisions migrate to the bible (AGENTS.md) when the task closes.
6. **Humans are lanes too.** Same protocol, same files; a person claims with their name.
   Status questions get answered from `task board`, not from memory.

## Session flow

```
start:   read AGENTS.md → task board → your task.md → latest handoff in handoffs/
work:    claim → execute (file findings into the task dir as you go)
pause:   handoff → index → commit (task.md + handoff + TASKS.md, one commit)
finish:  status review/done → final handoff → index → commit
```

## Migration from NEXT.md

Incremental, per repo: `task new` for each live thread in the current NEXT.md, paste the
relevant state into each task's first handoff, then delete NEXT.md and its mentions from
repo canon in the same commit. Until a repo migrates, its existing NEXT.md law stays
binding there (repo canon wins over forge).
