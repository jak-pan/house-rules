---
name: failure-forensics
description: Per-item forensic root-cause procedure for wrong results, regressions, score drops, slowdowns, and operator-reported symptoms. Use when a run underperforms, a metric moves unexpectedly, something got slower, or the operator says "investigate", "forensics", or "why".
license: MIT
---

# Failure Forensics

## Regressions: diff first

Something worked before and doesn't now → the cause is in the diff, not in the cosmos:
1. Enumerate what changed since it last worked (session edits, config churn, defaults, deps,
   model/provider switches). A change made in this session is the prior.
2. Bisect/difference against the last-good state; retry the old configuration to isolate.
3. Only after the diff is exhausted do environmental hypotheses enter.

## Wrong results: per-item evidence chain

Aggregate scores never tell the full story. For each failing item, pull the full chain 1:1:

```
input → ingested/distilled form → retrieved candidates (ranks, scores) →
effective prompt (the actual string sent) → model output + reasoning → judge verdict
```

- Read the actual traces. If logs can't answer a question about the pipeline, that's a
  logging gap — add the logging, then continue.
- Classify each failure by mechanism (model bug / retrieval miss / data broken / gold shaky /
  judge strict). A one-item anecdote is not forensics — do the full set difference between
  runs (a forensic difference, not a single-question analysis).
- Cross-check suspicious items against raw source data before "fixing" anything.

## Fix protocol

1. **Confirm first** with evidence, then fix.
2. Fix the root cause — never suppress, weaken an assertion, skip the case, or fail-open.
   Never mark it done with the failure "handled" by silence.
3. Add a red→green regression test when the defect affects product behavior or a
   documented invariant (`bm25_scorer_strips_stopwords_so_offtopic_facts_dont_win` is the
   house style). A harness defect receives only the smallest proof needed to trust the
   harness; it does not automatically justify a generalized analyzer or policy engine.
4. Re-run the exact repro and state the confirming evidence. Confirm every fix with
   runtime proof, not code inspection.
5. On the third occurrence of the same failure class, apply the three-occurrence
   reassessment (AGENTS.md) before another repair.

## Suspicious-constant checklist ⚒

Round or default-looking numbers are guilty until explained:
- 60s/120s timings ≈ some layer's default timeout
- 512 ≈ default max_tokens; 200 ≈ default batch/page size
- exact powers of two in throughput ≈ hidden queue/concurrency cap
- ~zero effect from a drastic change ≈ the knob never fired

## Slowdowns / parallelism

- Serial-looking progress, staggered completions, low GPU %, or ballooning RSS are defects
  with mechanisms: hidden queues, rpm/in-flight defaults, sync sections, transport limits.
- Read the physical signals first: GPU/CPU utilization, completions-per-minute vs expected
  parallelism, build profile (release vs debug). Idle hardware is evidence.
- **Anomalous regularity is a signature**: perfectly staggered batches, exact powers of
  two, 1-by-1 arrivals in a "parallel" system — a hidden constraint is speaking. Before
  adding a global default, search for consumers it could arm (a global rpm once armed a
  latent per-document charge and collapsed throughput 50×).
- Compare measured throughput against known-good priors — the delta
  is the clue.

## Method rules (hard-won)

- **Instrument before guessing**: full, ordered, labeled logging of each stage's I/O; if
  logs can't answer the causal question, fixing the logs is step one. Traces stream as
  they happen (async writer) — never buffered to end-of-run. For invisible state, add
  debug visualization (distinct colors, overlays) before another blind attempt.
  Diagnostic instrumentation is temporary unless production observability is an approved
  requirement; remove it before it becomes an unrelated maintained subsystem.
- **Debug at the raw boundary**: dump the literal payload entering each stage (the actual
  prompt, the actual bytes) — never trust the code that supposedly builds it. Reproduce
  one item outside the harness to confirm your model of the system.
- **Two-worlds probes**: when a failure is ambiguous, write down the 2-3 candidate worlds
  and design the cheapest test that distinguishes them before any recompile/rerun.
  Substitute a known-good control at a suspect stage to localize a fault in a composite.
- **Suspect the harness before the system** when results defy physics (quantized slower
  than fp16, "free" step costing more than the expensive one, same inputs → different
  outputs where determinism is expected — find the hidden recomputation).
- **Your own previous fixes are prime suspects**: layered compensating hacks cause the
  next regression; strip fudge factors before adding new ones.
- **One evidenced root cause** is the deliverable. A list of theories is not.
- Validate any new analysis tool against a hand-verified case before trusting its output;
  a tool that fails self-validation gets its results discarded explicitly.
- Present findings as one cohesive narrative: symptom → mechanism → evidence → exact fix.
