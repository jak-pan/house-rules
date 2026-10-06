# Git rules

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
- Keep spawning authority separate from delivery authority within the approved resource envelope.
- Read, clone, or fork externally owned repositories freely.
- For externally owned repositories, never push upstream, open pull requests/issues, or comment until the operator says ready.
- Agents push to our own fork only after local review rounds that apply the same rules
  as Warden. House Rules review and Warden stay fully aligned on rules. This does not
  authorize upstream pushes, PRs, issues or comments.
- Commit documentation with the code it describes.
