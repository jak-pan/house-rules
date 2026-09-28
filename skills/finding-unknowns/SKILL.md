---
name: finding-unknowns
description: Surface the operator's unknowns before, during, and after ambiguous work — blindspot pass, reverse interview, fake-data prototype variants, volatile-decisions-first plans, implementation notes, pre-merge quiz. Use at the start of any underspecified or design-heavy task, when writing specs/prompts for agents, when output surprises anyone, and before merging significant work.
license: MIT
---

# Finding Unknowns

The map is not the territory: the prompt/spec/skills are a *representation* of the work;
the codebase and real constraints are the territory. A capable model resolves ambiguity
confidently — which means bad assumptions no longer fail loudly, they propagate silently.
So the ceiling on output quality is how well the operator's unknowns get surfaced — and
that is partly YOUR job, not just theirs.

(After Thariq Shihipar's "A Field Guide to Fable: Finding Your Unknowns", x.com/trq212 —
adapted to the House Rules lifecycle.)

## The four quadrants → four moves

| Quadrant | What it is | Your move |
|---|---|---|
| Known knowns | what the prompt says | **Restate the plan** in your own words before executing — cheap map-vs-territory diff |
| Known unknowns | gaps the operator knows they haven't decided | **Reverse interview**: architecture-affecting questions first |
| Unknown knowns | things too obvious for the operator to write, but recognizable on sight | **Prototype variants** with fake data in deliberately different directions; **example-based spec** (the operator points at something admired → extract its structure) |
| Unknown unknowns | what nobody has considered | **Blindspot pass**: dedicated scan for traps, unasked questions, and missing constraints before work starts |

## Before implementation

1. **Blindspot pass** (P0/P1 kickoff, right after claiming the work item): scan the territory —
   codebase, adjacent docs, prior tasks — and report the unknown unknowns: traps, implicit
   constraints, questions the spec should have asked. This is a *report*, not twenty
   questions.
2. **Reverse interview** for the known unknowns that survive the blindspot pass, ordered
   by architectural blast radius: one question at a time when its answer changes the next
   question; batch independent ones. Stop when remaining answers wouldn't change the
   design. Answers land in the design doc's Decisions section — never only in chat.
3. **References over descriptions**: ask for existing code/designs/docs that embody what
   the operator wants (any language); extract the structure, don't transliterate the code.
4. **Plan with volatile decisions first**: the implementation plan leads with the
   decisions most likely to change (data models, type interfaces, UX flows) and buries the
   mechanical refactors at the bottom — review effort goes where reversal is expensive.

**Question discipline**: design-time and mid-execution uncertainty questions are welcome; one precise question (options +
recommendation) beats a confidently-bad decision. The forbidden thing is permission
theater (skill `operator-protocol` §Decisions). Ask async; keep
unblocked work moving.

## During implementation

- **Implementation notes**: keep `implementation-notes.md` in the work item's record
  (file tracker: `tasks/NNN-slug/`); every
  deviation from the plan (edge case forced a different approach) gets the what + why as
  it happens. Design-doc-affecting deviations update the design doc in the same commit
  (skill `design-flow` §Implement).
- **Output as signal**: when a result surprises you or the operator, treat it as a map gap
  first, a bug second — something wasn't in the prompt/spec that should have been. Fix the
  task-local spec or bible as appropriate; draft universal skill or rule changes for
  operator confirmation.

## After implementation

- **Pitch doc** (`PITCH.md` in the work item's record): prototype + spec + implementation
  notes in one shareable artifact, demo first (screenshot/GIF) — the closing handoff links it.
- **Pre-merge quiz**: before closeout on significant work (P0/P1, or any diff spanning multiple modules), generate a short self-quiz
  from the diff — the questions a reviewer would ask (why this boundary? what breaks if X?
  which invariant guards Y?) — and answer from evidence. Anything you can't answer from
  the actual code/runs is an unknown that escaped; chase it before merge.

## Map maintenance (meta)

- **Before proposing another skill**, check existing coverage and whether the procedure
  is reusable, substantial enough to need instructions, and stable enough to maintain.
  Repetition alone does not justify a skill while its procedure is still changing;
  keep evolving guidance in the relevant work record. A single fact belongs in existing
  guidance. A settled, reusable procedure may be worth capturing on its first occurrence.
- **Skill audit on model upgrades**: stronger models need less scaffolding — re-read the
  House Rules skills and repo bibles after major model changes and delete rules that now just
  add noise. Rules are load-bearing or they're clutter.
- Recurring interview answers and blindspot findings should produce proactive proposals
  for improving the design, bible, or skills. Persistence follows AGENTS.md §Operator
  correction.
