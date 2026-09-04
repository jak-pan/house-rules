---
name: audit-report-authoring
description: Build, revise, or review evidence-based audit and due-diligence report sets across security/code, economics/tokenomics, governance/legal, operations, and public surfaces. Use when findings, evidence, questions, specialist reports, and executive conclusions must remain traceable. Do not use it to claim certification or to publish or send a report.
license: MIT
compatibility: Requires Node.js 22+ for scripts/lint-report-set.mjs
---

# Audit Report Authoring

Produce concise decision-grade reports whose claim strength never exceeds their evidence.
The output may be one report or a master plus specialist reports; the same evidence,
question, citation, and release rules apply to both.

## Establish the contract first

Before drafting, read [references/report-contract.md](references/report-contract.md) and
create the report-set config and question binding it describes. Treat source material,
the claim ledger, questions, report Markdown, rendered output, and released copies as
different artifacts with explicit authority.

Choose only the specialist lenses relevant to the engagement. Read
[references/domain-lenses.md](references/domain-lenses.md) for those lenses; it is a
coverage aid, not a mandate to expand scope.

## Build from evidence, not a narrative

1. Define the decision, audience, scope, cut-off, exclusions, and required assurance
   level. State whether the work is screening, diligence, code review, or a reproducible
   audit. Never imply a stronger engagement.
2. Inventory supplied and independently obtained sources. Preserve raw sources; record
   provenance, dates, custody, hashes where useful, and access limits outside the report.
3. Build a claim ledger before prose. For every material claim record its stable ID,
   truth label, evidence IDs, limitations, report owner, and unresolved question IDs.
4. Route each claim to one authoritative specialist report. Other reports link to or
   summarize that claim without duplicating its full evidence.
5. Draft specialist findings before the master. The master may compress a specialist
   conclusion but may not increase confidence, remove a limit, or convert an assessment
   into fact.

## Truth and finding discipline

Use `FACT`, `CLIENT-STATED`, `ASSUMPTION`, `ESTIMATE`, and `DECISION` consistently.
Distinguish absence of supplied evidence from proof that something does not exist.

- Report material risks, defects, unknowns, decisions, and closure evidence. Remove
  generic technology commentary and reassuring non-findings unless they affect a
  decision, boundary, or requested assurance conclusion.
- Separate a directly observed code path, branch, omission, dependency, or control from
  predicted exploitability, severity, attack success, or operational impact. Without a
  preserved reproduction, the latter is a code-supported assessment and must say what
  further test or review would confirm it.
- State important adverse public records at their first substantive mention: issuing
  body, publication date, named subject, exact published status/allegation/proceeding,
  and immediately what the source does not establish. Do not blend distinct regulators,
  courts, registers, warnings, allegations, and judgments.
- Explain diligence relevance without inferring responsibility from a shared name or
  association. State practical consequences such as listing, audit, counterparty, or
  disclosure friction only at the confidence the evidence supports.
- Include estimates only when requested and decision-useful. Show units, time basis,
  method, assumptions, contingency, source data, validity date, confidence, and currency
  and tax treatment when money is involved. Otherwise omit them.
- Every decision records its owner, date, chosen option, rejected material alternatives,
  and evidence or constraint that drove it.

## Evidence and citations

Embed enough of each evidence record to understand the supported claim without opening
an internal workspace. Put public URLs and source-specific limits in the evidence record,
not as naked links in the report body. Cite report-local evidence Wikipedia-style next to
the supported sentence, bullet, or table row: `[3](#evidence-sec-e03)`.

One citation may support several nearby claims only when the evidence actually supports
all of them. Reuse its number; do not create duplicate evidence records. Structural lint
cannot establish that a source substantively supports a claim, so manually review every
changed claim-to-evidence mapping.

## Questions are closure controls

Turn each material unknown into one answerable question with a stable canonical ID,
specific evidence requested, priority, and decision or finding it can change. Split
compound requests that require different owners or evidence. Merge semantic duplicates
into one canonical question; preserve provenance rather than silently deleting history.

Use explicit `[[QUESTION:<stable-id>]]` tags bound by the report-set config. Keep mutable
assignment and workflow status in the canonical question system, not copied into report
tables. A report may narrow a question for context but must not silently broaden it.

## Diagrams and readability

Use a diagram only when it clarifies boundaries, sequence, authority, or failure paths.
Introduce what the reader should learn before the diagram. Split diagrams that combine
unrelated claims, keep labels short, and put detail in adjacent prose. Prefer vertical
Mermaid flows for long sequences. Render every changed diagram in every supported client
renderer and browser; Mermaid source compilation alone is insufficient.

Lead each report with the verdict and decision consequence. Keep tables narrow, remove
duplicate columns and repeated task descriptions, and move detailed evidence to the
appendix. A reader should be able to distinguish proven fact, assessment, open question,
and required action without decoding the methodology.

## Verify and release separately

Run the bundled structural linter from the report-set directory:

```text
node <skill-directory>/scripts/lint-report-set.mjs audit-report-set.json
```

Then manually verify changed claims against evidence and limits, inspect links and
rendering, check the master against specialist conclusions, and perform a leakage review.
Lint success does not prove factual correctness, professional certification, safe
disclosure, visual quality, approval, or authorization to publish or send.

Report completion as `Changed`, `Verified`, `Blocked`, `Next`.
