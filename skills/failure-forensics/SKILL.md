---
name: failure-forensics
description: Investigate observed failures, regressions, incorrect results, and unexpected performance with evidence and cheap distinguishing probes. Use when diagnosing a concrete symptom; ordinary explanatory questions do not require this workflow.
license: MIT
---

# Failure Forensics

Scale the investigation to the observed symptom and the requested outcome. A small bug
may need only a reproduction, a targeted fix, and confirmation. Use the work item's
existing record; do not create an experiment campaign for every diagnostic command.

## Establish what failed

1. Record expected and observed behavior, the affected inputs or environment, and the
   evidence supporting the report. Separate a reported symptom from a proposed cause.
2. Find a reproducible case or inspect the failing run's artifacts. If the issue is
   intermittent, preserve occurrence conditions and uncertainty rather than claiming
   that a successful retry disproves it.
3. Identify plausible changes since the last known good state: code, configuration,
   dependencies, data, traffic, credentials, provider behavior, or infrastructure.
   Rank hypotheses by evidence and the cost of a distinguishing probe. An outage can
   justify an environment check immediately; a local diff is often a useful starting
   point, never proof of the cause.
4. Run the cheapest informative probe. Compare with a known-good control, inspect the
   relevant boundary, or bisect a change when appropriate. Record what the probe rules
   in or out; a negative probe need not identify the remaining cause.

## Trace the relevant path

Follow the real input through the stages relevant to the symptom. For an ordinary
service this might be request → handler → dependency → response. For retrieval-backed
model evaluation it might be input → ingestion → candidates → effective prompt → output
→ grader verdict. Do not require irrelevant stages or unavailable internal reasoning.

- Inspect effective runtime values rather than inferring them only from configuration
  code. Cross-check suspicious outputs and labels against source data.
- If evidence is missing, add the smallest instrumentation that answers the causal
  question. Apply AGENTS.md's credential, data, and egress policies before capturing or
  exporting payloads; use redacted or synthetic reproductions where needed. Never dump
  secrets merely to obtain a complete trace.
- For an aggregate regression, compare changed items or representative failures and
  passing controls. Expand coverage when heterogeneity or the claim requires it; do not
  generalize from one convenient example to the whole population.
- Retain useful observations and counterexamples. Several causes can coexist, and a
  fully investigated result can remain unresolved within the available evidence.

## Performance signals are clues

State the workload, expected concurrency, rate limits, dependencies, and build profile
before calling resource behavior defective. Serial execution, low GPU use, or a slower
quantized model can be legitimate for a particular workload.

Use utilization, queue times, completions, memory, and known-good measurements to locate
the difference. Regular batch sizes, timeout-like durations, and exact caps suggest
settings or queue boundaries to inspect; they do not prove a hidden limit. A lever with
no measurable effect suggests checking whether it fired as well as whether the workload
can benefit from it. Validate units and timing boundaries when measurements appear
implausible. Check affected consumers before changing shared defaults.

## Fix protocol

1. Tie the proposed fix to an evidenced mechanism and the requested acceptance criterion
   or documented invariant. If the cause remains uncertain, label a diagnostic change
   or temporary mitigation accurately; do not call it a root-cause fix.
2. Repair the defect without silently dropping failures, weakening required assertions,
   or bypassing a security boundary. Follow AGENTS.md for material risk and scope changes.
3. Add the regression evidence AGENTS.md §Verification requires; for a harness defect,
   avoid growing a generalized analyzer to fix a local harness mistake.
4. Confirm per AGENTS.md §Verification. For intermittent failures, explain what the
   confirmation establishes and what uncertainty remains.
5. Apply AGENTS.md's three-occurrence reassessment when that condition is reached.

Diagnostic instrumentation is temporary unless ongoing observability is required.
Validate new analysis tools against a hand-verified case before relying on their output;
mark results invalid when that validation fails. Preserve useful evidence under the
project's retention policy before removing temporary instrumentation.

Before treating zero search matches as consequential evidence of absence, verify the
intended coverage (including relevant hidden or ignored paths) and confirm the check
detects a known matching example. Establish this when introducing or changing the check
or its search scope; reuse valid evidence while those conditions remain unchanged.
Routine navigation searches do not need this check.

Report the symptom, supported cause or causes, evidence, fix or next probe, and remaining
uncertainty in a cohesive account. Distinguish an unresolved investigation from a
confirmed repair, and record reusable findings in the Git-tracked work item.
