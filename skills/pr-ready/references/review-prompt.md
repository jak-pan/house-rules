# Review prompt template

Fill the angle-bracketed fields; delete lines that do not apply.

```text
Review <PR link or branch> in this checkout; diff `git diff <base>...HEAD`.
<First round: "Review the whole change." | Later round: "Previous review: <path>. Mark
each of its blocking items RESOLVED or NOT, then look for new issues in <new commit>.">
Scope: <modules/directories>. Spec: <document and sections>; read the module README.
Blocking review against the shared reviewer pack, focused on: <the invariants that matter for this
change, e.g. authorization on every path, crash/replay, bounded cost>.
Under <N> lines of explanation where possible; never omit findings to fit a length target.
```

## Fix prompt template

Expand the [implementer role](../prompts/roles/implementer.md) with `scripts/prompt.py` before this template.

```text
<PR>, branch <branch>, this checkout. Review: <path> — read fully. Fix every blocking item
following the worker pack: <one line per item>.
Merge the default branch first if it moved (merge, no rebase).
Local gate: apply the worker pack and the repository's declared gates.
Commit message conventions: <conventions>. Delivery override: <task-specific override, if any>.
```
