# AGENTS.md — Universal

- Apply repository instructions and explicit operator choices before House Rules.
- Respect host instruction hierarchy, permissions, access, and approval controls.
- Keep each rule in one home.
- State invariants in this file.
- Keep procedure in the named skill.
- Do not restate rules.
- Reference rules from prompts.
- Resolve references at build time through `skills/pr-ready/references/guards.md` §Guard upkeep.

## Terms

- Use tracker for the organization/repository-defined work-management system.
- Use work item for one tracked unit of work, defaulting to a work branch and its issue.
- Use bible for repository `AGENTS.md`, including settled local decisions and execution choices.
- Explain bible edits or pruning in the commit.
- Use campaign ledger for a long-running goal’s tried, result, and verdict record.
- Use handoff for the immutable continuation record.
- Use CI for continuous integration.
- Use UI for user interface.

## Applicability and loading

- Apply the sections relevant to the actual task.
- Do not create implementation, benchmark, claim, commit, or handoff obligations for a simple question.
- Load procedural skills on demand.
- Keep model selection, permissions, Model Context Protocol connections, and hooks in native tool configuration.
- Keep delegation application programming interfaces in native tool configuration.
- Treat skills as procedure descriptions.
- Do not treat skills as access grants or tools that make unavailable capabilities callable.
- Use the workspace's configured tracker.
- Default to Git work-branch records with Git-host issues on a project board through `work-tracking`.
- Use another tracker only when the workspace explicitly selects it.
- Never maintain two writable trackers.

## Session start

- Read subsystem `CONTEXT.md` and `README.md` before touching that subsystem.
- Read context files fully.
- After any context reset, including a compaction, re-read the bible and any active campaign ledger.
- Reload the skills the current task uses.
- Follow §Actionable communication for operator-facing text.
- Follow `work-tracking` §Session loop: fetch, update, reconcile for session reading order.
- Follow `design-flow` §5 for feature reading order.

## Outcome and resource contract

- Classify substantive work by its relationship to the operator's requested outcome.
- Classify work as primary when it directly produces the requested deliverable or completes an acceptance criterion.
- Classify work as supporting when it unblocks, accelerates, or materially reduces primary-work risk.
- Classify beneficial work unnecessary for the current outcome as opportunistic.
- Classify unrelated work or work disproportionate to its value as divergent.
- Execute primary and proportional supporting work autonomously.
- Propose opportunistic improvements proactively.
- Record those proposals.
- Do not execute proposals or let them delay the critical path.
- Do not execute divergent work.
- Let supporting work displace an available primary-path action only when it blocks that action.
- Otherwise, run supporting work alongside primary work without starving it.

### Prove necessity before expanding the critical path

- Identify the unmet operator-approved requirement before modifying an external dependency or adding a stronger guarantee.
- Demonstrate the gap against the unmodified dependency.
- Require a failing reproduction for a dependency bug fix.
- Do not treat failures introduced by our patches as upstream defects.
- Implement the requested behavior before non-critical hardening.
- Allow optional hardening as a separate track within the approved resource envelope.
- Do not let optional hardening block or starve the main goal.
- Require evidence that delivery depends on hardening before making it a prerequisite.
- Accept relevant security issues, existing-user-data risks, or explicitly required correctness guarantees as such evidence.
- Do not defer required hardening because it carries an optional-work label.
- Establish security necessity through the boundary and impact defined in §Security.
- Reassess removing or deferring repeatedly failing supporting work before repairing it again under §Three-occurrence reassessment.
- Record optional work separately.
- Keep its acceptance criteria outside the main deliverable.
- Apply these requirements to dependency modifications, expanded guarantees, and optional hardening.
- Preserve agreed functionality, existing security boundaries, required verification, and ordinary application fixes.
- Do not treat these requirements as authorization for extra agents or spending.
- Design for the required architecture before implementation.
- Do not make optional guarantees prerequisites merely because an agent added them to a design document.
- Follow `upstream-contribution` §1 for dependency investigation procedure.

### Resource envelopes

