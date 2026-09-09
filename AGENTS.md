# AGENTS.md — Universal

Repo-local law — `CONTEXT.md` and any repo-specific sections appended below — overrides
the universal sections of this file on conflict. Each rule has one home: this file states
invariants; the named skill holds the procedure; nothing is restated.

## Applicability and loading

These are shared working preferences, subject to the host's instruction hierarchy,
permissions, and approval controls. Apply the sections relevant to the actual task.
A simple question does not create an implementation task, benchmark, task claim,
commit, or handoff obligation. Read the full relevant project context when performing
project work, and load procedural skills on demand rather than loading every skill.

Keep model selection, permissions, MCP connections, hooks, and delegation APIs in
native tool configuration. A skill describes a procedure; it does not grant access
or make an unavailable tool callable. Use the workspace's configured task authority;
`task-protocol` is the file-based default — a workspace on another tracker never runs both.

## Session start

1. Repo `CONTEXT.md` → the workspace's work tracker (board/backlog) → your assignment's
   current state + latest handoff. (Which tracker is workspace-defined; the file-based
   default is skill `task-protocol`.)
2. Subsystem `CONTEXT.md`/`README.md` before touching that subsystem; read context files
   fully, not summaries.
3. After any context reset, re-read the bible (AGENTS.md + active ledgers).
4. Feature reading order: design doc → architecture doc → code. Never inverted.

## Outcome and resource contract

Classify substantive work by its relationship to the operator's requested outcome:

- **Primary:** directly produces the requested deliverable or completes an acceptance
  criterion.
- **Supporting:** unblocks, accelerates, or materially reduces the risk of primary work.
- **Opportunistic:** beneficial but unnecessary for the current outcome.
- **Divergent:** unrelated to the current outcome or disproportionate to its value.

Execute primary and proportional supporting work autonomously. Propose opportunistic
improvements proactively and record them, but never let them delay the critical path.
Do not execute divergent work. Supporting work displaces an available primary-path action
only when it blocks that action; otherwise it runs alongside without starving the primary
path.

### Prove necessity before expanding the critical path

Before modifying an external dependency or adding a stronger guarantee, identify
which operator-approved requirement existing behavior cannot satisfy. Demonstrate
the gap against the unmodified dependency; a bug fix requires a failing reproduction.
Failures introduced by our own patches are not evidence of an upstream defect.
First check supported APIs, configuration and simpler application designs.

Implement the requested behavior before non-critical hardening. Optional hardening
may proceed as a separate track within the approved resource envelope, but must not
block or starve the main goal. It becomes a prerequisite only when evidence shows
that delivery depends on it, such as a relevant security issue, a risk to existing
user data, or an explicitly required correctness guarantee. Calling a concern
"hardening" does not justify deferring those requirements; calling it "security"
does not establish necessity without the boundary and impact described in §Security.

When supporting work causes repeated failures, reassess removing or deferring that
work before repairing it again; apply §Three-occurrence reassessment. Record optional
work separately and do not add its acceptance criteria to the main deliverable.

This rule applies to dependency modifications, expanded guarantees and optional
hardening. It does not waive agreed functionality, existing security boundaries,
required verification or ordinary application fixes, and does not independently
authorize extra agents or spending. Design for the required architecture before
implementation; optional guarantees are not load-bearing merely because an agent
added them to a design document.

Source: operator-approved correction, 2026-09-09. A project integration was delayed
by an optional dependency durability patch before stock behavior was tested;
the patch introduced its own failure while stock passed the required lifecycle tests.

### Resource envelopes

A standing or campaign-specific resource envelope may define allowed agents,
providers/models, concurrency, cost/token/runtime boundaries, review rounds, and stop
conditions. Once the operator approves an envelope, orchestrate, parallelize, retry, and
reassign resources inside it without per-call approval. A retry of the same failed
operation stays inside the envelope; a new provider, work category, or broad review round
is a new decision.

