---
name: rust-canon
description: Rust implementation defaults and quality gates for workspace layout, dependencies, errors, configuration, and applicable model integrations. Use when writing Rust or scaffolding crates; general project stack selection belongs to project-bootstrap.
license: MIT
---

# Rust Canon

Project stack defaults live in `PREFERENCES.md` in the installed Forge root and apply
unless overridden. This skill applies after Rust is selected. Its tooling choices are
defaults too: preserve explicit user and repository decisions and the host's controls.

## Workspace

- Cargo workspace, crates prefixed `<product>-<name>`; edition 2024 for new crates.
- `rust-toolchain.toml` pinned and committed in every Rust repo; rustup only (no brew rust).
- Feature gates for optional subsystems (`sqlite`, `http`, `cli`, `experimental-*`);
  experimental features default OFF and byte-identical when off.
- Minimal dependencies — hand-roll small things before importing heavy deps. Household set: serde, serde_json,
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

## Config layering (default for Rust products)

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

Apply this section only to components that actually use models; do not add a model stack.

- The settled model stack (embedder + dims, reranker, workhorse LLM, judge — with exact
  reasoning-effort levels per role) lives in the repo bible. Treat it as settled: never
  re-test rejected alternatives without new evidence, never substitute.
- Cheap/free-first: the cheapest model that clears the quality bar wins; report cost per
  run; no expensive models outside the approved standing or campaign resource envelope.
- Local inference where hardware allows (e.g. MLX/Ollama on Apple Silicon), with
  hardware-adaptive local/cloud routing and local redaction before any cloud egress.
- Inspect the configured credential provider without displaying values; credential
  storage and diagnostic capture follow AGENTS.md §Security.

## Storage

Follow `PREFERENCES.md` and the project's selected canonical store. Use `design-canon`
for derived-data boundaries. Preserve shipped data compatibility and recovery needs;
rebuild is appropriate only when the required canonical data and equivalence are known.
