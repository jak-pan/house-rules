---
name: reasoning-moves
description: Mandatory reasoning checkpoints for any model below the strongest available tier, and a self-audit for the rest — the ground/gate/verify/report/learn moves a frontier model performs unprompted. Use at session start on complex work, before experiments, edits, or reports, when debugging, and whenever the executing model is not the top tier.
license: MIT
---

# Reasoning Moves

Apply every move below without being told. Rules are checkable — each names the failure
it prevents. (Provenance: the intersection of what operators hand-scaffold for weaker
models and what frontier models do unprompted — receipts in EVIDENCE.md.)

## Ground (before starting anything)

1. **Read the current state first.** Prior runs, WIP, existing docs, the repo bible.
   State in one paragraph what already exists. Prevents: rebuilding what a search would
   have found; re-litigating settled decisions.
2. **Research before answering.** Bleeding-edge or ecosystem questions get real lookups,
   never "from mind". Prevents: confidently stale answers.
3. **State floor and ceiling before interpreting any metric.** What would a no-op
   baseline score? What does the oracle/ideal path score? Interpret only the distance
   between. Prevents: celebrating numbers a null system would also hit; premature
   ceiling claims (if any comparable system scores higher, your ceiling argument is dead).

## Gate (before acting)

4. **Write the bug brief before the fix.** Repro command, file:line, observed vs
   expected, candidate fix, the verification command that will prove it, and the
   requested acceptance criterion or documented invariant affected. If none is affected,
   classify the finding as opportunistic before editing. If you can't fill the brief,
   you're not ready to code. Prevents: fixing imagined bugs and off-goal findings.
5. **State the blast radius in one sentence** before edits near live processes, shared
   files, or other lanes ("this touches nothing running because…"). Identify the owner
   of anything shared before touching it. Prevents: clobbering live runs and other lanes.
6. **Pre-register experiments**: hypothesis, predicted delta with mechanism, and the
   numeric gate that decides the next step — written before launch. Compare after and
   state hit/miss. Prevents: post-hoc goalpost moving.
7. **Enumerate the candidate worlds, then run the cheapest probe that distinguishes
   them.** Two or three written hypotheses; one cheap decisive test (slice an artifact,
   grep a log, one item outside the harness) before any recompile or rerun. Prevents:
   expensive blind retries.
8. **Never claim an environmental blocker without a failed attempt in hand.** "Stuck"
   requires the error output of a real try, not a prediction. Prevents: false blockers
   and avoidable detours.

## Verify (while executing)

9. **Precondition-gate every number.** Before reporting a metric: outputs counted vs
   expected (rows, vectors, non-empty answers), correct config/binary/dataset confirmed.
   Exit 0 and "run completed" are not success. Prevents: hollow green runs (the classic:
   a scored run whose ingest silently produced zero facts).
10. **Prove the lever fired.** Any knob, flag, or fix: diff the effective downstream
    artifact (prompt, config, behavior) before crediting it. A drastic change with zero
    effect is a wiring bug, not a finding. Prevents: silent no-op knobs; dead controls
    reported as "implemented".
11. **One variable per run.** Diff the two arms' config fingerprints and state the diff
    before interpreting any delta. A bundle result only ever says "the bundle moved" —
    decompose before keeping or killing any member. Prevents: confounded conclusions.
12. **Physical tripwires halt work.** Impossible rates (above hardware/provider
    ceilings), idle GPU during "GPU work", anomalous regularity (fixed-size staggering,
    1-by-1 arrivals in a parallel system), quantized slower than full precision — stop
    and probe the mechanism before continuing. Prevents: building on a broken harness.
13. **Keep an attempt ledger on iterative work** (tried → result → distance to the
    operator's requested outcome); record which target or acceptance criterion moved.
    Revert anything that moved away from the reference before trying the next idea. When
    stuck synthesizing from a reference, replicate it 1:1 first, verify parity, then swap
    pieces one at a time. Prevents: looping; compounding hacks.
14. **Questions are not stop signals.** Answer inline and keep executing to the stated
    done-condition. Scoped asks stay scoped: the one-item probe is done and reported
    before anything expands. Prevents: stalled runs; scope creep.

## Report (before claiming)

15. **Tag every claim's evidence tier**: measured / extrapolated / read-in-source /
    unverified. A hypothesis never appears in a headline. Prevents: hypotheses hardening
    into facts by repetition.
16. **Print the noise math next to every delta** (n, spread or SE); refuse conclusions
    inside the noise band and say so; propose the larger-n design instead. Prevents:
    tuning on randomness; sub-noise "wins".
17. **Read ≥3 raw records behind any aggregate** before analyzing it — and confirm you're
    reading the right field first. Verify a subagent's key claim against primary data
    before repeating it upward. Prevents: analyzing the wrong column; laundering others'
    errors.
18. **Structure findings as verdict → verbatim evidence → mechanism → what's
    banked/running/blocked → the one decision needed (if any).** One cohesive narrative,
    never scattered fragments. ETAs only from measured arithmetic. Prevents: "all over
    the place" reports; wishful forecasts.

## Learn (after failure)

19. **Converge to one evidenced root cause.** A list of theories is not a deliverable;
    every causal claim cites a log line, trace, or measurement. For regressions, the
    cause is in the diff from last-known-good — find the difference before forming
    theories. Prevents: theory-dumping; running in circles.
20. **Salvage before rerun.** After any kill/crash/park: inventory what is banked and
    reusable, state it, and re-enter at the cheapest valid point. Prevents: paying twice
    for the same work.
21. **Commit negative results with their mechanism** so dead ends are never re-tried
    as-is. A refutation needs per-item evidence — a topline delta is not a refutation
    (check for harness artifacts first). Prevents: zombie experiments; killing valid
    ideas for harness bugs.
22. **Correct the durable record, labeled.** A wrong number in a commit/doc/report gets
    an explicit correction propagated to every artifact that carried it. Missed
    predictions are stated as misses and the forecasting method is audited. Prevents:
    silent claim drift.
23. **Same failure class three times → apply the three-occurrence reassessment**
    (AGENTS.md) before another attempt. Prevents: paying repeatedly for the same lesson;
    over-generalized rules and tools.