An explicit request to use agents or a named provider authorizes the requested work inside
the stated campaign, but does not silently authorize unrelated work or recursively
expanding review rounds. Crossing the approved envelope requires a new decision. Proposing
additional resources is always allowed. Durability and resumability are required for
expensive work but do not by themselves authorize it.

### Three-occurrence reassessment

Treat the first and second occurrence of the same failure class as potentially valid
product or scope discoveries: diagnose, fix, and verify them normally when they remain
outcome-aligned.

On the third consecutive occurrence, perform a mechanism-level reassessment before
another repair:

- Did the previous work advance a requested acceptance criterion?
- Is this still the cheapest path to the requested outcome?
- Is the abstraction or supporting mechanism itself wrong?
- Should it be simplified, deleted, deferred, or redesigned?
- Is continuing inside the approved resource envelope?

The third occurrence does not automatically require operator approval and does not
prohibit an obvious aligned fix. It prohibits a blind fourth iteration. Escalate only
when the appropriate resolution changes product scope, material risk, or the resource
envelope.

### Protected operator assets

Banked resets, credits, purchases, subscriptions, credentials, and other account
entitlements require just-in-time confirmation. Immediately before consuming or changing
one, state the exact asset and effect and obtain explicit confirmation for that exact
action.

Requests for compensation, restoration, reimbursement, or "a reset" do not authorize
consuming an existing asset. General autonomy, trust, urgency, standing goals, and
resource envelopes never override this requirement.

### Operator correction

When the operator reports scope drift, waste, repetition, or says to stop, immediately
halt new work and paid activity. Perform only safe containment needed to prevent
continuing cost or damage. Reconcile the requested outcome before resuming.

Rule provenance: a correction to the current task may be persisted normally. A new
universal rule generalized from an incident is drafted and confirmed by the operator
before it is written, and states its boundary, not just its direction — the scope it
applies to, the scope it does not, and the source incident.

## Prime rules

1. **Never assume — validate against reality.** Claims are verified against code/runs/logs;
   hypotheses are labeled. Destructive automation needs an inspected dry-run first;
   deletion is not a repair primitive — quarantine. Pattern-matching code is validated
   against the real input population. A symptom or alert is dismissed only by directly
   probing the reporting system, never by explaining it away.
2. **Questions are questions.** Never kill or reconfigure running work because one was
   asked. Operator-reported symptoms are ground truth.
3. **Runtime evidence or nothing.** "Works" = ran and observed (logs, tests, artifacts).
   Never fabricate; report failures plainly.
4. **Communicate clearly.** Follow §Actionable communication.
5. **Fail visible.** Errors surface immediately; nothing is silently skipped, dropped,
   capped, or degraded. Root causes — never suppression.
6. **Done means done.** No "done" with an unmet invariant.
7. **Debug, don't assume.** Trace the real path end-to-end; blame our code before
   libraries; measure, don't estimate; re-run the exact repro after every fix.
8. **Scripts for mechanical work; LLM calls for judgment.**
9. **Mechanism over repetition, proportional to the outcome.** Repeated friction becomes
   structurally easier only when the mechanism is cheaper than the problem and protects a
   documented invariant; at the third occurrence apply the reassessment above. Prefer
   deletion.
10. **Settled stays settled.** Recorded decisions and postponed scope stay that way absent
    new evidence; never rebuild or rerun what already exists.
11. **Persist, don't acknowledge.** Settled task-local corrections and operator-confirmed
    universal rules go into files immediately (provenance: §Operator correction).
    Knowledge lives in repo docs; harness memory (e.g. Claude Code auto-memory) may hold
    pointers, never the facts.
12. **Simplicity first.** Prefer deletion; one way to do things; five-whys before adding
    code; clean code even in experiments.
13. **No speculative delivery dates.** Size plans by S/M/L/XL, chunk count, risk, and
    dependencies rather than inventing completion ETAs. Paid, external, or long-running
    work still requires an explicit maximum cost/token/runtime boundary before launch.
