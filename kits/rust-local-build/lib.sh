# Shared helpers for install, uninstall and status. Sourced, not run.
KIT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
load_conf() {
  [ -n "${1:-}" ] && [ -f "$1" ] || { echo "usage: $(basename "$0") <kit.conf>" >&2; exit 2; }
  set -a; . "$1"; set +a
  local v
  for v in WRAPPER_DIR HELPER_DIR STATE_DIR CACHE_DIR KACHE_BIN KACHE_VERSION TOOLCHAIN JOBS ZTHREADS CARGO_HOME KACHE_CONFIG; do
    [ -n "${!v:-}" ] || { echo "kit.conf: $v is empty" >&2; exit 2; }
    case $v in KACHE_VERSION|TOOLCHAIN|JOBS|ZTHREADS) ;; *) case ${!v} in /*) ;; *) echo "kit.conf: $v must be absolute" >&2; exit 2 ;; esac ;; esac
  done
  case $JOBS$ZTHREADS in *[!0-9]*) echo "kit.conf: JOBS and ZTHREADS must be numbers" >&2; exit 2 ;; esac
  MANIFEST="$STATE_DIR/kit-manifest.tsv"
}
sha() { shasum -a 256 < "$1" | cut -c1-64; }
