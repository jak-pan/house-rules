#!/usr/bin/env bash
# Quick review: one reviewer from family a (configure a fast, high-effort model there) for small,
# well-understood changes. Same prompt, rules and outputs as review-panel.sh, one model instead of
# the panel. Usage: quick-review.sh <name> <checkout> <base-prompt>
#
# Use for: fix-diff check-backs after a full panel round, docs and configuration edits, CI and
# build fixes, small refactors. Not for: a first review of a feature, access control or
# confidentiality, durability or storage, security-sensitive paths, or new mechanisms; those get
# the full panel. Changes above QUICK_REVIEW_MAX_LINES (default 300) changed lines are refused
# unless QUICK_REVIEW_FORCE=1. A quick review that raises a blocker or a spec issue goes to the
# full panel after the fix.
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd)
[ $# -eq 3 ] || { sed -n '2,4p' "$0" >&2; exit 2; }
dir=$(cd "$2" && pwd) || exit 2
base_args=(base "$dir")
[ -n "${REVIEW_BASE:-}" ] && base_args+=(--base "$REVIEW_BASE")
base=$("$here/prepare.py" "${base_args[@]}") || exit 1
# Pin the base to a commit so the size check and the review see the same range.
base=$(git -C "$dir" rev-parse --verify "$base^{commit}") || exit 1
# Match what the reviewer sees: no rename detection; a binary file ("-") cannot be measured.
changed=$(git -C "$dir" diff --no-renames --numstat "$base...HEAD" |
  awk '$1 == "-" || $2 == "-" {print "binary"; exit} {a+=$1; d+=$2} END {if (NR == 0 || a+d >= 0) print a+d+0}' | tail -1) || {
  echo "quick review failed: cannot measure the change" >&2; exit 1; }
if [ "$changed" = binary ] && [ "${QUICK_REVIEW_FORCE:-0}" != 1 ]; then
  echo "quick review refused: the change includes binary files; run review-panel.sh (or set QUICK_REVIEW_FORCE=1)" >&2
  exit 2
fi
[ "$changed" = binary ] && changed=0
max=${QUICK_REVIEW_MAX_LINES:-300}
[[ "$max" =~ ^[0-9]+$ ]] || { echo "quick review failed: QUICK_REVIEW_MAX_LINES must be a whole number" >&2; exit 2; }
if [ "$changed" -gt "$max" ] && [ "${QUICK_REVIEW_FORCE:-0}" != 1 ]; then
  echo "quick review refused: $changed changed lines exceed $max; run review-panel.sh (or set QUICK_REVIEW_FORCE=1)" >&2
  exit 2
fi
REVIEW_BASE=$base exec "$here/review-panel.sh" "$1" "$dir" "$3" generalist-a