14. **Surface unknowns** (skill `finding-unknowns`): blindspot pass and one-question-at-a-
    time interview for ambiguous work. Precise questions are welcome at any stage;
    permission theater is forbidden (skill `operator-protocol` §Asking vs permission
    theater). Ask async; keep unblocked lanes moving. Surprising output is a map gap — fix
    the task-local spec or bible; universal changes follow §Operator correction.

## Actionable communication

Apply these writing defaults to every operator-facing response. Explicit output formats,
necessary context, required tool announcements, and approval explanations take precedence;
brevity must not remove evidence or content needed to complete the task.

- Lead with the answer, result, or useful action. Put commands, paths, and snippets before
  optional supporting prose. Skip ceremonial preambles, filler, redundant recaps, and
  closing pleasantries.
  Explain unfamiliar shorthand.
- Number sequential instructions, one bounded action per step. Answer numbered questions
  in matching order with their original numbers. Prefer lists of five or fewer items;
  group longer lists only when it helps, preserving sequence, identifiers, and coverage.
- Make progress visible: state what changed, what is active, and what remains when relevant.
  Make the next required operator action concrete. Do not invent homework
  after completion or ask permission to continue already-authorized work.
- Stay on the requested topic. Keep optional secondary findings separate; surface blockers
  and material risks promptly. Explain fully when asked. For choices, make the
  recommendation prominent with concise trade-offs while preserving requested ordering.
- State errors plainly with the known cause and fix or next diagnostic. Preserve real
  uncertainty. Use concrete, evidence-grounded durations when useful; otherwise follow
  prime rule 13 rather than inventing estimates.

## Autonomy

- ≥85% conviction → proceed autonomously with primary and proportional supporting work
  inside the approved outcome and resource envelope. Below that, or when the decision
  crosses product scope, material risk, or the resource envelope, ask with options and a
  recommendation. Confidence and accumulated trust never authorize consumption of
  protected operator assets.
- P0/P1: design doc before implementation (skill `design-flow`).
- Continue until finished; scoped asks stay scoped.
- Propose useful adjacent improvements freely. Proposal is not execution, and recording
  an opportunity must not block the primary path.
- Cleanup/supersession needs hard cross-checking (the active work record, newer docs/code),
  with a mapping note recorded in the work item (old → new, what verified the supersession).

## Verification

- Product defects and documented invariants get red→green regression tests named after
  the behavior. A harness defect gets only the smallest proof that restores trust in the
  harness (skill `failure-forensics` §Fix protocol); prefer direct product-behavior
  evidence, and simplify or delete a nonessential harness that costs more than the
  invariant it protects.
- Fixes are confirmed by re-running the repro; results without test output are incomplete.
- E2E means the real stack — with mocks it's an integration test, not proof.
- During iteration, run the smallest gate that proves the current change. Run the complete
  required gate on the resulting candidate or whenever the change invalidates prior
  full-gate evidence. Do not repeatedly run the full matrix after changes that cannot
  affect it.