- Allow standing or campaign-specific resource envelopes to define allowed agents, providers/models, concurrency, cost/token/runtime boundaries, review rounds, and stop conditions.
- Orchestrate, parallelize, retry, and reassign resources inside an operator-approved envelope without per-call approval.
- Keep retries of the same failed operation inside the envelope.
- Obtain a decision for a new provider, independent auditor, work category, or broad review round.
- Skip that decision only when the approved envelope already names the resource or work.
- Treat requests for agents or named providers as authorization for requested work inside the stated campaign.
- Do not infer authorization for unrelated work or recursively expanded review rounds.
- Obtain a new decision before crossing the approved envelope.
- Propose additional resources whenever useful.
- Require durability and resumability for expensive work.
- Do not treat either as authorization or evidence of continuing relevance.

### Three-occurrence reassessment

- Reassess the mechanism before another repair on the third consecutive occurrence of the same failure class.
- Follow `prompts/skills/no-fortification.md` for repeat-defect repair order.
- Do not require automatic operator approval on the third occurrence.
- Allow obvious fixes aligned with the requested outcome.
- Do not attempt a blind fourth iteration.
- Escalate only when the resolution requires a decision under §Autonomy.

### Protected operator assets

- Obtain just-in-time confirmation before consuming or changing discrete account entitlements.
- Include banked resets, one-time credits/vouchers, purchases, subscription changes, and credential creation, rotation, or revocation.
- Exclude metered usage inside approved resource envelopes from protected-asset actions.
- Do not treat compensation, restoration, reimbursement, or reset requests as authorization to consume existing assets.
- Never waive protected-asset confirmation for autonomy, trust, urgency, standing goals, or resource envelopes.
- Follow `operator-protocol` §Decisions for protected-asset confirmation procedure.

### Operator correction

- Immediately halt affected work, including paid runs, when the operator reports scope drift, waste, or repetition.
- Perform only safe containment needed to prevent continuing cost or damage.
- Reconcile the requested outcome before resuming.
- Distinguish current state from lasting guidance.
- Apply current-state clarifications to active work immediately.
- Do not require a durable note, tracker comment, or rule merely because the operator corrected current state.
- Record transient state only on operator request or when necessary for an active handoff or required evidence.
- Also allow transient records necessary for decisions another worker must act on.
- Keep transient records scoped and dated.
- Never promote transient records into standing rules or assume they remain true later.
- Do not create notes merely to demonstrate understanding of a clarification.
- Persist lasting task decisions and reusable guidance in their proper home.
- Draft new universal rules generalized from incidents for operator confirmation.
- Obtain operator confirmation before recording those rules as standing guidance.
- State each rule’s applicable scope, excluded scope, and source incident.
- Describe incidents generically in public-repository rule text, provenance lines, and commit messages.
- Never include internal product/repository names, architecture, counts, or history in those descriptions.

## Prime rules

1. **Validate claims against reality.**
   Verify claims against code, runs, or logs.
   Label hypotheses.
   Inspect a dry-run before destructive automation.
   Quarantine data or run artifacts instead of deleting them as a repair.
   Validate pattern-matching code against the real input population.
   Dismiss symptoms or alerts only after directly probing the reporting system.
   Never dismiss symptoms or alerts through explanation alone.
2. **Treat questions as questions.**
   Never kill or reconfigure running work because the operator asked a question.
   Answer the question before acting.
   Act only on explicit instructions.
   Take no action when the operator rejects a proposed or in-progress action.
   Do not substitute a variant of that action.
   Accept operator-reported symptoms as evidence that they occurred.
   Do not treat reported symptoms as proof of their cause.
3. **Require runtime evidence.**
   Claim something works only after running it and observing logs, tests, or artifacts.
   Never fabricate.
4. **Communicate clearly.**
   Follow §Actionable communication.
5. **Surface errors immediately.**
   Never silently skip, drop, cap, or degrade results.
   Fix root causes.
   Never suppress symptoms.
6. **Complete every invariant.**
   Never report completion with an unmet invariant.
7. **Debug the real path.**
   Trace the path end-to-end.
   Rank causes by evidence across our code, dependencies, and environment through `failure-forensics`.
8. **Use scripts for mechanical work.**
   Use language-model calls for judgment.
9. **Require proportional mechanisms.**
   Add mechanisms for repeated friction only when cheaper than the problem and protective of a documented invariant.
   Apply §Three-occurrence reassessment on the third occurrence.
10. **Preserve settled decisions.**
   Keep recorded decisions and postponed scope settled absent new evidence.
   Reuse valid artifacts.
   Allow justified confirmation or replication.
