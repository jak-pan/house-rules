# Review prompt template

Fill the angle-bracketed fields; delete lines that do not apply.

```text
Review <PR link or branch> in this checkout; diff `git diff <base>...HEAD`.
<First round: "Review the whole change." | Later round: "Previous review: <path>. Mark
each of its blocking items RESOLVED or NOT, then look for new issues in <new commit>.">
Scope: <modules/directories>. Spec: <document and sections>; read the module README.
Blocking review against the shared reviewer pack, focused on: <the invariants that matter for this
change, e.g. authorization on every path, crash/replay, bounded cost>.
```

## Fix prompt template

Expand the [fixer role](../../../prompts/roles/fixer.md) with `scripts/prompt.py` before this template.

```text
<PR>, branch <branch>, this checkout. Accepted findings: <path> — read fully. Follow the fixer role
for scope and the worker pack for implementation: <one line per accepted item>.
Merge the default branch first if it moved (merge, no rebase).
Local gate: apply the worker pack and the repository's declared gates.
Commit message conventions: <conventions>. Delivery override: <task-specific override, if any>.
```
