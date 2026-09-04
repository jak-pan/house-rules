---
name: bench-discipline
description: Benchmark and experiment methodology — no test-targeted hacks, variance floors, controls and oracle ceilings, one-knob isolation, prove-the-knob-fired, cost ladder, comparability, judge validation. Use whenever designing or running benchmarks, evals, A/B tests, or tuning sweeps.
---

# Bench Discipline

The campaign ledger (`PUSH-TO-<goal>.md` in the work item's record — file tracker:
`tasks/NNN-slug/`; paths: `STRUCTURE.md`) is the house style.

Paid experiments run autonomously inside the campaign resource envelope. Statistical
requirements, repeated baselines, and model cross-checks must fit that envelope. Crossing
it requires a proposed expansion, not silent reduction of experimental rigor.

## Cardinal rule: no cheating

Nothing enters the pipeline that couldn't run blind in production:
- No gold answers, gold strings, or test samples in prompts, few-shot examples, or heuristics.
- No per-question special-casing, no category routing, no substring gold-matching.
- No hardcoded text extraction (regex dates, keyword lists) — structured metadata and IDs only.
- Never tune to match broken gold — cross-check a "miss" against raw source first; ~40% of
  misses can be benchmark noise.
- Borderline idea? Flag it before building. Gaming the test must never be a plausible
  reading of your work.

## Cost ladder — cheapest experiment that answers the question

1. Single-item repro outside the harness (~$0, seconds).
2. Answer-only rerun on stored artifacts (<$1). Re-judge stored answers instead of re-running.
3. Small diverse smoke set (n=5–50) → medium (~100Q) → full run, scaling up only on improvement.
4. Reuse golden datasets/artifacts; **only launch what's missing** — never rerun work whose
   results already exist. Finish in-flight paid runs before starting new ones.
5. Track $ after every paid run; report cost and cost-per-point in comparison tables.
   Verify costs against provider pricing pages, not vibes.

## Variance protocol

- Measure the noise floor first (N-run baseline, report spread).
- One run is never a result; a single attempt is not tuning. K=2–3, report medians.
- A lever wins only when ranges separate (ON-min > OFF-max). Inside the band = noise, say so.
- Never re-roll nondeterministic stages (distill, think-on answering) across comparison arms —
  keep variance low by construction, reuse the same base.
- Comparability is sacred: same question set, same candidates, same judge across arms. If
  settings drift polluted runs, invalidate them wholesale and rerun baselines.

## Knob methodology

- One variable at a time: atom sweeps → additive combos → interaction matrix. Sweep with
  bracketing points around inflections.
- **Prove the knob fired** before crediting any delta: diff the effective prompt/evidence/
  config downstream. Audit for silent no-op knobs (a yaml that never loads is a classic).
- Drastic change with ~zero effect = pipeline-bug hypothesis first, finding second.
- Every experimental lever: config/env-gated, default OFF, byte-identical when unset.
  Keep tested options as switches; set measured sweet spots as experiment-lever defaults
  (act + notify) — shipped product defaults follow the `operator-protocol` ladder.
- **Defaults ARE the settled config.** The baseline run is the bare default run — zero
  tuning env vars; flags exist only for the lever under test. A canonical command that
  needs a wall of pins is config drift: promote the settled values into shipped defaults
  and delete the pins. When a default flips, re-baseline (N≥2) — scores across a default
  change are not comparable; running the old value afterwards is a pinned, named test.
- Diagnostic targeted loops beat random knob hunting — always work from a mechanism.

## Controls and ceilings

- Always run the feature-off control alongside the experiment — and check the control is
  *clean* before reading the treatment (a contaminated control means the instrument is
  broken, not the hypothesis confirmed).
- Oracle first, backwards: gold-path/full-context ceiling runs isolate reader ceiling from
  retrieval before you tune retrieval. State the floor (no-op baseline) and ceiling before
  interpreting anything between them.
- **Pre-register each experiment**: hypothesis, predicted delta with mechanism, and the
  numeric gate that decides the next step — written before launch; hit/miss stated after.
- **Decompose the target into stage ceilings** (e.g. evidence-in-context % vs final score)
  and spend only on the binding stage; a 2% lever that dominates cost is a lever to remove.
- **Apparatus parity, stated explicitly**: same models, same reasoning effort, same
  concurrency, same judge, same dataset version across all arms. Performance-comparison
  arms run sequentially on shared hardware, never concurrently.
- **A config bug invalidates the ladder**: mark every polluted run invalid and rerun the
  baseline ladder — never mix polluted and clean numbers.
- **Validate the judge/grader against the primary source** (the benchmark's own spec) by
  inspecting actual runtime prompts, and audit the dataset itself when scores plateau
  (variant? distractors present? gold labels sane?) before tuning further.
- **Detect sub-noise levers by subset isolation**: a real lever changes a deterministic
  subset — compare on that subset with a ≈0 noise-check on the untouched remainder.
- When it fits the resource envelope, cross-check prompt changes on a cheaper/weaker model
  too — improvements that only help the strongest reader are fragile.
- Sanity-check every cost/token/time figure against the pricing unit and a Fermi estimate;
  a 100×-off number is a bug, not a result.
- Triage every miss by mechanism: model bug / retrieval miss / broken data / shaky gold /
  judge-strict → compute the honest reachable ceiling. Never accept "ceiling" while a
  competitor scores higher; quantify headroom instead.
- Validate the judge: check judge prompts against the paper/source, read judge traces, test
  judge strictness before trusting scores. Aggregate score never tells the full story —
  per-question forensics does (see `failure-forensics`).

## Runs

- Release builds, always. Measure the concurrency sweet spot, then set it as default.
- I/O-bound stages run at provider-limit parallelism; anything progressing 1-by-1 is a defect.
  GPU/latency benchmarks run strictly sequentially, one process at a time.
- Checkpoint every step so runs survive kills; artifacts (verdicts, per-question debug,
  gold-eval) are the source of truth, named run dirs under `runs/…`.
- Record a run manifest: git sha, config hash, model IDs + reasoning effort, params, cost. ⚒
- Report p95/p98 for latency and rank metrics, not means.
- Log the running ledger (`PUSH-TO-<goal>.md`): baseline table, knob map with wired-status,
  tried → result → verdict. Future sessions must be able to continue without re-testing.
