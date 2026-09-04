---
name: rust-canon
description: Rust stack defaults and quality gates for Rust-first product ecosystems — workspace layout, dependency policy, error handling, config layering, model-stack policy, secrets. Use when writing Rust, scaffolding crates, choosing dependencies, or picking models/providers.
license: MIT
---

# Rust Canon

Rust is the default for products — prefer building native over porting or wrapping.
TypeScript for standalone web libs and lightweight org tooling (Node ≥22 LTS — 24 preferred — ESM,
pnpm, near-zero deps); Svelte 5 + Vite + plain CSS (no SSR) for dashboards and
prototypes; Flutter when a multi-platform consumer app is needed. Python is throwaway
experiment glue only — never in `src/` or shipped code; confined to `prototypes/spikes/`
and gitignored scratch.

Shipping posture: server backends are Rust or TS by
complexity (Rust for durable/complex, TS for simple services), always runnable
containerized — any container runtime (Docker/Podman/other OCI, or enhanced ones like
Sysbox for system workloads), not Docker specifically — on a plain VPS or cloud
provider, never platform-locked out of the VPS path (set your default provider in the
repo bible). Web frontends are static Svelte + TS pages — no SSR
unless genuinely necessary (expensive to run). Mobile is native or Flutter, not web wrappers.

## Workspace

- Cargo workspace, crates prefixed `<product>-<name>`; edition 2024 for new crates.
- `rust-toolchain.toml` pinned and committed in every Rust repo; rustup only (no brew rust).
- Feature gates for optional subsystems (`sqlite`, `http`, `cli`, `experimental-*`);
  experimental features default OFF and byte-identical when off.
- Minimal dependencies — hand-roll small things before importing heavy deps (a JSON-RPC
  hand-roll beat rmcp to keep regex/tokio-util out). Household set: serde, serde_json,
  thiserror, anyhow, chrono, clap (derive), tokio, reqwest, rusqlite, axum, tracing.

## Code rules

- `thiserror` in libraries, `anyhow` in binaries — and never `anyhow` in hot paths.
- Never `unwrap()` in library code (tests only). Errors bubble to the caller/operator;
  no fail-open, no silent skip.
- Async on tokio; non-blocking, multi-threaded by default.
- `--release` by default for everything executed or measured; debug builds only when
  actively debugging (assertions, symbols, tight edit-compile loops).
- `///` docs on public items; names say what things do (`captured_at` ≠ `ingested_at`;
  no defaults encoded in names). Rename confusing things immediately.

## Repo tooling

Where a repo ships git/build/test scripts (`scripts/git-commit.sh`, smoke gates, guard
scripts), use them instead of raw commands — they encode repo law (submodule pointer
bumps, scope checks) that raw git/cargo silently violates.

## Gates

Gates must pass on the final candidate; iteration cadence per AGENTS.md §Verification.

```
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --all-features --no-fail-fast
```

Zero warnings is the bar. Red→green regression test per bug fix. Architecture guard scripts
(`scripts/ci-architecture-guards.sh`) run after structural changes. Env-mutating tests use
`#[serial(env)]`; fixtures are synthetic and date-relative (no fixture rot).

## Config layering (the standard way, everywhere)

```
built-in sane defaults → versioned TOML (profiles/presets) → env vars → CLI flags
```

- Per-product config crates — the same kit gets different settings per consuming product.
- Model/provider settings layer general → provider → provider-model (foundation owns them);
  no blanket rpm/tpm defaults buried in code.
- Env-var tuning (ad-hoc `MYAPP_*` knobs) is for experiments, not a production artifact —
  promote proven knobs into typed config keys.
- Record config hash in run params; versioned prompts live in config, not code.

## Model stack policy

- The settled model stack (embedder + dims, reranker, workhorse LLM, judge — with exact
  reasoning-effort levels per role) lives in the repo bible. Treat it as settled: never
  re-test rejected alternatives without new evidence, never substitute.
- Cheap/free-first: the cheapest model that clears the quality bar wins; report cost per
  run; no expensive models outside the approved standing or campaign resource envelope.
- Local inference where hardware allows (e.g. MLX/Ollama on Apple Silicon), with
  hardware-adaptive local/cloud routing and local redaction before any cloud egress.
- Keys in `.env.test.local`-style files — check there before declaring credentials missing.

## Storage

- Raw data canonical: Markdown vault + YAML frontmatter (Obsidian-compatible) or append-only
  event log. SQLite and vector indexes are rebuildable caches — skill `design-canon`.
- Prefer one store over parallel legacy stores; batch rebuild beats compat migration.
