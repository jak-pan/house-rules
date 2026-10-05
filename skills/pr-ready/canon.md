Shared code canon, inlined into every reviewer and worker prompt in place of the {{CANON}} line.

Canon the change must follow:
- Fail visible: nothing is silently skipped, dropped, capped, truncated or degraded;
  errors reach the caller; no fail-open paths. Root causes, not suppression: a retry,
  sleep, catch-all or widened tolerance that hides a symptom is blocking.
- Never remove or downgrade a security or architecture boundary as a workaround. A
  boundary is one the spec, threat model or shipped runtime declares; a reviewer concern
  is not one by label alone. Credentials never appear in code, tests, fixtures or logs.
- Recorded operator decisions are settled. If the code follows one you think is wrong,
  report it under Spec issues with "operator decision needed"; do not block on it.
- Simplicity: one mechanism per concept; duplicates are merged; a shared owner is
  extended, never forked into a local copy; every structure has a defensible reason.
- Delete unreleased dead paths; rebuild pre-release internal formats and current live data, without migrations or legacy readers; product schema migrations may be a feature (design-canon §Decisions).
- Policies that could vary are versioned config with spec-stated defaults, not constants.
- Derived indexes and caches are rebuildable from the canonical store and never become a
  second source of truth.
- New persistent state (stored fields, indexes, projections, caches, mirrors) needs a spec
  line or settled decision that requires it; state that only duplicates the source of
  truth is waste. Ask "why does this exist?" before "how do we keep it in sync?".
- Ordering invariants the code depends on are written down.
- Structured fields (ids, timestamps, typed values) over parsing meaning from text.
- Claims such as "measured", "verified" or "bounded" point at the test, benchmark or code
  that shows them.
- Rust: no `unwrap()` in library code; `thiserror` in libraries, `anyhow` only in binaries
  and never on hot paths; public items carry `///` docs.

## Native-first

Storage, read and search changes state the bare-engine cost of the same operation and
what each added layer earns. Use the underlying engine or library's supported features
first; a layer that does not earn its counted cost blocks review.

## No fortification

A cache, budget, retry, index-like row, indirection or reduced test that works around
cost or complexity elsewhere must name the root cause. Fix that cause or cite a recorded
decision accepting the workaround. First ask whether the mechanism should exist; delete
or narrow it before adding another mechanism. A workaround without that evidence blocks
review.

## Test discipline

Single tests finish in seconds and never run long. Remove a known looping or hanging
test at once, keep its defect tracked, and replace it with a small, explicitly bounded
test. Stop a command holding the shared build queue after a few minutes without CPU
progress and after a fixed overall hold limit; configure those limits in the build runner.

Test logging and pruning follow [Guard upkeep](references/guards.md#guard-upkeep).
Scale tests move, never vanish: record the replacement test and where it runs,
preserving the scale and behavior it proves.