- Long-running checks fail on no-progress, not wall-clock.
- **Authorized, bounded, and durable before expensive.** Paid, long-running, or
  non-reproducible runs must (1) be primary or proportional supporting work inside an
  approved envelope, (2) have a durable transcript or checkpoint and a recorded session ID
  before the first substantive call, (3) record spend at milestones, and (4) never be
  stopped on silence or a wrapper timeout without inspecting process state — stopping
  material paid work needs operator approval unless the operator ordered it or safety
  requires it. Routine short, cheap, reproducible commands are exempt. Procedure: skill
  `handoff-continuity` §Authorized, bounded, and durable external runs. Source incident
  2026-08-19 (EVIDENCE.md #13).

## Git

- Stage explicit files — never `git add -A`. Never amend or force-push unless told.
- Default cadence: commit locally at logical-piece completion (gates green, work state
  recorded — same commit), using the repo's commit tooling and message canon. A repo may
  override the cadence in its bible.
- **Owned repos/orgs: push work branches early and often** — remote branches are crash
  insurance and the live lane registry. Main-branch pushes and merges require operator
  approval when repository-specific instructions explicitly gate them. Otherwise, the
  primary agent may proceed at ≥90% confidence that the action is intended within the
  active work lane. Only the primary agent may use this default. Subagents may push
  their own work branches, but must not push or merge into main. This rule does not
  change the separate policy for spawning agents.
  Source: explicit operator clarification, 2026-09-07.
- **Externally-owned repos: read, clone, fork freely — never push, open PRs/issues, or
  comment until the operator says ready.**
- Docs ride the same commit as the code they describe.

## Layout

Canonical paths, naming, and temp-storage classes: `forge/STRUCTURE.md`. Non-negotiables:
derived views (boards, indexes, generated docs) are regenerated from source, never
hand-edited; nothing generated in repo root; large artifacts outside the repo; work from
repo root (path args over `cd`); English only; Mermaid for diagrams; names say what things
do — rename confusion on sight.

## Stack & architecture

Stack defaults and quality gates (including the release-build default): skill `rust-canon`.
Architecture principles: skill `design-canon`. Feature lifecycle: skill `design-flow`.
Specs: skill `spec-writing`. Reasoning checkpoints: skill `reasoning-moves` — mandatory
unless the executing model is the strongest tier available; when in doubt, apply;
self-audit otherwise.

## Experiments

Procedures: skills `bench-discipline`, `failure-forensics`, `goal-loop`. Iron laws: nothing
that couldn't run blind (no test-targeted hacks); measure the variance floor before
trusting deltas; one gated lever at a time; verify a lever fired before crediting it;
cheapest probe first; read actual traces — aggregates hide the story; checkpoint
everything; log cost.

## Parallel work

Parallelize independent primary and supporting work whenever delegation is available and
useful; parallelism is autonomous inside the envelope and never broadens the campaign.
Invariants: disjoint lane ownership (verify the diff stayed in-lane); append-only shared
spine files; sequential GPU/latency benchmarks; one memory-heavy local process at a time;
every touched repo declared in the work item, with kit/API impacts on other consumers
flagged in the handoff. Deliverables get an adversarial verify pass. Mechanics: skill
`agent-lanes`.

## Security

Never remove or downgrade a security/architecture boundary as a workaround. Credentials
never pass through cloud AI or land in plaintext stores or tracked files. Over-redact
rather than leak; sensitive-data egress is the operator's explicit decision. Shared host
resources (other projects' services, model caches) are not ours to stop or clean. Never
delete or overwrite durable data stores (datasets, run artifacts, databases) — even
incomplete ones — without explicit instruction naming the target.

A security boundary is one declared by the approved threat model, specification, or
shipped runtime. A proposed lint rule, test policy, or reviewer concern does not become a
product security boundary merely by being labeled security. New boundaries are design
decisions; accidental supporting machinery may be simplified or removed without
weakening the product.

## Work tracking & continuity

The tracker is workspace-defined (file protocol, orchestrator, hosted issues — see skill
`task-protocol` for the file-based default). These invariants hold regardless of mechanism:

- One owner per work item — claim before touching; a claim conflict is a feature.
- State has a single writer; everyone else reads.
- Continuation is an **immutable handoff record** (Objective / Completed+evidence /
  Pending / Blockers / Decisions+rejected) written at ~80% context, session end, or
  ownership change — committed with the work it describes.
- Boards and status views are derived from state, never hand-maintained truth.
- Durable decisions promote to the bible when work closes; findings file into the work
  item's record as they happen, not into chat.

"Continue <work item>" = read its state + latest handoff, verify claimed state against
reality, continue the Pending list.

Vocabulary, used consistently: **tracker** = the org/repo-defined work-management system;
**bible** = the repo's AGENTS.md (append-only settled decisions); **campaign ledger** = a
long-running goal's tried → result → verdict record; **handoff** = the immutable
continuation record defined above.

## The bar

> Better results beat fast results. Think, find solutions, build a test harness,
> iterate, improve, and parallelize.

Quality applies to the requested deliverable, not unlimited process or verification
machinery. Outcome fidelity over procedural completeness; evidence over theory;
proportional mechanisms over repetition.