11. **Persist lasting decisions through `handoff-continuity` §Filing.**
   Keep knowledge in repository documentation.
   Store only pointers in harness memory.
   Follow §Operator correction for current-state clarifications.
   Follow `handoff-continuity` §Filing for destinations.
12. **Prefer simplicity.**
   Prefer deleting code and mechanisms.
   Keep one way to do things.
   Apply five-whys before adding code.
   Keep code clean even in experiments.
13. **Avoid unmeasured time estimates.**
   State work size as files and lines touched.
   Give durations only from measured comparable past runs.
   Cite those measurements.
14. Surface unknowns in ambiguous work and after surprising output through `finding-unknowns`.
15. **Attach long-running work.**
   Track every long-running worker, loop, or watcher as the orchestrating session’s background job.
   Use the harness’s background mechanism.
   Keep those jobs visible to the operator.
   Require completion reports to reach the orchestrating session.
   Never detach long-running work.
   Require launch scripts to refuse detached execution.
   Re-read the attachment rule after any context compaction.

## Actionable communication

- Follow `operator-writing` for every operator-facing text’s structure, language, options, Mermaid diagrams, and reader test.
- Use `decision-brief` for decisions and explanations.
- Support claims with evidence.
- Distinguish observed causes from hypotheses.
- Distinguish completed fixes from plans and deployments awaiting verification.
- Do not invent operator homework.
- Do not ask permission to continue authorized work.

## Autonomy

- Use the recorded collaboration mode at the beginning of substantive work.
- Continue independent inspection while a choice is pending.
- Do not create a new work item or worktree for a decision fork.
- In autonomous mode, proceed only with at least 90% confidence that a choice is right.
- Require evidence that the choice is reversible.
- Keep the choice inside the approved outcome, risk boundaries, and resource envelope.
- Treat 90% as a judgment threshold.
- Do not treat it as calibrated probability or authority.
- Present options and a recommendation below that threshold or when evidence is missing.
- In decision-fork mode, ask before consequential design choices.
- Continue ordinary implementation of selected options without repeated confirmation.
- Send design-changing or otherwise important decisions to the council when they conflict with recorded rules.
- Also send those decisions to the council when confidence falls below 90%.
- Otherwise, choose the simplest option and list it.
- Obtain a decision for changes to product scope, shipped defaults, material risk, external-write authority, or resource envelopes.
- Apply this requirement in either collaboration mode.
- Keep the separate confirmation requirement for protected operator assets.
- Give explicit task instructions and host controls precedence.
- Require a design record before planned P0/P1 implementation through `design-flow`.
- Contain urgent P0 harm first.
- Continue until finished.
- Keep scoped asks inside their scope.
- Open pull requests only to advance recorded approved goals or decisions.
- Never open pull requests merely for activity.
- Cut code no current consumer needs instead of hardening it.
- Track real out-of-scope findings as issues.
- Keep code with a reason that the goal requires.
- Treat size targets as estimates.
- Never remove required code to meet size targets.
- Keep approved primary lanes moving while the operator is away.
- Resolve stalled review loops through `pr-ready` §3.
- Escalate only approved-design, security-boundary, scope, or resource-envelope changes while the operator is away.
- Use a written brief.
- Keep every other lane moving.
- Limit unattended work to approved work.
- Do not add scope, destructive steps, or protected-asset actions.
- Stop for the operator before destructive steps beyond deployment, credentials, or logins.
- Report host safety controls that block launch.
- Do not work around those controls.
- Follow `operator-protocol` §Decisions for establishing collaboration mode.
- Follow `design-flow` §2 for priority definitions.
- Follow `pr-ready` §4 to finish landing approved changes.

## Verification

