# Kit: local Rust builds

Installs the local Rust build setup that skill `ci-build-optimization` §Local Rust builds describes:
a machine-wide cargo queue with a core budget, a shared compiler cache (kache), and one set of local
build settings. Everything it writes is recorded, and `uninstall` puts the machine back as it was.

## What it installs

| File | Installed as |
|---|---|
| `files/cargo-queue` | `$WRAPPER_DIR/cargo` |
| `files/kache-rustc`, `kache-cc`, `kache-c++` | `$HELPER_DIR/` |
| `files/cargo-config.toml` | `$CARGO_HOME/config.toml` |
| `files/kache-config.toml` | `$KACHE_CONFIG` |
| `BUDGET_OVERRIDE` (if set) | `$STATE_DIR/build-budget-override` |

Prerequisites, not installed by the kit: rustup with the toolchain named in `TOOLCHAIN`, and the kache
binary (version `KACHE_VERSION`) at `KACHE_BIN`.

## Use

1. Copy `kit.conf.example` to a machine-local file (House Rules: `custom/rust-local-build.conf`, gitignored)
   and set the paths.
2. `kits/rust-local-build/install custom/rust-local-build.conf`
3. Put `$WRAPPER_DIR` before `$CARGO_HOME/bin` in `PATH`.
4. `kits/rust-local-build/status custom/rust-local-build.conf` shows each installed file (installed,
   changed or missing), which cargo is on `PATH`, and the budget cargo will use.

`uninstall <kit.conf>` restores every replaced file from its backup and removes files the kit created. A
file changed after install is first kept under `$STATE_DIR/kit-backups/modified-<time>/`. A failed
install restores what it had already replaced. A second install is refused until the first is
uninstalled; to upgrade, uninstall and install again.

## The core budget

The queue runs one compiling cargo command at a time on the whole machine and sets `CARGO_BUILD_JOBS`
and `RUST_TEST_THREADS` to the budget: total cores − efficiency cores − 2 (`BUILD_RESERVE`), saved in
`$STATE_DIR/build-budget` for sandboxes that cannot read core counts. An operator override in
`$STATE_DIR/build-budget-override` wins: one number, or `<number> <expiry epoch seconds>`. Delete the
file to return to the computed budget.

`-Zthreads` (`ZTHREADS`) does not raise the core count: the compiler's extra front-end threads come from
the same job pool. Changing its value changes every crate's fingerprint, so every target rebuilds once.

Hold limits: the queue stops a build that makes no CPU progress for `CARGO_QUEUE_STALL_MIN` minutes
(default 5) or holds the queue longer than `CARGO_QUEUE_MAX_HOLD_MIN` (default 40), with exit 124.

## Tests

`tests/run.sh` installs into a temporary home and checks the round trip (byte-identical restore, created
files removed, changed files kept, failed install rolled back) and the queue's exit code and stall limit
with `tests/fake-cargo`. It never touches the real queue.
