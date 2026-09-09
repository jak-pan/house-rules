# forge

A skill bundle that standardizes how AI coding agents work across all your repos —
operating discipline, benchmark methodology, multi-agent work tracking, audit-report
authoring, and a feature lifecycle — as plain files: global base instructions, focused skills,
and a small Git-backed task CLI.

Named after its own core directive: **"Forge Over Hack — when the same class of
friction recurs a third time, reassess the mechanism: simplify, delete, or add the
smallest proportional rule."** This repo is that directive applied to agent collaboration
itself.

Forge provides opinionated defaults that apply immediately and remain overridable.
Explicit user choices, repository rules, and an existing coherent stack take precedence.
Skills supply procedures only when their scope applies.

## Layout

| File | Role |
|---|---|
| `AGENTS.md` | **Universal agent canon** — global base rules, including everyday actionable writing; repository-local instructions override shared preferences |
| `PREFERENCES.md` | Default stack and architecture choices, with explicit project/user overrides |
| `STRUCTURE.md` | Canonical paths & naming for every artifact (docs, prototypes, spikes, runs, branches, tasks) |
| `skills/operator-protocol` | Working with the operator: steering vocabulary, question≠instruction, status, autonomy, earning trust |
| `skills/project-bootstrap` | Apply defaults, inspect constraints, and ask only unsettled consequential project questions |
| `skills/experiment-planning` | Evidence-first experiment questionnaire; records only unsettled consequential choices |
| `skills/bench-discipline` | Controlled comparisons, appropriate uncertainty, proof that changes took effect, and bounded cost |
| `skills/failure-forensics` | Per-item root-cause procedure: evidence-led diagnosis, environmental checks, multiple causes and confirmation |
| `skills/goal-loop` | Goal-locked autonomous iteration toward numeric targets with ledger, checkpoints, honest ceilings |
| `skills/agent-lanes` | Parallel agent orchestration: lane ownership, worktrees, resource budgets, cross-repo rules |
| `skills/rust-canon` | Rust implementation defaults, workspace rules, quality gates, and configuration |
| `skills/design-canon` | Architecture principles: raw-canonical data, black-box boundaries, end-state-first, naming |
| `skills/design-flow` | Feature lifecycle: spec/design → lofi/hifi prototype → spike → implement → closeout with doc migration |
| `skills/finding-unknowns` | Unknowns-first working (after Thariq Shihipar's field guide): blindspot pass, reverse interview, prototype variants, pre-merge quiz |
| `skills/reasoning-moves` | Proportional checkpoints for assumptions, causal claims, verification and reporting |
| `skills/spec-writing` | Specs that pass the "buildable by a mid-level engineer without questions" bar: shape, worked examples, decisions+rejected, naming, reality-sweep first |
| `skills/audit-report-authoring` | Evidence-based audit and diligence report sets: claim labels, specialist/master authority, canonical questions, report-local citations, domain lenses and structural lint |
| `skills/task-protocol` | Multi-agent task management: single-writer task files, immutable handoffs, generated board |
| `skills/handoff-continuity` | Handoffs, task ledgers, bible maintenance, filing rules |
| `bin/task` | zsh CLI for the task protocol — ownership, release, handoff, closeout, and derived board |
| `CUSTOM-INDEX.example.md` | Template for the gitignored per-machine catalog of optional Skills, plugins, MCP clients, and other capabilities |
| `NOTICE.md` | Public attribution for adapted material |
| `scripts/export-public.mjs` | Build a file-only release from the explicit public file list; excludes local history and configuration |

## Install

Read [INSTALL-AGENTS.md](INSTALL-AGENTS.md) and give its destination prompt to
the agent on the computer being configured. The guide is authoritative; Forge
does not ship a universal installer script because agent discovery paths and
native filesystem capabilities differ by product and platform.

Global instruction adapters live in the tool-native files:

| Tool | Global adapter | Global settings |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | `~/.claude/settings.json` |
| Codex | `~/.codex/AGENTS.md` | `~/.codex/config.toml` |
| Kimi Code | `$KIMI_CODE_HOME/AGENTS.md` (default `~/.kimi-code/AGENTS.md`) | `$KIMI_CODE_HOME/config.toml` |

Codex and Kimi share portable user Skills through `~/.agents/skills/`; Claude
Code receives the same Forge-owned Skills through its native user directory.
The installing agent chooses verified symlinks or checked copies, preserves
operator instructions, and reports actual runtime discovery.

Model choice, permissions, plugins, hooks, and Model Context Protocol (MCP)
connections stay in each tool's native configuration. Sharing a skill makes
its instructions available; it does not install or authorize its tools.

Machine-specific and externally owned capabilities are recorded in the
gitignored `custom/INDEX.md`, created from `CUSTOM-INDEX.example.md`. A product
such as a self-installing tool installs and updates its own Skill, client, MCP
registration, and credentials; Forge records only the ownership and canonical
location. Never vendor an external product's Skill into Forge or copy one
agent's enrollment identity to another.

Forge is installed globally. Do not copy its universal instructions into every
repository. Each native global instruction file has one small managed pointer to the
permanent Forge source, loaded at session start. Repository `AGENTS.md` and `CONTEXT.md`
contain project-specific choices only.

Preserve existing global instructions in place by default. When the operator requests
consolidation, the installing agent may copy or merge human-authored rules into a
machine-local `custom/external-rules/<tool>.md` and keep an explicit pointer to that file.
Keep third-party managed blocks in their owner's supported location. Show the exact merge,
retain a backup, and preserve tool-specific rules rather than flattening conflicts.
See the installation guide for ownership, receipt, update, and removal rules.

Git-backed `tasks/` is the default tracker. The optional zsh helper manages those same
files; using it does not require a hosted tracker, MCP server, or database.

For a new project, `project-bootstrap` uses [PREFERENCES.md](PREFERENCES.md) automatically.
The defaults favor Rust for durable native/systems applications, TypeScript on Node for
ordinary backends and scripts, and static Svelte frontends. Select only what the project
needs, preserve established stacks, and allow domain-specific choices such as Python
for analysis. A repository override can be as simple as “This project uses Python and
FastAPI; retain that stack.” No extra approval or opt-in profile is required.

## Checks

Run `node --test tests/task.test.mjs scripts/export-public.test.mjs skills/audit-report-authoring/scripts/lint-report-set.test.mjs`
and `zsh -n bin/task`. GitHub CI runs these checks and a public export on Linux and macOS.
CI does not establish native agent discovery; report that separately during installation.

## Preparing a public bundle

Use `node scripts/export-public.mjs <new-output-directory>` to copy only paths declared
in `PUBLIC-FILES.txt`. The destination must not exist. The export contains no Git history,
local task records, audit reports, or machine configuration. Inspect the generated manifest
and the exported files before publishing. This produces a reviewable distribution; it
does not publish it or certify its contents. Publishing this development repository's
history is a separate decision.

## Maintenance

- **Each rule has one home.** `AGENTS.md` states an invariant in one line; the owning skill
  holds the procedure; every other file references it as skill `name` §Section and never
  restates it. A restatement is a bug: delete it.
- The third occurrence of the same friction class triggers a mechanism review.
  Add standing law or a procedural Skill only when it is the smallest
  proportional fix, and record the evidence in the owning work item.
- **Rules distilled from one incident must state their boundary, not just their direction.**
  A contextual correction compressed into an absolute produces a wrong rule that survives
  until it bites. Every rule born from a single correction records: the scope it applies
  to, the scope it explicitly does NOT apply to, and the incident it came from. If the
  boundary is unknown, ask before generalizing.
- Settled decisions that agents keep re-litigating → append to the repo's AGENTS.md bible,
  and to the relevant skill if they're stack-wide.
- Audit the skills after major model upgrades — stronger models need less scaffolding;
  delete rules that have become noise.
- Keep public instructions free of private transcripts, machine-specific setup, and
  personal incident details. Preserve approved attribution separately in NOTICE.md.
