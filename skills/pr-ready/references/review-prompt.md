# Review prompt template

Fill the angle-bracketed fields; delete lines that do not apply.

```text
Review <PR link or branch> in this checkout; diff `git diff <base>...HEAD`.
<First round: "Review the whole change." | Later round: "Previous review: <path>. Mark
each of its blocking items RESOLVED or NOT, then look for new issues in <new commit>.">
Scope: <modules/directories>. Spec: <document and sections>; read the module README.
Blocking review against the review bar (skill `pr-ready` §3: correctness, security,
performance, code quality, waste), focused on: <the invariants that matter for this
change, e.g. authorization on every path, crash/replay, bounded cost>.
Review statically; CI runs the full suite. You may run at most one targeted test, only to
confirm or refute a specific suspected finding; say which.
Challenge the spec as well: report contradictions, infeasible or unmeasurable
requirements, undefined cases and evidently worse designs under Spec issues.
Output: VERDICT: APPROVE or REQUEST_CHANGES; Blocking (numbered: file:line, concrete
scenario, smallest fix); Spec issues (section, problem, proposed resolution, and whether
it needs an operator decision); Follow-ups; Non-blocking. Do not edit files. Under <N>
lines.
```

## Fix prompt template

```text
<PR>, branch <branch>, this checkout. Review: <path> — read fully. Fix every blocking item
with the reviewer's smallest fix and a regression test per scenario: <one line per item>.
Merge the default branch first if it moved (merge, no rebase).
Local gate: skill `pr-ready` §1 (targeted tests only; CI runs the full suite).
Commit once (<commit message conventions>). Do not push. Report per item and the gate
commands with counts. If a fix needs a genuine design choice, stop and report options.
```
