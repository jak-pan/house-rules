# Prompt collection

- [skills/](skills/): code-change rules.
- [util/](util/): role-specific pieces used by some roles.
- [shared rules](../rules/): canonical writing, Git and priority-label owners.
- [roles/](roles/): role instructions and includes; a role may include another role.
- [lenses/](lenses/): review focus instructions.

Include one whole file per line:

```text
@rule house-rules:prompts/skills/code-canon.md
```

Skill and utility files never include other files. Includes are repository-relative
whole files, recursively expanded without heading parsing or title stripping.
A missing file fails the build, including a shared owner omitted with `--session`.

From a pinned checkout, run `/usr/bin/python3 skills/pr-ready/scripts/prompt.py`
with a repository-relative file argument, or supply text on stdin. `--list` prints
the files used in depth-first include order, including the entry file when supplied
and repeated includes each time. Paths outside the repository, section references
and cycles fail with exit 2, one stderr line and no stdout.

## Loading paths

The default compile includes [writing rules](../rules/writing.md),
[Git rules](../rules/git.md) and [priority labels](../rules/priority-labels.md).
Warden uses this complete pack without reading a live House Rules checkout.
Warden reviewers use a read-only pull-request copy, contact only the model provider and run no builds or tests.
Continuous integration runs builds and tests. The Warden service posts reviews.

Use `--session` for normal lane sessions:

```sh
python3 -B skills/pr-ready/scripts/prompt.py --session prompts/roles/implementer.md
```

The session index loads the same shared owners plus [session writing rules](../rules/session-writing.md).
The compiler omits only the three declared shared-rule includes.
Role instructions, review lenses and role-specific utility fragments remain included.
The compiled header states the selected loading path.
`--list` reports only files expanded for that path.

Session rules come from the live checkout through the installed House Rules block.
Only the role prompt uses a named commit under the one-step assembly design.
This compiler still reads checkout files; it does not implement named-commit assembly.
The dispatcher supplies repository rules and the work item's Decisions and Pre-flight sections.
