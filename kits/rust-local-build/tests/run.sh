#!/usr/bin/env bash
# Kit tests in a temporary home: install/uninstall round trip, and the queue's exit code and stall limit.
# Never touches the real machine queue (CARGO_QUEUE_LOCK and CARGO_QUEUE_REAL point into the temp dir).
set -uo pipefail
KIT=$(cd "$(dirname "$0")/.." && pwd)
base=${KIT_TEST_DIR:-$HOME/.cache/rust-local-build/test}; mkdir -p "$base"   # durable path, not the system temp folder
T=$(mktemp -d "$base/run.XXXXXX"); trap 'rm -rf "$T"' EXIT
fail=0; check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
H=$T/home; mkdir -p "$H/.cargo" "$H/.config/kache" "$H/bin"
printf 'original cargo config\n' > "$H/.cargo/config.toml"
printf 'original kache config\n' > "$H/.config/kache/config.toml"
printf '#!/bin/sh\necho "kache 0.28.1"\n' > "$H/bin/kache"; chmod 0755 "$H/bin/kache"
cp -p "$H/.cargo/config.toml" "$T/orig-cargo"; cp -p "$H/.config/kache/config.toml" "$T/orig-kache"
cat > "$T/kit.conf" <<C
WRAPPER_DIR="$H/wrapper"
HELPER_DIR="$H/helper"
STATE_DIR="$H/state"
CACHE_DIR="$H/cache"
KACHE_BIN="$H/bin/kache"
KACHE_VERSION="0.28.1"
TOOLCHAIN="nightly-2026-10-03"
JOBS="6"
ZTHREADS="8"
BUDGET_OVERRIDE="6"
CARGO_HOME="$H/.cargo"
KACHE_CONFIG="$H/.config/kache/config.toml"
C
"$KIT/install" "$T/kit.conf" > "$T/install.log" 2>&1; check "install succeeds" '[ $? -eq 0 ]'
check "manifest lists 8 files" '[ "$(wc -l < "$H/state/kit-manifest.tsv")" -eq 8 ]'
check "no placeholder left" '! grep -l "@[A-Z_]*@" "$H/wrapper/cargo" "$H/helper"/* "$H/.cargo/config.toml" "$H/.config/kache/config.toml"'
check "cargo config uses the helper wrapper" 'grep -q "rustc-wrapper = \"$H/helper/kache-rustc\"" "$H/.cargo/config.toml"'
check "jobs and threads rendered" 'grep -q "^jobs = 6$" "$H/.cargo/config.toml" && grep -q "Zthreads=8" "$H/.cargo/config.toml"'
check "budget override written" '[ "$(cat "$H/state/build-budget-override")" = 6 ]'
check "second install refused" '! "$KIT/install" "$T/kit.conf" > /dev/null 2>&1'
"$KIT/status" "$T/kit.conf" > "$T/status.log" 2>&1
check "status reports installed files" '[ "$(grep -c "^installed" "$T/status.log")" -eq 8 ]'
# Queue: exit code passes through; a stalled build is stopped with 124 (fake cargo, private lock).
export CARGO_QUEUE_REAL="$KIT/tests/fake-cargo" CARGO_QUEUE_LOCK="$T/queue.lock"
FAKE_MODE=exit3 "$H/wrapper/cargo" test > /dev/null 2>&1; check "queue passes the exit code through" '[ $? -eq 3 ]'
start=$(date +%s); FAKE_MODE=sleep CARGO_QUEUE_STALL_MIN=0.15 "$H/wrapper/cargo" test > "$T/stall.log" 2>&1; rc=$?
check "queue stops a stalled build with 124" '[ $rc -eq 124 ] && [ $(( $(date +%s) - start )) -lt 60 ]'
# One number drives build jobs and test threads.
check "budget shows the installed override" '"$KIT/cores" "$T/kit.conf" | grep "^cores: 6 (override"'
"$KIT/cores" "$T/kit.conf" 4 > /dev/null
check "budget 4 reaches cargo as jobs and test threads" '[ "$(FAKE_MODE=env "$H/wrapper/cargo" test)" = "jobs=4 tests=4" ]'
check "status still reports the override as the kit file" '"$KIT/status" "$T/kit.conf" | grep "^installed .*build-budget-override"'
"$KIT/cores" "$T/kit.conf" 3 --for 1h > /dev/null
check "a timed budget records its expiry" 'read -r n e < "$H/state/build-budget-override"; [ "$n" = 3 ] && [ "$e" -gt "$(date +%s)" ]'
check "a timed budget reaches cargo" '[ "$(FAKE_MODE=env "$H/wrapper/cargo" test)" = "jobs=3 tests=3" ]'
printf '5 1\n' > "$H/state/build-budget-override"
check "an expired budget is ignored" '"$KIT/cores" "$T/kit.conf" | grep "expired or invalid, ignored"'
check "a lower test-thread request is kept" '[ "$(RUST_TEST_THREADS=1 FAKE_MODE=env "$H/wrapper/cargo" test)" = "jobs=$(cat "$H/state/build-budget") tests=1" ]'
check "budget refuses a non-number" '! "$KIT/cores" "$T/kit.conf" six > /dev/null 2>&1'
for line in "0" "8 abc" "8 $(( $(date +%s) + 3600 )) 5"; do printf '%s\n' "$line" > "$H/state/build-budget-override"
  "$KIT/cores" "$T/kit.conf" > "$T/odd.out" 2> "$T/odd.err"
  case $line in 0) want="^cores: 1 ";; *) want="ignored";; esac
  check "override '$line' read like the queue, without errors" 'grep "$want" "$T/odd.out" > /dev/null && [ ! -s "$T/odd.err" ]'
