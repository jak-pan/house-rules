---
name: goal-loop
description: Run autonomous iteration toward an explicit measurable target or acceptance checklist, including overnight work and "do not stop" mandates. The loop remains bound to the operator's outcome and approved resource envelope; a supporting subproblem cannot become the goal.
license: MIT
---

# Goal Loop

When a target is set (a score, acceptance checklist, "polished production ready", "until
conclusive"), the loop is the standing order inside the accepted outcome and resource
envelope. Status does not stop the loop, but a supporting subproblem never replaces its
target.

## Loop contract

1. **Ledger first.** Open/refresh the campaign ledger (`PUSH-TO-<goal>.md`, paths: `STRUCTURE.md`): operator
   outcome, measurable target or acceptance checklist, current completion gap, approved
   resource envelope, allowed primary/supporting work categories, baseline with measured
   variance where applicable, knob map with wired/tested status, and
   tried→result→verdict log. On any context reset, re-read the ledger and AGENTS.md bible
   before acting — never re-test what the ledger already settles.
2. **Cheap first.** Order the idea queue by cost (skill `bench-discipline` §Cost ladder).
   Promote to expensive runs only on cheap-tier wins.
3. **Iterate.** Test → forensics on misses → mechanism hypothesis → targeted fix → verify
   knob fired → measure vs noise floor → log verdict → next. Every cycle records which
   target or acceptance criterion moved. A supporting result counts only when it changes
   the completion gap. Diagnostic targeted loops, never random knob hunting. Parallelize
   independent probes via skill `agent-lanes`.
4. **Checkpoint everything.** Every step resumable; overnight work must survive crashes and
   kills. An empty morning result from a checkpointed campaign is your failure, not fate.
5. **Status without stopping.** Emit status lines (skill `operator-protocol` §Status format) at milestones; keep
   money counters live. Surface hard failures immediately — a dead API or exhausted credits
   kills the loop loudly, never silently.
6. **Expand only along the binding gap.** Exhausting the approved idea queue may justify
   research or a new mechanism only when it addresses the current binding completion gap
   and remains inside the resource envelope. Otherwise propose the expansion and continue
   any available primary work. Claim a ceiling only with a quantified honest-noise-floor
   argument where metrics apply.

## Hard iteration (visual/quality targets without a numeric score)

When the goal is "match this reference" or "iterate until perfect":

- Store the reference artifact locally; **diff every iteration against it before
  reporting** — never claim "closer" without having looked.
- Keep the attempt ledger: tried → result → distance-to-goal. If a change moved away
  from the reference, revert before the next idea.
- Set an iteration budget inside the resource envelope (for example, after the approved
  number of attempts without convergence, stop patching and restart from a simpler base).
  Record the budget as a standing rule for the task.
- When synthesis from a reference keeps failing: **replicate it 1:1 first** (same libs,
  same parameters, same scene), verify parity, then swap components one at a time.
- For parameter-tuning against human taste, build a calibration surface (sliders, knobs)
  and let the operator hand back values to persist as defaults — cheaper than twenty
  rounds of verbal "move it left".

## Stop or reassessment conditions

- Budget, credit, token, runtime, or round boundary reached (report exact spend + best next
  step before exceeding it).
- Credentials or an operator-only action required (name it precisely).
- Destructive/irreversible fork, or a genuine design fork → present options + recommendation.
- The third consecutive failure of the same class → three-occurrence reassessment
  (AGENTS.md) before another attempt.
- Supporting work is consuming the critical path without changing the completion gap.
- Continuing requires a new work category or expansion of the resource envelope.
- Target reached → verify with N-run confirmation, then full wrap-up: final score vs
  baseline, what moved the needle, what didn't, updated ledger, docs.

These conditions pause the affected loop, not unrelated primary work.

## Not stop conditions

Sub-step completion, "should I continue?", context anxiety (write a handoff instead — skill
`handoff-continuity`), a single failed attempt, nightfall.
