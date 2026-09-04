# Report-set contract

Use this contract when creating a new evidence-based audit report set. Adapt filenames,
specialist boundaries, and identifiers to the engagement; do not weaken traceability.

## Canonical artifacts

- Raw source material is immutable evidence.
- A private evidence register owns provenance, custody, hashes, capture dates, and access
  limits.
- A claim ledger maps stable finding IDs to truth labels, evidence IDs, limitations, and
  unresolved questions.
- Canonical question records own wording, evidence requests, assignment, and workflow.
- Markdown reports are the semantic source for rendered reports.
- Rendered files and portal views are derived.
- Released copies are immutable snapshots with their own approval record.

Do not treat a rendered view, an index, or a released copy as the editable source.

## Report-set configuration

Place `audit-report-set.json` beside the reports:

```json
{
  "contractVersion": "1.0",
  "questionBindingFile": "question-bindings.json",
  "reports": [
    { "file": "00-master-report.md", "kind": "master", "claimPrefix": "M" },
    { "file": "01-security.md", "kind": "specialist", "claimPrefix": "SEC" },
    { "file": "02-economics.md", "kind": "specialist", "claimPrefix": "ECO" }
  ]
}
```

Each filename is relative to the config. `kind` is `master` or `specialist`.
`claimPrefix` contains uppercase letters and identifies finding IDs such as `SEC-03`.
Every report filename and prefix is unique.

Place the configured question binding beside the config:

```json
{
  "schemaVersion": 1,
  "scopeId": "engagement-or-questionnaire-id",
  "questionIds": ["Q-001", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"]
}
```

Use the durable ID from the canonical question system. UUIDs are preferred when that
system provides them. `scopeId` prevents reusing a binding against the wrong engagement;
the linter verifies membership, not the external database.

## Required report metadata

Immediately below the level-one title include:

```text
Status: DRAFT
Classification: INTERNAL / CONFIDENTIAL
Date: 2026-09-04
Version: 0.1
Report contract: 1.0
Report owner: [[OWNER:Name or UNASSIGNED; role=Accountability]]
Evidence cut-off: 2026-09-04
```

Use `Technical cut-off` instead when that is the meaningful boundary. `Status`,
`Classification`, date, version, owner, and cut-off are mandatory. `UNASSIGNED` is more
truthful than inventing a person.

## Semantic tags

Finding IDs are plain stable identifiers such as `SEC-03`. Use each ID for one claim.

Question reference:

```text
[[QUESTION:Q-001]]
```

Owner metadata or dated decision:

```text
[[OWNER:UNASSIGNED; role=Security decision owner]]
```

Do not put owner tags or accountable-owner columns in question, evidence-request,
stop-gate, or decision-matrix tables. Assignment belongs to the question/workflow system.

Evidence appendix marker and record:

```markdown
## Embedded evidence

[[EVIDENCE-APPENDIX:OPEN]]

### [[EVIDENCE:SEC-E01]] [1] Released source inspection

**Supports:** SEC-03

**Type and cut-off:** FACT; source inspected 2026-09-04.

**Method or origin:** Repository and revision, tool/method, relevant scope.

**Embedded record:** The material observation, excerpt-sized fact, or calculation needed
to understand the finding.

**Limits:** What was unavailable, not reproduced, not independently confirmed, or outside
scope.
```

Evidence IDs are uppercase letters plus `-E` and a two-digit sequence. They are unique
across the report set. Citation numbers are local to each report, start at 1, follow
appendix order without gaps, and are reused for repeated citations:

```markdown
The release path accepts an unverified state transition. [1](#evidence-sec-e01)
```

Every evidence record is cited from the body. Every material finding is named by at least
one record's `Supports` field. A URL appears only inside the evidence appendix beside the
embedded record and limits. Internal absolute paths and raw-workspace links never appear
in a distributable report.

## Authority boundaries

- The master owns the overall verdict, cross-cutting stop-gates, and decision matrix.
- A specialist owns its detailed findings, evidence, limitations, and closure questions.
- One authoritative specialist owns a cross-cutting claim; other reports cite or link it.
- The master cannot strengthen, de-limit, or factualize a specialist assessment.
- A question is not evidence. An unanswered question proves only that the matter remains
  unresolved within the engagement record.
- A source URL is not evidence without an embedded record and source-specific limits.

## Assurance notice

If the engagement is not a full reproducible audit, state that prominently but in normal
body typography. Name what was and was not performed and what separate client validation,
reproduction, specialist audit, legal review, or operational test is required. Avoid both
overclaiming and boilerplate disclaimers repeated after every finding.

## Release gate

Before release, require separate evidence review, factual/claim review, confidentiality
and personal-data review, legal-sensitivity review where applicable, link validation,
multi-renderer visual inspection, named approval, immutable versioning, and destination
authorization. Passing the structural linter satisfies none of those gates by itself.