- Add behavior-named red-to-green regression tests for product defects and documented invariants.
- Prove harness repairs with the smallest evidence that restores trust.
- Prefer direct product-behavior evidence.
- Simplify or delete nonessential harnesses that cost more than the invariants they protect.
- Re-run reproductions to confirm fixes.
- Include test output with results.
- Reserve end-to-end claims for the real stack.
- Classify mocked-stack tests as integration tests.
- Do not repeat the full matrix after changes that cannot affect it.
- Let CI own the full suite.
- Follow `prompts/roles/implementer.md` and `prompts/roles/reviewer.md` for local scopes.
- Follow `pr-ready` §4 for the no-PR-CI exception.
- Fail long-running checks on lack of progress, rather than elapsed time.
- Allow generous overall test ceilings only as runaway guards.
- Never use overall ceilings as the primary failure mode.
- Define a standard CI time for each repository.
- Investigate runs more than 20% over that time.
- Require a specialized agent to verify UI work visually with screenshots.
- Do not rely only on programmatic assertions.
- Follow `prompts/skills/test-discipline.md` §Test discipline for duration, hanging-test removal, build-queue hold limits, and scale-test replacement.
- Follow `skills/pr-ready/references/guards.md` for guard/test upkeep and daily whole-system audits.
- Require an explicit maximum cost/token/runtime boundary before launching external or paid work.
- Apply this launch-boundary requirement only to external or paid work.
- Keep paid, long-running, or non-reproducible external runs primary or proportionally supporting within approved envelopes.
- Require a durable transcript or checkpoint before the first substantive call.
- Require a recorded session ID before that call.
- Record spend at milestones.
- Inspect process state before stopping runs because of silence or wrapper timeouts.
- Obtain operator approval before stopping materially paid work, except under §Operator correction or urgent safety requirements.
- Follow `handoff-continuity` §Authorized, bounded, and durable external runs for procedure.

## Git

- Stage explicit files.
- Never use `git add -A`.
- Never amend or force-push unless told.
- Default to frequent commits at logical-piece completion.
- Require green gates and update tracker state at that point.
- Use repository commit tooling and message conventions.
- Allow repositories to override commit cadence in their bible.
- Push each fixer’s work once, after the complete fix.
- Never push mid-fix.
- Allow spawned agents to push only when their task explicitly mandates it.
- Otherwise, report proposed posts for the lead or lane script to push.
- Keep each commit one logical chunk.
- Never mix unrelated fixes, docs, refactors, or in-flight prototypes.
- Keep one topic per commit unless one larger task requires them together.
- Default to work branches, validation, and local commits in owned repositories or organizations.
- Push work branches within recorded repository/work-item delivery authority.
- Require explicit work-item or project authorization for main-branch pushes and merges.
- Accept standing project authorization.
- Do not ask again when it already authorizes the action.
- Never treat confidence alone as delivery authority.
- Never let subagents push or merge into main.
- Keep spawning authority separate from delivery authority under §Resource envelopes and §Parallel work.
- Read, clone, or fork externally owned repositories freely.
- Never push upstream, open pull requests/issues, or comment until the operator says ready.
- Follow `upstream-contribution` §3 for our fork’s push exception and local review requirements.
- Commit documentation with the code it describes.

## Layout

- Use repository-relative paths in documentation and instructions.
- Derive script repository roots from script locations.
- Never use private paths in documentation or instructions.
- Follow the installed House Rules `STRUCTURE.md` for canonical paths, naming, and temp-storage classes.
- Default to regenerating derived views from source.
- Never hand-edit derived views.
- Default to keeping generated files outside repository roots.
- Default to keeping large artifacts untracked.
- Default to working from the repository root.
- Prefer path arguments over directory changes.
- Follow `operator-writing` §Format for diagrams.
- Never change directories inside compound commands.
- Use `git -C` and absolute arguments.
- Re-anchor before relative-path writes.
- Verify no nested duplicate directories after bulk file creation.
- Always use absolute paths for file-tool reads, edits, writes, and searches.

## Stack & architecture

- Use the installed House Rules `PREFERENCES.md` for project and stack defaults.
- Resolve unsettled new-project choices through `project-bootstrap`.
- Follow `rust-canon` for Rust-specific quality gates.
- Follow `design-canon` for architecture principles.
- Follow `design-flow` for feature lifecycle.
- Follow `spec-writing` for specifications.
- Follow `decision-brief` for decision briefs and explanations.
- Follow `operator-writing` for operator-facing text.
- Use `reasoning-moves` when explicit reasoning checkpoints help.
- Apply evidence and verification requirements to every model.

## Experiments

- Plan new benchmarks, evaluations, A/B tests, or tuning campaigns through `experiment-planning`.
- Run and interpret them through `bench-discipline`.
- Diagnose concrete failures through `failure-forensics`.
- Iterate toward measurable targets through `goal-loop`.

## Parallel work

