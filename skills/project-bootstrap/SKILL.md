---
name: project-bootstrap
description: Establish a new project's purpose, stack, collaboration mode, and delivery policy using the overridable House Rules defaults. Use when bootstrapping a project or deliberately revisiting its foundation; skip routine work in an established project.
license: MIT
---

# Project bootstrap

## Inspect before asking

Read existing AGENTS.md, CONTEXT.md, manifests, deployment configuration, and the work
item. Read `PREFERENCES.md` in the installed House Rules root: its defaults apply without an
opt-in. Explicit user choices, repository instructions, and an existing coherent stack
override them. Preserve settled choices; do not bootstrap an established project again
for a routine feature or fix.

## Settle only important unknowns

Propose the smallest useful starting configuration and identify material assumptions.
Ask only questions that remain unanswered and affect outcome, operations, or authority:

- What should the project do, for whom, and what demonstrates the first useful result?
- Where must it run, and which data/privacy, offline, performance, and recovery needs
  affect that choice? Inspect known constraints before asking.
- Do requirements justify overriding a default or adding another language/component?
  Explain the concrete benefit and maintenance cost. Do not require a stack exception
  form or another approval when the user or project has already selected an alternative.
- Which collaboration mode applies under AGENTS.md §Autonomy? Reuse a recorded answer;
  otherwise ask once about autonomy versus consequential decision forks.
- Is the default Git task/branch/review workflow suitable, and what delivery authority
  is actually recorded? Confidence does not grant main-write permission.

Use concise batches, or one question when its answer determines the next choice.
Continue independent preparation while answers are pending; silence is not approval.
Do not add hypothetical infrastructure questions to a small script or analysis.

## Record and proceed

Choose only needed components from PREFERENCES.md. Reuse pinned project tooling and
prefer one language when sufficient. Record purpose, acceptance, deployment/data needs,
selected stack, and consequential overrides with reasons in CONTEXT.md. Put concise
execution choices in the bible (repository AGENTS.md): collaboration mode, Git task authority, delivery
permissions, and verified build/test commands. Reference global House Rules instead of copying
its base. Record unresolved decisions in the existing Git task.

For example, an existing Python analysis repository keeps Python; a small web project
can use TypeScript on Node plus static Svelte without adding Rust; a Rust CLI need not
add Node merely to run scripts. Each uses the same Git task default unless overridden.

Implement the authorized bootstrap scope. Stack defaults do not authorize migrations,
paid services, publication, or unrelated components. Load experiment-planning only for
an actual study.
