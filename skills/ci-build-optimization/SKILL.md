---
name: ci-build-optimization
description: Diagnose and reduce CI build time and cost, especially Rust cache reuse, runner sizing, and safe parallel scheduling. Use for CI performance work; application runtime tuning belongs elsewhere.
license: MIT
---

# CI build optimization

Optimize the time to a trustworthy required result. Preserve the repository's
build, test, security, and release contracts; select mechanisms proportional to
the measured bottleneck. A faster compiler phase does not establish faster CI.

## Establish what is actually running

Read the effective workflow and every invoked helper, including container entrypoints,
cache actions, post steps, artifact admission, and release packaging. Record the
source revision and required gate set. Follow existing work-item and delivery authority.

Distinguish four clocks: queue delay, each job's allocation, the full required
workflow's elapsed time, and nested command time. Construct the dependency path from
job and step timestamps. Account for setup, restore, archive compression, uploads,
post actions, and handoff gaps; label unexplained time instead of attributing it to
compilation. Parallel intervals count once in elapsed time.

Before a paid comparison, settle the decision, workload, original cache seed,
runner conditions, maximum runs/runtime/cost, and failure stopping point. Reuse
existing valid measurements; the operator need not repeat an already settled
experiment interview. Use `bench-discipline` for broader experimental design when
available. A required validation run is not automatically a performance campaign.
When authorized to reuse validation, compare source and effective gate/build-contract
identities. A parent workflow fix can need fresh workflow validation while an unchanged
pinned dependency retains its earlier proof. Record that reuse explicitly; never turn
a cache hit into a claim that tests passed or silently bypass repository policy.

## Rust: recover reuse before adding cores

Identify the effective toolchain, target triple, profile, features, native ABI,
compiler/linker, build-script inputs, codegen settings, incremental mode, wrappers,
source paths, target paths, and Cargo job count. Matching `--release` alone does not
make check, Clippy, test, and binary artifacts identical. Preserve deliberate debug
assertion tests and platform/feature gates when aligning profiles.

Separate the caches:

| Cache | What a hit proves |
|---|---|
| Builder image / tool installation | The build environment can be reused |
| Cargo registry and Git sources | Dependencies need not be fetched again |
| Cargo target with native incremental state | Compatible compiled outputs may be reused |
| Compiler wrapper cache | Eligible compiler invocations may be served by the wrapper |

A builder hit is not a warm compilation. A wrapper seed is not evidence of native
incremental state. Verify restored keys, scope, contents, compatibility and actual
reuse. Preserve the complete required target state; inspect cache-action pruning
and save behavior before assuming workspace incremental artifacts survive.

Content-verified preservation of unchanged source/native input timestamps can avoid
false build-script invalidations on fresh checkouts. Never disguise changed inputs
with restored timestamps. Verify native package provenance and digest before reuse;
keep compatible image/ABI/toolchain identities in cache selection. A broad restore
prefix requires validation before Cargo accesses the restored target.
A digest or provenance file inside that same cache is not an independent trust
anchor: compare against repository-pinned hashes or trusted attestations. Cached
metadata must not switch a prebuilt-only verifier into a weaker source-build mode.

Avoid simultaneous Cargo writers sharing a target: they can serialize on locks or
invalidate one another. Independent targets permit concurrency at the cost of duplicate
work, memory and storage. Inspect all helper paths before overriding `CARGO_TARGET_DIR`:
packaging and relocation scripts may still read a literal `target/release`.

Use normal compiler progress. Temporarily enable verbose/fingerprint diagnostics to
prove why work rebuilds, then remove them after confirming the mechanism. Preserve
exit status through logging pipes. Probe the smallest distinguishing case before
another expensive full build.
After restructuring CI, run its complete cheap pre-build sequence in workflow order,
including source-cleanliness checks. Individually passing fixtures can still leave
generated files, depend on a renamed step, or expect an obsolete command form. Prove
that the revised guard still rejects its intended failure before paying for a retry.

## Parallelize at real dependency boundaries

First overlap genuinely independent gates or setup with cache restoration. Join
every worker, propagate failures, and publish readiness only after outputs are
complete. A background shell cannot directly update the parent environment; use an
owned result file and import it after a successful join. Preserve credential scope.

Setup may overlap target restoration only while neither path reads or writes that
target. If cache identity requires the prepared builder, either retain this dependency
or use a verified identity sidecar and compare it against the actual builder before
using the restored outputs. A cold miss must remain correct.

For long test execution, consider compiling all outputs first, then overlapping
read-only tests with cache/archive publication. Read
[the build/test split contract](references/build-test-overlap.md) before implementing
this pattern. Prefer ordinary Cargo execution when the savings do not justify a
separate execution protocol. Multiple feature builds or short tests often favor the
simpler pipeline.

A successful compilation can be cacheable before tests finish when repository policy
permits, but it is not a passed CI run or a releasable artifact. Admission and final
status still depend on every required gate.

## Compare and report fairly

Use the same application revision or same representative edit, exact gates and
immutable pre-edit cache seed for all arms. Do not let the second arm consume the
first arm's newly warmed output. Distinguish cold, warm unchanged, and warm edited
runs. If unchanged code is intentionally skipped, a no-op rebuild is not the target
workload. Confirm that saved caches are available before dispatching consumers.
Record the workflow event, Git ref and cache version alongside the key. Verify a
restore in the actual consumer scope; an existing compatible archive is not enough.
GitHub PR merge-ref caches cannot seed the default branch or other PRs; preserve a
trusted default-branch cache producer when adopting the workflow. See
[GitHub's cache access rules](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache).

Record actual CPU model, available CPUs, memory and Cargo jobs, not only the runner
label. Runner sizes can also change CPU generation. Treat a single paired run as an
observation, not a stable speedup estimate; state bundled changes and hardware
confounders. Preserve test counts/results and relevant artifact identity evidence.

For GitHub-hosted larger runners, a configured runner entry represents a pool of
separate job VMs, limited by its concurrency setting. Check repository/group/workflow
eligibility before selecting an organization label. Cross-repository optimization
does not authorize transfers, access changes or subscriptions by itself.

Read current provider pricing when estimating spend. Attribute compute to the actual
runner used by each job, apply the provider's per-job rounding, and separate included
standard minutes from paid larger runners. Do not price the entire workflow as though
every job used its largest runner. Step costs are time allocations within a job,
not independent bills; avoid double-counting overlapped work. Storage is a separate
size-and-retention expense.

Deliver the resulting workflow, required-gate evidence, full elapsed comparison,
cost assumptions, and remaining limitations. Separate prepared, published, validated,
and adopted states. Do not claim measured savings for another repository merely
because the same pattern was applied.
