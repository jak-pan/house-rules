# Overlapping test execution with cache publication

Use this pattern when measured test execution can hide meaningful cache compression,
upload, or artifact work. It is a scheduling change with a test-execution contract,
not just appending `&` to two Cargo commands.

## Find the final writer

Compile ordinary tests, required doctests, and production binaries before declaring
the target immutable. `cargo test --no-run` does not execute doctests; normal doctest
execution may still compile. Run doctests before the freeze, or give them independent
storage and include that cost in the comparison. Complete feature-specific builds,
binary audits and metadata writes as required by their actual dependencies.

The test worker must not modify the files being archived. Cover every alias of the
target, including bind mounts, symlinks and host/container paths. A read-only mount
is useful evidence; provide separate writable scratch where tests legitimately need
it. Restoring a cache and starting Cargo against it are also separate phases.

## Preserve the execution contract

Prefer a supported test runner that already preserves the repository's behavior.
If recording and replaying Cargo invocations, capture the exact executable, argument
vector, working directory, and required environment through Cargo's runner interface.
Do not enumerate executables with a target-directory glob: stale binaries and custom
harnesses make that unreliable.

Retain target selection, package order where relevant, custom `harness = false`
arguments, Cargo-provided environment, fixture paths, ignored-test policy, doctests,
and fail-fast/no-fail-fast behavior. Remove recorder-only configuration before replay.
Treat records as owned run state; clear stale completion markers before starting.
Do not persist credentials in captured environments or logs.

Validate equivalence using the ordinary baseline: captured command set, harness/test
counts and outcomes, required artifacts, plus targeted tests for orchestration failure
paths. Counts alone do not prove identical execution semantics.

## Make the join trustworthy

Use explicit states such as preparing, ready, running, and completed; atomically
publish status only after outputs are durable. Keep logs live and attributable to
their phase. A successful cache save must not overwrite a test failure. Join all
required workers before producing the final job result, including paths where setup,
tests, or publication fail.

Bound workers by owned process groups, handle cancellation, and reap descendants.
Container PID 1 changes process behavior: replacing an existing entrypoint with a
Python coordinator can change orphan reaping and signal handling. Verify the actual
entrypoint with a small Linux process probe and the affected product tests; retaining
an established init/shell may be simpler than adding new process supervision.

## Interpret the result

The theoretical saving is the hidden portion of independent work, bounded by the
shorter overlapping branch, minus added coordination and contention. Compression
can compete with CPU-bound tests, and cache restore can saturate disk/network. Measure
the complete required workflow after the change; retain phase intervals so the gain
can be explained without adding their durations twice.

This pattern was extracted from a September 2026 Rust CI optimization session:
verbose compilation obscured progress, archive work extended the critical path, and
a replacement container entrypoint initially broke process cleanup tests. The lasting
lessons are semantic equivalence, immutable publication inputs, and full elapsed
accounting. Particular core counts, timings, cache keys and prices are campaign data,
not defaults for other repositories.
