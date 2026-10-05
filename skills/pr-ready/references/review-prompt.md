# Review prompt template

Fill the angle-bracketed fields; delete lines that do not apply.

```text
Review <PR link or branch> in this checkout; diff `git diff <base>...HEAD`.
<First round: "Review the whole change." | Later round: "Previous review: <path>. Mark
each of its blocking items RESOLVED or NOT, then look for new issues in <new commit>.">
Scope: <modules/directories>. Spec: <document and sections>; read the module README.
Blocking review against the shared reviewer pack, focused on: <the invariants that matter for this
change, e.g. authorization on every path, crash/replay, bounded cost>.
Challenge the spec as well: report contradictions, infeasible or unmeasurable
requirements, undefined cases and evidently worse designs under Spec issues.
Output: VERDICT: APPROVE or REQUEST_CHANGES; Blocking (numbered: file:line, concrete
scenario, smallest fix); Spec issues (section, problem, proposed resolution, and whether
it needs an operator decision); Follow-ups; Non-blocking. Do not edit files. Under <N>
lines of explanation where possible; never omit findings to fit a length target.
```

## Fix prompt template

Prepend the worker pack (`scripts/worker-pack.py`) to this template.

```text
<PR>, branch <branch>, this checkout. Review: <path> — read fully. Fix every blocking item
with the reviewer's smallest fix and a regression test per scenario: <one line per item>.
Merge the default branch first if it moved (merge, no rebase).
Local gate: apply the worker pack and the repository's declared gates.
Commit once (<commit message conventions>). Do not push. Report per item and the gate
commands with counts. Apply the worker pack's choice and decision boundaries.
```
