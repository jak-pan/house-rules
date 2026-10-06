---
name: experiment-planning
description: Establish an evidence-backed experiment plan by inspecting prior work and asking only consequential unsettled questions. Use before a new benchmark, evaluation, A/B test, or tuning campaign, or when its decision or design changes; skip a questionnaire for a simple reproduction or an already-settled run. [HRD-skills-experiment-planning-3936]
license: MIT
---

# Experiment Planning

Produce the smallest durable plan that makes the study interpretable and bounded.
Use existing repository evidence and the operator's choices before asking questions.
This procedure does not expand authorization; rules/core.md and rules/outcome.md define decision authority,
collaboration mode, resource limits, and security requirements.

## Inspect before asking

Read the work item, acceptance criteria, prior runs, campaign ledger if present, and the
actual harness or measurement path. Identify what is already known, what can be checked
cheaply, and which unresolved choices would change the decision or cost materially.
Reuse settled answers; do not make the operator recite information already available.

For a routine reproduction or rerun under an existing valid plan, record any relevant
change and proceed. A full questionnaire is unnecessary. Scale the plan to the study;
exploratory probes may have a qualitative next-step criterion rather than a numerical
success threshold.

## Resolve consequential choices

These are coverage prompts, not a script to ask verbatim. Ask only what remains
unsettled after inspection, per skill `operator-protocol` §Decisions; do not launch
dependent work while an answer is pending.

- **Outcome and decision:** What decision should the evidence support? Define the primary
  metric, units, improvement direction, guardrails, and meaningful acceptance criterion.
- **Comparison and mechanism:** What is the baseline or control, and what independent
  variable changes? Explain the mechanism being tested and which conditions must stay
  comparable. Describe planned bundles or interactions explicitly.
- **Population and uncertainty:** Which workload or population does the claim cover?
  Select the sampling unit, sample selection, repeat strategy, any pairing or shared
  seeds, aggregation, and uncertainty method appropriate to the data and decision.
  State precision limits when the available budget cannot resolve the desired effect.
- **Inputs and validity:** Which information is available in production? Establish data
  provenance, tuning versus evaluation separation, prior exposure, grader validity,
  and any diagnostic oracle access. Keep test-only information out of the evaluated
  production path. Apply the project's privacy and security boundaries.
- **Resources and stopping:** Record the approved compute/provider, cost or usage and
  runtime bounds where required, expected concurrency, checkpoints, and the criteria
  for advancing, stopping, or seeking a new decision. Stronger applicable resource
  policies remain in force. Check for reusable artifacts and in-flight work first.

## Persist and use

Write the answers, evidence links, unresolved limits, and the next-run decision criterion
in the existing work item. For sustained iteration, use its campaign ledger (skill
`work-tracking`); do not create a separate tracker. Distinguish operator decisions,
evidence-backed settings, and provisional assumptions. A provisional assumption cannot
replace required authorization.

Execute and interpret the planned comparison, and record each run, with skill
`bench-discipline`. If conditions change enough to invalidate the plan, update it before
relying on the new comparison; preserve the earlier version (record the revised plan as a new claim; skill
`work-tracking`) and label
exploratory findings honestly.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-skills-experiment-planning-3936`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