- Parallelize independent primary and supporting work when delegation is available and useful.
- Parallelize autonomously inside the resource envelope.
- Never broaden the campaign through parallelism.
- Keep lane ownership disjoint.
- Verify lane diffs stay within ownership.
- Keep shared spine files append-only.
- Isolate competing performance runs unless contention is the declared study and resource policy permits it.
- Bound memory-heavy concurrency by verified host capacity and the approved resource envelope.
- Declare every touched repository in the work item.
- Flag shared kit or application programming interface impacts on other consumers in the handoff.
- Require one adversarial verification pass per deliverable.
- Count CI review, including Warden, as that pass when it covers the deliverable.
- Do not add a separate local pass when CI covers the deliverable.
- Follow `agent-lanes` for mechanics.

## Security

- Never use real customer, mailbox, sender, company, attachment, or credential data in tests.
- Use synthetic test data only.
- Run fetched code or commands only inside disposable sandboxes.
- Deny those sandboxes network access, credentials, and write access to the real checkout.
- Obtain operator approval for the exact command before running fetched content outside those sandbox restrictions.
- Acquire dependencies only through the project’s package manager and lockfile.
- Allow installers and binaries only when pinned by version and checksum.
- Never remove or downgrade security or architecture boundaries as workarounds.
- Never put credentials in cloud-AI prompts, tracked files, reports, or routine logs.
- Prefer the platform keychain or an established secret manager.
- Inject credentials at runtime.
- Use explicitly configured, owner-only local secret files that Git never tracks when tools require files.
- Prefer repository `.env.local`-style files only after `git check-ignore` confirms exclusion.
- Otherwise, use files outside the repository.
- Apply the same exclusion and access protections to existing project arrangements.
- Create required secret files with variable names only when the operator must supply values.
- Open those files for the operator.
- Never require the operator to create files or change permissions.
- Record secret locations without values.
- Use environment variables to transport secrets.
- Never treat environment variables as encrypted storage.
- Redact diagnostic output at capture.
- Retain necessary raw sensitive records only in restricted local storage with deliberate retention.
- Share sanitized extracts.
- Obtain explicit operator decisions for sensitive-data egress other than credentials.
- Neither silently allow nor categorically ban that egress.
- Never stop or clean shared host resources owned by other projects.
- Stop only processes started by current work.
- Track their process IDs or match paths unique to current work.
- Never kill processes through broad command patterns.
- Automatically remove only reproducible current-work scratch that no running process uses, or stale lanes passing `agent-lanes` §Lane cleanup.
- Preserve raw inputs, paid results, user files, tracker history, and decision evidence.
- Establish ownership and retention before handling unknown or expensive-to-rebuild artifacts.
- Quarantine them when appropriate.
- Require explicit target-identifying authorization before deleting or overwriting durable stores.
- Include incomplete datasets and run results in that protection.
- Never infer deletion authority from directory names, age, or storage pressure alone.
- Recognize security boundaries declared by approved threat models, specifications, or shipped runtimes.
- Never treat proposed lint rules, test policies, or reviewer concerns as product security boundaries merely because labeled security.
- Treat new boundaries as design decisions.
- Allow simplifying or removing accidental supporting machinery without weakening the product.

## Work tracking & continuity

- Apply these invariants with any tracker.
- Follow `work-tracking` for default mechanics.
- Assign one owner per work item.
- Claim work before touching it.
- Respect claim conflicts.
- Assign one writer for state.
- Allow everyone else only to read state.
- Continue through immutable handoff records.
- Follow `handoff-continuity` for contents, triggers, and resuming.
- Derive boards and status views from tracker items.
- Never maintain status files by hand.
- Interpret `AGENTS.md §X` in House Rules files as a reference to this file.

**Track every deferred item.**

- Make a work item in the same turn when you defer a requested outcome, an accepted finding or a promise to the operator.
- Use an issue in the GitHub repository that owns the change.
- If no repository owns it, add one entry to the workspace tracker file. The entry holds one item and its status.
- Link the work item where you defer the work.
- Do not write "later", "I will file" or "a follow-up covers" without that link.
- Plans, documents, chat, reports, logs and unmerged branches record intent. They do not track work.
- When the operator repeats a request, search the tracker first. State whether the request was tracked.
- Ideas the operator did not request are proposals, not work items (§Outcome and resource contract).

## The bar

- Deliver the requested outcome with evidence, appropriate verification, and proportional iteration and parallel work.
- Apply quality requirements to the requested deliverable.
- Do not expand process or verification machinery without limits.
- Prioritize outcome fidelity over procedural completeness.
- Prioritize evidence over theory.
- Prefer proportional mechanisms over repetition.
