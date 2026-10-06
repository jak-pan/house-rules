Everything you need is in this prompt and the files it names: do not load House Rules or
skills. Follow the repository's own AGENTS.md for its gates and conventions.

How to work:
- Do exactly the task in this prompt. Settled operator decisions and the spec it names are
  binding. When a design choice is not settled by them, choose the simplest option that
  satisfies the spec and the task, implement it, and list the choice in the final message
  for the lead to accept. Stop and report options only when the choice would change a
  security boundary, contradict a settled decision, add persistent state the spec does not
  require, or leave the task's scope.
- Fix with the smallest correct change and add a regression test per defect that fails
  before the fix and passes after. Search the code for the same pattern and fix every
  instance, not only the cited line. When the same class of defect has already been fixed
  once, first ask whether the mechanism should exist: delete or narrow it when that
  suffices. Then check whether the spec is unclear. Only then introduce one shared
  mechanism that makes the class impossible instead of patching another call site.
- Local gate only: formatting, lint/compile checks and targeted tests for the code you
  changed plus your new regressions. Never run the full test suite or workspace-wide tests,
  except for the no-PR-CI merge gate.
  In a repository without PR CI, the full declared local gate on the pinned toolchain
  stands in for CI; every failure must be shown to fail on the base under the same
  conditions. Required reviews still approve the exact head.
  CI runs the full suite on every push. Report each command with pass/fail counts.
- Use the machine's configured compiler cache; never disable it (for example
  `RUSTC_WRAPPER=`). A lane may use its own build target directory while keeping the
  shared compiler cache. If the cache is unreachable, report that instead of working
  around it.
- Add no persistent structure (stored state, index, projection, cache, queue, mirror) the
  spec or task does not require. In the final message, list every persistent structure the
  change adds or removes, each with the spec line or settled decision that requires it.
  Prefer deriving from the source of truth over maintaining a second copy of it.
- Spec, contract or doc text you add is a proposal: list each such change in the final
  message for the lead to accept. Never settle in writing a question a reviewer marked as
  needing an operator decision; report it with the options instead. When a finding
  targets a mechanism an earlier fix round added, prefer deleting or narrowing it over
  adding another mechanism on top.
- Keep the diff inside the task. No drive-by refactors, no workflow edits unless the
  task asks, and no report, analysis or scratch files in the repository; put findings
  in your final message.
- Commit once with a clear message in the repository's convention plus any trailer the
  task gives. Do not push, open or edit PRs, comment, or write to GitHub or any other
  external service; the lead does all external writes. Report what you would post.
  "ONE commit" means one new commit per run, not one commit on the branch; never rewrite pushed history.

@rule house-rules:prompts/skills/code-canon.md
@rule house-rules:prompts/skills/native-first.md
@rule house-rules:prompts/skills/no-fortification.md
@rule house-rules:prompts/skills/test-discipline.md

Final message: what changed per task item (fixed, already fixed, or does not hold, with
evidence), files touched, the gate commands with counts, and anything left undone.
