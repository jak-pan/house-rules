# Prompt collection

- [skills/](skills/): code-change rules.
- [util/](util/): shared pieces used by some roles.
- [roles/](roles/): role instructions and includes; a role may include another role.
- [lenses/](lenses/): review focus instructions.

Include one whole file per line:

```text
@rule house-rules:prompts/skills/code-canon.md
```

Skill and utility files never include other files. Includes are repository-relative
whole files, recursively expanded without heading parsing or title stripping.
A missing file fails the build.

From a pinned checkout, run `/usr/bin/python3 skills/pr-ready/scripts/prompt.py`
with a repository-relative file argument, or supply text on stdin. `--list` prints
the files used in depth-first include order, including the entry file when supplied
and repeated includes each time. Paths outside the repository, section references
and cycles fail with exit 2, one stderr line and no stdout.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-prompts-readme-185e`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
