---
name: handoff-continuity
description: Session continuity — immutable handoff files before compaction, task ledgers, AGENTS.md bible maintenance, dated reports, task filing. Use before context compaction, at session end, when work spans sessions, when spawning successor agents, or when the operator says "handover".
---

# Handoff & Continuity

"A fresh agent with a handoff file outperforms a saturated agent every time."

## The 80% rule

At ~80% context (or before any compaction), stop and write the handoff — an **immutable
record wherever the workspace tracker keeps them**: file protocol → `task handoff NNN`
under `tasks/NNN-slug/handoffs/`; external tracker → a closing comment/entry on the work
item; legacy repos → a dated HANDOVER-YYYY-MM-DD.md. Same required contents everywhere:

```
  Objective   — the standing goal, verbatim (incl. numeric targets)
  Completed   — with evidence pointers (run dirs, commits, file:line)
  Pending     — ordered next steps, cheapest/highest-signal first
  Blockers    — exact state: what's running, what's waiting on whom/what
  Decisions   — settled choices made this session + rejected alternatives (with why)
```

Handoffs are events, not documents you maintain: never edit an existing handoff —
corrections go in a new one. Never continue degraded, and never let a compaction eat
unpersisted findings. Write the full plan and
next steps down for the next agent.

## The bible (AGENTS.md)

Every repo's AGENTS.md is the persistent bible, re-read after every
context reset. On session start and after every reset:
1. Read AGENTS.md, CONTEXT.md, and the workspace's board + continuation records.
2. Append newly settled decisions to the bible so they're never re-litigated: chosen models,
   rejected alternatives (with the evidence), key locations (`.env.test.local`), owned
   defaults, environment facts that were forgotten twice.

## Filing

- Findings go where they belong, as they happen — not dumped in chat and not in assistant
  memory — they belong in runbooks and docs:
  - experiments/results → the work item's record and the campaign ledger
  - audits/reviews → dated `docs/reports/YYYY-MM-DD-topic.md`
  - operational knowledge → RUNBOOK.md; architecture → docs system map + deep dives
- Paths for runs, reports, ledgers, debug evidence, and scratch: `STRUCTURE.md`.
- Work state (item state + regenerated board + new handoff, whatever form the tracker
  gives them) travels in the same commit as the work it describes. In legacy NEXT.md
  repos, that repo's convention stays binding until migrated.

## Authorized, bounded, and durable external runs

Durability prevents loss; it does not authorize a run or prove that the run remains
relevant. Before launch, verify that the work is primary or proportional supporting work
inside the standing or campaign resource envelope. Record that envelope in the active work
record: approved agents/providers, concurrency, round limits, cost/token/runtime boundary,
and stop condition. Once inside the envelope, no per-call approval is required.

Before the first substantive call of any paid, long-running, or non-reproducible external
agent/model/tool run:

1. Choose a durable workspace path for raw stdout/stderr or the native session transcript.
2. Enable the tool's persistent/resumable session mode where available.
3. Record the session/process ID, exact model/tool, start time, cost/budget boundary, and
   output path in the active work record.
4. Confirm that output is actually being appended or that the native session can be
   resumed before allowing major spend or runtime to accumulate.

At meaningful milestones, record actual spend, tokens, runtime, and rounds against the
remaining envelope. A retry of the same failed operation is not a new round; a new
provider, work category, independent auditor, or broad review pass is.

During a quiet or apparently stalled run, distinguish UI/wrapper silence from process
failure: inspect the process, terminal/session state, transcript growth, checkpoints, and
provider status. A timeout is an observation, not authorization to kill the run.

Before interrupt/restart/replacement, persist the latest recoverable output and decide
whether the evidence proves no progress. For a materially paid or unique run, obtain the
operator's approval unless the operator already ordered the stop. An urgent safety stop
takes precedence; capture only what can be captured without delaying it. If durable
capture cannot be established at launch, ask the operator to accept the loss risk or use
a cheaper/reproducible probe instead.

Boundary: this gate applies to external agents, model CLIs, remote jobs, benchmarks,
crawls, and similarly costly or unique work. It does not add ceremony to ordinary short,
cheap, reproducible commands. Source incident: 2026-08-19 paid Claude review interrupted
while useful output existed only in an ephemeral wrapper stream.

## Resuming

"continue task NNN" (or "read HANDOVER-*.md and continue") is a complete instruction.
Resume means: read the task.md + latest handoff + bible + campaign ledger, verify claimed
state against reality (is that run still live? did the commit land?), then continue the
Pending list — without re-testing what the ledger settles and without re-asking answered
questions. After a crash: commit recoverable work first (when commits are authorized),
then resume.
