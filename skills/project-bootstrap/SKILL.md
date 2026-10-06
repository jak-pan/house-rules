---
name: project-bootstrap
description: Establish a new project's purpose, stack, collaboration mode, and delivery policy using the overridable House Rules defaults. Use when bootstrapping a project or deliberately revisiting its foundation; skip routine work in an established project. [HRD-skills-project-bootstrap-37d5]
license: MIT
---

# Project bootstrap

## Inspect before asking

Read the bible, CONTEXT.md, manifests, deployment configuration, and the work item, then
`PREFERENCES.md` in the installed House Rules root. Preserve settled choices; do not
bootstrap an established project again for a routine feature or fix.

## Settle only important unknowns

Propose the smallest useful starting configuration and identify material assumptions.
Ask only questions that remain unanswered and affect outcome, operations, or authority:

- What should the project do, for whom, and what demonstrates the first useful result?
- Where must it run, and which data/privacy, offline, performance, and recovery needs
  affect that choice? Inspect known constraints before asking.
- Do requirements justify overriding a default or adding another language/component
  (`PREFERENCES.md`)?
- Which collaboration mode applies (rules/core.md §Autonomy)?
- Is the default issue/branch/PR workflow suitable (skill `work-tracking`), does the
  repository have a Git host, and what delivery authority is actually recorded
  (rules/delivery.md §Git)?

Ask per skill `operator-protocol` §Decisions. Do not add hypothetical infrastructure
questions to a small script or analysis.

## Record and proceed

Choose components per `PREFERENCES.md`. Record purpose, acceptance, deployment/data needs,
selected stack, and consequential overrides with reasons in CONTEXT.md. Put concise
execution choices in the bible (repository .agents/rules.md): collaboration mode, tracker and
project board, delivery permissions, and verified build/test commands. Reference global
House Rules instead of copying its base. Record unresolved decisions in the existing work
item.

For example, an existing Python analysis repository keeps Python; a small web project
can use TypeScript on Node plus static Svelte without adding Rust; a Rust CLI need not
add Node merely to run scripts. Each uses the same issue-tracking default unless overridden.

Implement the authorized bootstrap scope. Stack defaults do not authorize migrations,
paid services, publication, or unrelated components. Load experiment-planning only for
an actual study.

---

**House Rules debug round** (branch `debug/load-canaries`, never merged). This file's canary code is `HRC-skills-project-bootstrap-37d5`.
While this debug round runs, end every reply with one line that starts with `HR-LOADED:` and lists the canary codes (`HRC-…`) of every House Rules file whose text you have seen in this session, including text pasted into your prompt, and the `HRD-…` codes of skill descriptions you have seen. Write `HR-LOADED: none` if you have seen none.
