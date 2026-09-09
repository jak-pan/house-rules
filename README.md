# forge

A skill bundle that standardizes how AI coding agents work across all your repos —
operating discipline, benchmark methodology, multi-agent work tracking, audit-report
authoring, and a feature lifecycle — as plain files: one universal `AGENTS.md`, 14 skills,
and a tiny zsh CLI.

Named after its own core directive: **"Forge Over Hack — when the same class of
friction recurs a third time, reassess the mechanism: simplify, delete, or add the
smallest proportional rule."** This repo is that directive applied to agent collaboration
itself.

Built by mining ~3,500 real operator messages from six production repos' agent-session
transcripts (both polarities: corrections that show what to prevent, and praise that shows
what to reproduce), merged with the repos' existing canon files and the model's own
engineering judgment (rules marked ⚒). Method and receipts: [EVIDENCE.md](EVIDENCE.md).

## Layout

| File | Role |
|---|---|
| `AGENTS.md` | **Universal agent canon** — the single rules source; drop into any repo (copy), repo-local rules win on conflict |
| `STRUCTURE.md` | Canonical paths & naming for every artifact (docs, prototypes, spikes, runs, branches, tasks) |
| `skills/operator-protocol` | Working with the operator: default actionable communication, steering vocabulary, question≠instruction, status, autonomy, earning trust |
| `skills/bench-discipline` | Benchmark/experiment methodology: no hacks, variance floors, knob-fired proof, cost ladder |
| `skills/failure-forensics` | Per-item root-cause procedure: diff-first regressions, evidence chains, fix protocol |
| `skills/goal-loop` | Goal-locked autonomous iteration toward numeric targets with ledger, checkpoints, honest ceilings |
| `skills/agent-lanes` | Parallel agent orchestration: lane ownership, worktrees, resource budgets, cross-repo rules |
| `skills/rust-canon` | Stack defaults: Rust workspace rules, quality gates, config layering, model-stack policy, secrets |
| `skills/design-canon` | Architecture principles: raw-canonical data, black-box boundaries, end-state-first, naming |
| `skills/design-flow` | Feature lifecycle: spec/design → lofi/hifi prototype → spike → implement → closeout with doc migration |
| `skills/finding-unknowns` | Unknowns-first working (after Thariq Shihipar's field guide): blindspot pass, reverse interview, prototype variants, pre-merge quiz |
| `skills/reasoning-moves` | **The scaffold pack** — frontier-native reasoning moves as explicit checkpoints for capable-but-not-frontier models (for any model below the strongest available tier): ground/gate/verify/report/learn |
| `skills/spec-writing` | Specs that pass the "buildable by a mid-level engineer without questions" bar: shape, worked examples, decisions+rejected, naming, reality-sweep first |
| `skills/audit-report-authoring` | Evidence-based audit and diligence report sets: claim labels, specialist/master authority, canonical questions, report-local citations, domain lenses and structural lint |
| `skills/task-protocol` | Multi-agent task management: single-writer task files, immutable handoffs, generated board |
| `skills/handoff-continuity` | Handoffs, task ledgers, bible maintenance, filing rules |
| `bin/task` | zsh CLI for the task protocol (`new/claim/status/done/handoff/index/board`) — `done` is the closeout gate |
| `CUSTOM-INDEX.example.md` | Template for the gitignored per-machine catalog of optional Skills, plugins, MCP clients, and other capabilities |
| `EVIDENCE.md` | Provenance: mining method, golden quotes, positive patterns, the 13 failure modes this bundle prevents |

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

Adopting the universal canon in a repo — **copy, never symlink** (the repo's AGENTS.md
is its append-only bible of settled decisions; a symlink would leak appends into the
shared file):

```bash
cp <path-to-forge>/AGENTS.md AGENTS.md   # then append repo-specific sections over time
printf '@AGENTS.md\n' > CLAUDE.md          # Claude Code reads only CLAUDE.md; this imports the canon
```

Division of law: `CONTEXT.md` holds repo rules; `AGENTS.md` holds the copied universal
canon plus the repo's appended settled decisions (the bible). Both override the universal
sections on conflict.

For existing repos with a rich `AGENTS.md`: paste the universal canon above the repo's own
sections, then delete local rules that merely duplicate it — keep only repo-specific law
(paths, crate maps, high-risk zones, stream tables). The universal sections lose on
conflict by design, so adoption is safe to do incrementally.

## Maintenance

- **Each rule has one home.** `AGENTS.md` states an invariant in one line; the owning skill
  holds the procedure; every other file references it as skill `name` §Section and never
  restates it. A restatement is a bug: delete it.
- The third occurrence of the same friction class triggers a mechanism review.
  Add standing law or a procedural Skill only when it is the smallest
  proportional fix, and record the evidence in EVIDENCE.md.
- **Rules distilled from one incident must state their boundary, not just their direction.**
  A contextual correction compressed into an absolute produces a wrong rule that survives
  until it bites. Every rule born from a single correction records: the scope it applies
  to, the scope it explicitly does NOT apply to, and the incident it came from. If the
  boundary is unknown, ask before generalizing.
- Settled decisions that agents keep re-litigating → append to the repo's AGENTS.md bible,
  and to the relevant skill if they're stack-wide.
- Audit the skills after major model upgrades — stronger models need less scaffolding;
  delete rules that have become noise.
- Re-mine transcripts occasionally: jq over the agent-session JSONL files, keep only
  operator-typed messages, truncate pasted blobs, fan out analysis agents per chunk, then
  distill both the corrections and the praise.
