# STRUCTURE — Canonical Paths & Naming (all repos)

One reference for where every artifact lives and what it's called. Lifecycle rules: skill
`design-flow`. Task mechanics: skill `task-protocol`.

```
repo/
├── AGENTS.md                      # the bible: repository rules, settled decisions, execution choices
├── CONTEXT.md                     # project purpose, acceptance, stack, overrides with reasons
├── CLAUDE.md                      # Claude Code instructions; preserve existing content; import
│                                  #   AGENTS.md only if /memory shows this version does not load it
├── .claude/rules/<name>.md        # optional, Claude-only: path-scoped rules (frontmatter paths:)
├── docs/
│   ├── SYSTEM-MAP.md              # ONE high-level system map (skill design-canon §Docs)
│   ├── design/                    # INTENT — approved future design
│   │   └── NNN-feature-name.md    #   NNN = owning task id; statuses: see below
│   ├── architecture/              # SHIPPED behavior
│   │   └── feature-name.md        #   no task number — durable name
│   ├── specs/                     # product/subsystem specs (where repo uses spec layout)
│   │   └── {subsystem}/{subsystem}-spec.md
│   └── reports/
│       └── YYYY-MM-DD-topic.md    # dated (audits, reviews, handovers; a multi-file set is a
│                                  #   YYYY-MM-DD-topic/ dir); immutable once released —
│                                  #   corrections go in a new dated report or a labeled erratum
├── prototypes/
│   ├── NNN-feature-name/
│   │   ├── lofi/                  # md + mermaid flows, single-file html sketches
│   │   └── hifi/                  # project UI stack (PREFERENCES.md default) + mock data
│   └── spikes/
│       └── YYYY-MM-DD-question/   # throwaway code answering ONE question
│           └── SPIKE.md           #   question / method / verdict / date — kill-or-promote
├── tasks/                         # file-tracker default (skill task-protocol); other trackers
│   │                              #   keep AGENTS.md §Work tracking invariants, not these files
│   ├── TASKS.md                   # GENERATED board — never hand-edit
│   └── NNN-slug/
│       ├── task.md                # single-writer canonical state (frontmatter)
│       ├── handoffs/YYYYMMDD-HHMMSS-<agent>-000001.md   # immutable; collision suffix
│       ├── PRE-FLIGHT.md          # multi-phase only; maintained, not appended
│       ├── PUSH-TO-<goal>.md      # campaign ledger: baseline, knob map, tried→result→verdict (campaigns only)
│       ├── implementation-notes.md # plan deviations, what + why, as they happen
│       └── PITCH.md               # closing pitch: demo first, then spec + notes (significant work only)
├── runs/                          # benchmark/eval artifacts (gitignored unless promoted)
│   └── {system}/{benchmark}/{limit}/{run_name}/  # neutral condition names, run-params.json
├── records/                       # curated promoted runs (same shape as runs/)
├── skills/<name>/SKILL.md         # repo-local skills; check before writing shell pipelines
├── scripts/                       # git-commit.sh, git-push.sh, ci guards, smoke gates
├── RUNBOOK.md                     # operational knowledge: run, recover, rotate — not architecture
├── .debug-session/                # gitignored: logs, screenshots, debug reports
└── .tmp/                          # gitignored: scratch, per-lane cargo targets
```

## Naming rules

| Thing | Rule | Example |
|---|---|---|
| Task dir | `NNN-kebab-slug` (monotonic per repo, at least three digits; continues past 999) | `042-rerank-stage2` |
| Design doc | `docs/design/NNN-kebab.md` — carries owning task id | `docs/design/042-rerank-stage2.md` |
| Architecture doc | `docs/architecture/kebab.md` — durable, no id | `docs/architecture/rerank-pipeline.md` |
| Report | `docs/reports/YYYY-MM-DD-topic.md` | `2026-07-06-knob-audit.md` |
| Branch (file-tracker default) | `task/NNN-slug/<agent>` — advertises the lane; not an exclusive lock | `task/042-rerank-stage2/agent` |
| Run name | neutral benchmark condition, never debugging history | `candidate-answer-thinking` |
| Spike | `prototypes/spikes/YYYY-MM-DD-question/` | `2026-07-06-fts-vs-vector-speed/` |
| Handoff | `YYYYMMDD-HHMMSS-<agent>-<sequence>.md` (legacy names still readable) | `20260706-214005-agent-000001.md` |
| Legacy handover | `HANDOVER-YYYY-MM-DD.md` at repo root — un-migrated repos only | `HANDOVER-2026-07-06.md` |
| Commit | `type(scope): description` | `feat(recall): stage2 rerank` |
| Crates | `<product>-<domain>` | `acme-intake` |

General: kebab-case for directories and slugs; UPPERCASE for fixed canonical file names
(`TASKS.md`, `SPIKE.md`, `PITCH.md`); English only; names say what things do (no
defaults in names; disambiguate lookalikes, `captured_at` ≠ `ingested_at` ≠
`observed_at`); rename confusing names the moment they're noticed.

## Temp storage — three classes, one rule

Work products never live in system `/tmp`: it's outside git, outside backups, outside the project's data
boundary, shared across projects, and the OS purges it (reboot + periodic cleanup) — which
silently violates "checkpoint everything". In-repo gitignored dirs keep artifacts
inspectable, deliberately prunable, and inside the project's backup boundary.

| Class | Where | Lifecycle |
|---|---|---|
| Evidence — screenshots, debug logs, run reports you will open | `.debug-session/` | retain per the project's retention policy (none recorded: AGENTS.md §Security); task closure alone does not authorize deletion |
| Machine scratch — build targets, caches, never opened by a human | `.tmp/` | remove only under AGENTS.md §Security ownership, reproducibility, and active-process checks |
| Tool-provided session scratchpads (agent-harness temp dirs) | wherever the tool puts them | ephemeral by definition — copy anything worth keeping into the repo before session end |

The two-dir split is a retention policy, not taxonomy — evidence and scratch have different
deletion rules, so they get different homes. Exception: a shared out-of-repo cache
(e.g. `~/.cache/<tool>`) is fine for rebuildable artifacts that are expensive to recreate
and safe to lose.

## Frontmatter statuses

- Task (`task.md`): `pending → active → review → done` (+ `blocked`)
- Design doc: `draft → approved → implemented | superseded` (implemented = shipped
  sections migrated to architecture/spec, doc shrinks to a pointer that keeps its
  `status:` frontmatter (keep the work item's `design:` field) or is deleted (clear `design:` in the same commit); superseded =
  replaced by a newer design)
- Spike: `open → promoted | killed` (in SPIKE.md verdict; review and cleanup: skill
  `design-flow` §Spikes)
