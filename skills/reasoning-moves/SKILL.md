---
name: reasoning-moves
description: Proportional reasoning checkpoints for complex changes, experiments, investigations, and evidence-based reports. Use when assumptions, causal claims, or verification need a deliberate check; scale to the task without relying on model-tier labels.
license: MIT
---

# Reasoning Moves

Use the relevant checkpoints to catch unsupported assumptions and wasted work. They are
a review aid, not a requirement to narrate every step, invent extra documents, or apply
an experiment protocol to a simple question. Decision authority and the operator's
selected collaboration mode come from AGENTS.md; these checkpoints do not redefine them.

## Ground

- Read current state, existing evidence, and applicable project rules before building
  on assumptions. Reuse settled decisions and valid completed work.
- Verify changing ecosystem facts against current primary sources when relevant to the
  answer. Label unverified assumptions instead of presenting memory as evidence.
- Identify the requested outcome and the uncertainty that matters to it. For a study,
  use `experiment-planning` to establish the comparison and decision criterion; a floor
  or oracle is useful only when it answers that study's question.

## Gate

- Before a bug fix, establish observed versus expected behavior, affected requirement,
  available reproduction evidence, and how the repair will be confirmed. Record these
  in the existing work item at the detail needed to reproduce the issue.
- Before changing shared files, resources, or live processes, identify their owner and
  the likely impact. Apply the existing authority, security, and resource boundaries.
- For an ambiguous diagnosis, identify plausible explanations and choose a cheap probe
  that distinguishes them. Use `failure-forensics`; do not force a fixed number of
  hypotheses or postpone relevant environmental evidence.
- Support a claimed blocker with observed evidence. Do not attempt a prohibited or
  destructive action merely to prove a known permission or safety boundary.

## Verify

- Confirm that the measured outputs, input coverage, configuration, and measurement
  boundaries match the claim. A successful process exit alone does not establish
  correct behavior.
- Verify that a changed setting or code path took effect before attributing a delta.
  Little effect can indicate a wiring problem, insufficient precision, or a valid null
  result; distinguish them with evidence.
- Compare the arms' effective conditions. Follow the planned independent variable or
  experimental design; a bundle comparison supports a bundle-level conclusion unless
  additional evidence isolates its components (`bench-discipline`).
- Treat surprising physical signals as reasons to check expectations, units, workload,
  and instrumentation. They are not automatic proof of a defect. Pause dependent
  conclusions when the measurement is suspect; follow the resource policy for any
  intervention in running work.
- Keep an attempt ledger for sustained iteration: tried → result → effect on the
  requested outcome. Preserve evidence before reverting a failed candidate. Avoid
  layering compensating changes on an unexplained regression.

## Report

- Distinguish measured results, source-backed facts, extrapolations, and hypotheses.
  Attach the evidence and limitation needed to assess a consequential claim; do not
  require a label on every ordinary sentence.
- For noisy comparisons, report the sampling design and relevant uncertainty alongside
  the effect. Apply the method selected for the study rather than a universal range
  or sample-size rule. State an inconclusive result when the evidence cannot support
  the requested decision.
- Inspect enough primary records to verify field meaning, data integrity, and the
  important aggregate claims. Choose coverage for the heterogeneity and consequence
  of the claim rather than a fixed record count. Verify delegated key claims against
  primary evidence before repeating them.
- Lead with the result and explain its evidence, implications, remaining work, and any
  required decision. Follow AGENTS.md's communication and timing rules.

## Learn

- Tie causal claims to traces, measurements, or reproductions. Accept multiple supported
  causes or an explicit unresolved result; a local diff is a lead rather than a verdict.
- After a failed or interrupted run, inventory valid reusable artifacts and resume at
  the cheapest informative point. Respect artifact retention and run-stop policies.
- Record negative and inconclusive results, tested conditions, and the evidence in the
  Git-tracked work item or campaign ledger. Do not infer a mechanism from a score alone.
- Correct erroneous durable claims explicitly and propagate the correction to affected
  reports. Preserve the original evidence and explain changed interpretations.
- Apply AGENTS.md's three-occurrence reassessment before repeating the same failure
  class again. Reconsider the mechanism and scope, not just the next patch.
