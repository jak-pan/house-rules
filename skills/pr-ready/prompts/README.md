# Prompt collection

- [common/](common/): rules every role receives.
- [utils/](utils/): shared pieces used by some roles.
- [roles/](roles/): role instructions and includes; a role may include another role.
- [lenses/](lenses/): review focus instructions.

Include one whole file per line:

```text
@rule house-rules:skills/pr-ready/prompts/common/code-canon.md
```

Common and utility files never include other files. Includes are repository-relative
whole files, recursively expanded without heading parsing or title stripping.
A missing file fails the build.

From a pinned checkout, run `/usr/bin/python3 skills/pr-ready/scripts/prompt.py`
with a repository-relative file argument, or supply text on stdin. `--list` prints
the files used in depth-first include order, including the entry file when supplied
and repeated includes each time. Paths outside the repository, section references
and cycles fail with exit 2, one stderr line and no stdout.
