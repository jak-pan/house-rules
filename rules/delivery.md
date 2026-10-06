# Delivery rules

## Verification

- Add behavior-named red-to-green regression tests for product defects and documented invariants.
- Prove harness repairs with only the smallest evidence that restores trust.
- Prefer direct product-behavior evidence.
- Simplify or delete nonessential harnesses that cost more than the invariants they protect.
- Re-run reproductions to confirm fixes.
- Include test output with results.
- Reserve end-to-end claims for the real stack.
- Classify mocked-stack tests as integration tests.
- During iteration, run the smallest gate that proves the current change.
- Run the complete required gate on the resulting candidate or whenever changes invalidate prior full-gate evidence.
- Where CI owns the full suite, use CI’s run on the pushed head.
- Do not repeat the full matrix after changes that cannot affect it.
- Let CI own the full suite.
- Follow `../prompts/roles/implementer.md` and `../prompts/roles/reviewer.md` for local scopes.
- Follow `pr-ready` §4 for the no-PR-CI exception.
- Fail long-running checks on lack of progress, rather than elapsed time.
- Allow generous overall test ceilings only as runaway guards.
- Never use overall ceilings as the primary failure mode.
- Define a standard CI time for each repository.
- Investigate runs more than 20% over that time.
- Allow an expected long run once, including a rebuilt dependency cache.
- Have Warden review CI runs.
- Send failing jobs to a CI-repair investigator.
- Require a specialized agent to verify UI work visually with screenshots.
- Do not rely only on programmatic assertions.
- Follow `../prompts/skills/test-discipline.md` §Test discipline for duration, hanging-test removal, build-queue hold limits, and scale-test replacement.
- Follow `../skills/pr-ready/references/guards.md` for guard/test upkeep and daily whole-system audits.
- Require an explicit maximum cost/token/runtime boundary before launching external or paid work.
- Apply this launch-boundary requirement only to external or paid work.
- Exempt routine short, cheap, reproducible commands from these expensive-work requirements.
- Keep paid, long-running, or non-reproducible external runs primary or proportionally supporting within approved envelopes.
- Examples include agents, model command-line interfaces, remote jobs, benchmarks, and crawls.
- Require a durable transcript or checkpoint before the first substantive call for those runs.
- Require a recorded session ID before that call.
- Record spend at milestones.
- Inspect process state before stopping runs because of silence or wrapper timeouts.
- Obtain operator approval before stopping materially paid work, except under rules/core.md §Operator correction or safety requirements.
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
- Never mix unrelated fixes, docs, refactors, or in-flight prototypes in one commit.
- Keep one topic per commit unless one larger task requires them together.
- Default to work branches, validation, and local commits in owned repositories or organizations.
- Push work branches within recorded repository/work-item delivery authority.
- Require explicit work-item or project authorization for main-branch pushes and merges.
- Accept standing project authorization.
- Do not ask again when it already authorizes the action.
- Never treat confidence alone as delivery authority.
- Never let subagents push or merge into main.
- Keep spawning authority separate from delivery authority under rules/outcome.md §Resource envelopes and §Parallel work in this file.
- Read, clone, or fork externally owned repositories freely.
- For externally owned repositories, never push upstream, open pull requests/issues, or comment until the operator says ready.
- Follow `upstream-contribution` §3 for our fork’s push exception and local review requirements.
- Commit documentation with the code it describes.

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

## Work tracking & continuity

- Apply these invariants with any tracker.
- Follow `work-tracking` for default mechanics.
- Assign one owner per work item.
- Claim work before touching it.
- Treat a claim conflict as a signal to stop and coordinate.
- Assign one writer for state.
- Allow everyone else only to read state.
- Continue through immutable handoff records.
- Follow `handoff-continuity` for contents, triggers, and resuming.
- Derive boards and status views from tracker items.
- Never maintain status files by hand.

**Track every deferred item.**

- Make a work item in the same turn when you defer a requested outcome, an accepted finding or a promise to the operator.
- Use an issue in the GitHub repository that owns the change.
- If no repository owns it, add one entry to the workspace tracker file. The entry holds one item and its status.
- Link the work item where you defer the work.
- Do not write "later", "I will file" or "a follow-up covers" without that link.
- Plans, documents, chat, reports, logs and unmerged branches record intent. They do not track work.
- When the operator repeats a request, search the tracker first. State whether the request was tracked.
- Ideas the operator did not request are proposals, not work items (rules/outcome.md §Outcome and resource contract).

- A requested outcome or accepted finding that the session does not finish becomes a work item in the repository that owns the change, before the session ends, linked from wherever it was set aside.
- That covers work that is deferred, "saved as a task", scoped out of another item, left as an audit gap, a plan or migration step, or said to "belong to the other repository's side".
- Accepted findings are findings the operator or a review accepted.

## Layout

- Use repository-relative paths in documentation and instructions.
- Derive script repository roots from script locations.
- Never use private paths in documentation or instructions.
- Follow the installed House Rules `STRUCTURE.md` for canonical paths, naming, and temp-storage classes.
- Default to regenerating derived views from source.
- Never hand-edit derived views.
- Keep generated files out of the repository's top-level directory.
- Default to keeping large artifacts untracked.
- Default to working from the repository root.
- Prefer path arguments over directory changes.
- Follow [rules/writing.md §Format](writing.md#format) for diagrams.
- Never change directories inside compound commands.
- Use `git -C` and absolute arguments.
- Re-anchor before relative-path writes.
- Verify no nested duplicate directories after bulk file creation.
- Always use absolute paths for file-tool reads, edits, writes, and searches.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-rules-delivery-2a9f`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
