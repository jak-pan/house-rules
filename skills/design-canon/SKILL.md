---
name: design-canon
description: Architecture principles — raw-canonical data with rebuildable derived stores, black-box module boundaries, config over hardcoding, metadata over text heuristics, end-state-first, no pre-launch legacy, naming precision, spec-first UX. Use for design decisions, new components, refactors, specs, or architecture reviews.
license: MIT
---

# Design Canon

Use the overridable project defaults in `PREFERENCES.md` in the installed Groundwork root.
Apply these procedures to the actual product; examples do not require a memory system,
retrieval pipeline, or model stack in an unrelated application.

## Data

- **Canonical data and derived views.** Identify the authoritative store chosen for the
  product. Derived indexes and summaries link back to it and are rebuildable. Verify the
  required semantic or byte equivalence; nondeterministic summaries need not be identical
  bytes. A transactional database may be canonical, not merely a cache.
- **Provenance escalation.** Derived layers link back to raw; recall escalates depth on
  demand (distilled → raw detail). Context tiers are labeled by truth level (raw convo /
  distilled / brief) — each has different fact authority.
- **Prefer authoritative metadata.** Use available IDs, timestamps, and structured fields
  instead of guessing their meaning from prose. Regex or keyword logic can implement a
  real parsing/routing requirement; validate it against representative production inputs.
- **Choose retrieval cutoffs for the requirement.** Compare fixed top-K, thresholds, or
  distribution-based selection against quality, latency, and cost needs; no method is
  universally required. Record the selected policy and its evidence.
- Nothing silently dropped, skipped, or capped — chunks/blobs that can't be processed bubble
  errors up the chain.

## Boundaries

- **Black-box modules.** Hosts never see internals of a kit they consume (a host app must
  have zero knowledge of its memory kit's store internals).
  Facades + adapters + capability manifests; standalone reusable products with semver deps,
  nothing "bench-owned" or host-owned.
- **One parameterized pipeline** with skip/reuse flags — never forked ad-hoc flows tweaked
  independently. **One mechanism per concept**: duplicate paths doing "basically the same
  thing" get merged; dead or rule-violating paths get deleted completely.
- **Pipeline-order invariants are written down** (what runs before what, and why) and
  re-checked after every refactor — they are the first casualties of context resets.
- **State the redo-dependency DAG** for any multi-stage system: what invalidates what,
  and the cheapest valid re-entry point for each change class. Cache invalidation is
  structural, part of the flow — never a manual memory.
- Truth tiers labeled end-to-end: consumers see which data is raw vs derived vs
  summarized, each with its own authority level.
- Modular adapters over hardcoded tool-specific logic ("tools change").
- If adding an enum variant means rewriting 40 sites, that's a code smell — say so.
- Initialization equals first visible state: render/start only after all defaults are
  loaded; the first interaction must not change anything the defaults didn't declare.

## Decisions

- **End-state first.** Design load-bearing structure for the agreed product. Resolve
  material tenancy/distribution requirements without assuming a multi-tenant service.
- **No legacy pre-launch.** Delete dead paths completely (code, tests, call sites) — no deprecation
  shims, no backwards compatibility for things that never shipped.
- **Configurable, never hard-imposed.** Every policy that could vary is a versioned config
  with sane defaults (skill `rust-canon` §Config layering). Best-case defaults are found empirically,
  then owned by the operator.
- **Distrust accidental design.** every structure should have a defensible reason or be simplified.
  Less is usually more.
- **Now-vs-later is explicit.** Postponed scope is recorded as TODO and stays postponed;
  bleeding-edge is chosen deliberately when justified, not drifted into.
- **Names mean what they say.** Misleading names get renamed the moment they're noticed
  — no defaults encoded in names; timestamps disambiguated
  (captured_at / ingested_at / observed_at).

## Security & sovereignty

- Keep credentials separate from ordinary product data. Storage and diagnostic capture
  follow AGENTS.md §Security; do not invent conflicting secret-file rules here.
- Sovereignty: cloud egress of sensitive data is the operator's informed decision — neither
  a silent default nor a hard ban. Local models for private processing where hardware allows.
- Never weaken a capability/auth/redaction boundary as a workaround — fix the actual
  problem. What counts as a boundary: AGENTS.md §Security.

## Spec-first UX

For complex products: system map → per-screen micro-specs (Mermaid + md) → lofi → hifi
prototype (Svelte, mock data) → implementation. Component library before screens. Hifi
prototypes exist so decisions happen before the engine is wired to the frontend. Function
before polish — a confusing broken flow outranks theming every time. Design against
personas: every persona's consumption path must exist and be satisfying.
Full lifecycle with stage gates, artifact paths, and closeout: skill `design-flow` +
`STRUCTURE.md` in the installed Groundwork root.

## Docs

- Two tiers: one clean system map for high-level understanding + deep dives per feature.
- Docs update in the same commit as the code that changed them; doc sweeps after design
  changes. Engineering guidance lives in repo docs/runbooks — never in assistant memory.
- In Markdown, diagrams are Mermaid, never ASCII art.
