---
name: design-canon
description: Architecture principles — raw-canonical data with rebuildable derived stores, black-box module boundaries, config over hardcoding, metadata over text heuristics, end-state-first, no pre-launch legacy, spec-first UX. Use for design decisions, new components, refactors, specs, or architecture reviews.
license: MIT
---

# Design Canon

Stack defaults: `PREFERENCES.md` in the installed House Rules root. Apply these principles
to the actual product; examples do not require a memory system, retrieval pipeline, or
model stack in an unrelated application.

## Data

- **Canonical data and derived views.** Identify the authoritative store chosen for the
  product. Derived indexes and summaries link back to it and are rebuildable. Verify the
  required semantic or byte equivalence; nondeterministic summaries need not be identical
  bytes. A transactional database may be canonical, not merely a cache.
- **Provenance escalation.** Derived layers link back to raw; recall escalates depth on
  demand (distilled → raw detail).
- **Truth tiers labeled end-to-end.** Consumers see which data is raw vs derived vs
  summarized, each with its own fact authority.
- **Prefer authoritative metadata.** Use available IDs, timestamps, and structured fields
  instead of guessing their meaning from prose. Regex or keyword logic can implement a
  real parsing/routing requirement; validate it against representative production inputs.
- **Choose retrieval cutoffs for the requirement.** Compare fixed top-K, thresholds, or
  distribution-based selection against quality, latency, and cost needs; no method is
  universally required. Record the selected policy and its evidence.

## Boundaries

- **Black-box modules.** Hosts never see internals of a kit they consume (a host app must
  have zero knowledge of its memory kit's store internals).
  Facades + adapters + capability manifests; standalone reusable products with semver deps,
  nothing owned by a benchmark harness or a single host. This holds at build time too: a
  consumer never mirrors, re-hosts, pins or special-cases a dependency's internal
  artifacts (native libraries, model files, generated code, release assets). The
  dependency's own build acquires and verifies them from its own source of truth; a
  consumer may at most supply a credential. When that fails in a consumer's environment,
  fix the dependency, not the consumer. Pinning the dependency's own version (a lockfile or
  pin file) is not reaching into its internals. Operator direction: 2026-09-28, after a
  product's CI had to mirror a kit's native library releases into its own repository.
- **One parameterized pipeline** with skip/reuse flags — never forked ad-hoc flows tweaked
  independently. **One mechanism per concept**: duplicate paths doing "basically the same
  thing" get merged; dead or rule-violating paths get deleted completely.
- **Extend the owner; never fork it.** When a consumer cannot use a shared module's
  mechanism as it stands (a missing backend, feature, or constraint such as "no embedded
  database"), the gap is fixed in the module that owns the mechanism, and the consumer
  adapts to that. A local copy in the consumer is a new duplicate, however temporary it
  is called. A change that adds behaviour to a known duplicate is blocked in review until
  the duplicate's removal is tracked (AGENTS.md §Work tracking & continuity), and it
  should land on the shared mechanism instead where that is practical. Boundary:
  covers infrastructure that has, or should have, one owner (queues, transports,
  provider wrappers, storage backends); product-specific behaviour built on top of it
  stays in the product. Operator direction: 2026-09-28, after a consumer forked a shared
  mechanism it could not use as it stood.
- **Pipeline-order invariants are written down** as an explicit ordered list (what runs
  before what, and why) and re-checked after every refactor — they are the first
  casualties of refactors and context resets.
- **State the redo-dependency DAG** for any multi-stage system: what invalidates what,
  and the cheapest valid re-entry point for each change class. Cache invalidation is
  structural, part of the flow — never a manual memory.
- Modular adapters over hardcoded tool-specific logic ("tools change").
- If adding an enum variant means rewriting 40 sites, that's a code smell — say so.
- Initialization equals first visible state: render/start only after all defaults are
  loaded; the first interaction must not change anything the defaults didn't declare.

## Decisions

- **End-state first.** Design load-bearing structure for the agreed final product — no
  "fix in v2" for load-bearing structure — using the simplest tenancy/deployment model
  that meets it. Do not add multi-tenancy solely because a future product might need it.
- **No legacy pre-launch.** Delete dead paths completely (code, tests, call sites) — no deprecation
  shims, no backwards compatibility for things that never shipped.
- **Configurable, never hard-imposed.** Every policy that could vary is a versioned config
  with sane defaults; a spec defines the defaults and the config surface (Rust layering:
  skill `rust-canon` §Config layering). Best-case defaults are found empirically, then
  owned by the operator.
- **Distrust accidental design.** Every structure should have a defensible reason or be simplified.
  Less is usually more.
- **Now-vs-later is explicit.** Postponed scope is recorded as TODO (it stays postponed:
  AGENTS.md prime rule 10); bleeding-edge is chosen deliberately when justified, not
  drifted into.

## Security & sovereignty

- Keep credentials separate from ordinary product data; storage and diagnostic capture
  follow AGENTS.md §Security.
- Prefer local models for private processing where hardware allows (e.g. MLX/Ollama on
  Apple Silicon), with hardware-adaptive local/cloud routing and local redaction before
  any cloud egress. Egress itself follows AGENTS.md §Security.

## Spec-first UX

For complex products, specify and prototype UX before the engine is wired to the frontend
(stages: skill `design-flow` §Prototype). Function before polish — a confusing broken flow
outranks theming every time. Design against personas: every persona's consumption path
must exist and be satisfying.

## Docs

- Two tiers: one clean system map for high-level understanding + deep dives per feature.
- Doc sweeps after design changes (same-commit rule: AGENTS.md §Git).