done
"$KIT/cores" "$T/kit.conf" --clear > /dev/null
check "cleared budget falls back to the computed value" '"$KIT/cores" "$T/kit.conf" | grep "^cores: .*computed"'
"$KIT/status" "$T/kit.conf" > "$T/status-cleared.log" 2>&1
check "status after clearing reports no missing file and the computed budget" '! grep -q "^missing" "$T/status-cleared.log" && grep -q "^cores: .*computed" "$T/status-cleared.log"'
"$KIT/cores" "$T/kit.conf" 6 > /dev/null
(cd / && "$H/wrapper/cargo-cores" cores 5) > /dev/null
check "cargo cores works from any folder" '(cd / && "$H/wrapper/cargo-cores" cores) | grep "^cores: 5 " > /dev/null'
"$KIT/cores" "$T/kit.conf" 6 > /dev/null
unset CARGO_QUEUE_REAL CARGO_QUEUE_LOCK
printf 'changed after install\n' >> "$H/.cargo/config.toml"
"$KIT/uninstall" "$T/kit.conf" > "$T/uninstall.log" 2>&1; check "uninstall succeeds" '[ $? -eq 0 ]'
check "cargo config restored byte for byte" 'cmp -s "$T/orig-cargo" "$H/.cargo/config.toml"'
check "kache config restored byte for byte" 'cmp -s "$T/orig-kache" "$H/.config/kache/config.toml"'
check "created files removed" '[ ! -e "$H/wrapper/cargo" ] && [ ! -e "$H/wrapper/cargo-cores" ] && [ ! -e "$H/helper/kache-rustc" ] && [ ! -e "$H/state/build-budget-override" ]'
check "changed file kept as a copy" 'ls "$H/state/kit-backups"/modified-*/* 2>/dev/null | grep -q config.toml'
check "manifest retired" '[ ! -e "$H/state/kit-manifest.tsv" ] && ls "$H/state"/kit-manifest.tsv.uninstalled-* > /dev/null 2>&1'
# A failed install restores what it replaced: the kache config directory is read-only, so its file fails last.
chmod 0555 "$H/.config/kache"
"$KIT/install" "$T/kit.conf" > "$T/install2.log" 2>&1; rc=$?
chmod 0755 "$H/.config/kache"
check "failed install exits nonzero" '[ $rc -ne 0 ]'
check "failed install restores the cargo config" 'cmp -s "$T/orig-cargo" "$H/.cargo/config.toml"'
check "failed install removes created files" '[ ! -e "$H/wrapper/cargo" ] && [ ! -e "$H/helper/kache-cc" ]'
check "failed install leaves no manifest" '[ ! -e "$H/state/kit-manifest.tsv" ] && [ ! -e "$H/state/kit-manifest.tsv.new" ]'
[ $fail -eq 0 ] && echo "all kit tests passed" || { echo "kit tests failed"; cat "$T/install.log" "$T/uninstall.log"; exit 1; }
