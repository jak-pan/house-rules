#!/usr/bin/env bash
# Run a read-only review panel in parallel.
# Usage: review-panel.sh <name> <checkout> <base-prompt> [reviewer ...]
#   reviewer: a file stem in ../reviewers/ (default: generalist-<family> for each configured family)
# Config: ${REVIEW_PANEL_CONF:-<house-rules>/custom/review-panel.conf}, lines "<family> = <cli> <model> [tier] [effort]",
#   cli one of codex | grok | kimi. Families without a config line are skipped.
# Prompt order: common rules, lens, summary/task, spec, change (prepare.py review).
# Range: ${REVIEW_BASE:-remote default branch}...HEAD; upstream preferred to origin.
# Output directory: ${REVIEW_PANEL_OUT:-<checkout>/.tmp/review-panel}/<name>/ with <reviewer>.md,
#   raw logs, and summary.txt (verdict and wall time per reviewer).
set -u
here=$(cd "$(dirname "$0")" && pwd)
reviewers_dir=$here/../reviewers
conf=${REVIEW_PANEL_CONF:-$here/../../../custom/review-panel.conf}
name=$1; dir=$(cd "$2" && pwd); base=$(cd "$(dirname "$3")" && pwd)/$(basename "$3"); shift 3
out=${REVIEW_PANEL_OUT:-$dir/.tmp/review-panel}/$name; mkdir -p "$out"
family_cfg() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$conf" 2>/dev/null | head -1; }
frontmatter() { sed -n "s/^$2:[[:space:]]*//p" "$1" | head -1; }

if [ $# -eq 0 ]; then
  for f in a b c; do [ -n "$(family_cfg $f)" ] && set -- "$@" "generalist-$f"; done
fi
[ $# -gt 0 ] || { echo "no reviewers: configure families in $conf" >&2; exit 2; }

base_args=(base "$dir")
[ -n "${REVIEW_BASE:-}" ] && base_args+=(--base "$REVIEW_BASE")
resolved_base=$("$here/prepare.py" "${base_args[@]}") || exit 1

run_one() {
  local r=$1 file=$reviewers_dir/$1.md
  local fam cfg cli model tier effort prompt=$out/$r.prompt t0 cli_status=0 verdict
  # A reused panel directory must never supply evidence from a previous run.
  if ! rm -f -- "$out/$r.md" "$out/$r.jsonl" "$out/$r.json" \
      "$out/$r.err" "$out/$r.prepare.err" "$prompt"; then
    echo "$r failed: clearing previous reviewer outputs" >> "$out/summary.txt"
    return 1
  fi
  fam=$(frontmatter "$file" family); cfg=$(family_cfg "$fam")
  [ -n "$cfg" ] || { echo "$r skipped: family $fam not configured" >> "$out/summary.txt"; return; }
  read -r cli model tier effort <<<"$cfg"; [ "$tier" = - ] && tier=
  local prepare_args=(review "$dir" --lens "$r" --cli "$cli" --summary "$base" --base "$resolved_base" --no-fetch)
  if ! "$here/prepare.py" "${prepare_args[@]}" > "$prompt" 2> "$out/$r.prepare.err"; then
    cat "$out/$r.prepare.err" >&2
    echo "$r failed: context preparation (see $r.prepare.err)" >> "$out/summary.txt"
    return 1
  fi
  cat "$out/$r.prepare.err" >&2
  sed -n '/^# 1\. Review pack/q; /^Size guard:/p' "$prompt" |
    while IFS= read -r notice; do printf '%s: %s\n' "$r" "$notice"; done >> "$out/summary.txt"
  t0=$(date +%s)
  case $cli in
    codex) codex exec --json --skip-git-repo-check -m "$model" -c model_reasoning_effort="${effort:-high}" \
             ${tier:+-c service_tier="\"$tier\""} -s read-only -C "$dir" -o "$out/$r.md" - < "$prompt" \
             > "$out/$r.jsonl" 2> "$out/$r.err" || cli_status=$? ;;
    grok)  (cd "$dir" && env GROK_CLAUDE_AGENTS_ENABLED=0 GROK_CLAUDE_SKILLS_ENABLED=0 GROK_CLAUDE_RULES_ENABLED=0 \
             GROK_CLAUDE_MCPS_ENABLED=0 GROK_CLAUDE_HOOKS_ENABLED=0 GROK_CURSOR_AGENTS_ENABLED=0 \
             GROK_CURSOR_SKILLS_ENABLED=0 GROK_CURSOR_RULES_ENABLED=0 \
             grok -m "$model" --reasoning-effort "${effort:-high}" --output-format json --always-approve --disable-web-search --prompt-file "$prompt" > "$out/$r.json" 2> "$out/$r.err") || cli_status=$?
           if [ "$cli_status" -eq 0 ]; then
             python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('text',''))" "$out/$r.json" > "$out/$r.md" 2>> "$out/$r.err" || cli_status=$?
           fi ;;
    kimi)  (cd "$dir" && kimi -m "$model" -p "$(cat "$prompt")" > "$out/$r.md" 2> "$out/$r.err") || cli_status=$? ;;
    *)     echo "$r skipped: unknown cli $cli" >> "$out/summary.txt"; return ;;
  esac
  if [ "$cli_status" -ne 0 ]; then
    echo "$r failed: reviewer CLI (exit $cli_status; see $r.err)" >> "$out/summary.txt"
    return 1
  fi
  if ! verdict=$(grep -E -m1 '^VERDICT: (APPROVE|REQUEST_CHANGES)[[:space:]]*$' "$out/$r.md" 2>> "$out/$r.err"); then
    echo "$r failed: reviewer report missing valid VERDICT: APPROVE or VERDICT: REQUEST_CHANGES line (see $r.md and $r.err)" >> "$out/summary.txt"
    return 1
  fi
  echo "$r $cli/$model wall=$(( $(date +%s) - t0 ))s verdict=${verdict#VERDICT: }" >> "$out/summary.txt"
}

: > "$out/summary.txt" || exit 1
"$here/review-panel-models.py" --check >&2 || true   # notice only: newer models available
pids=()
for r in "$@"; do
  run_one "$r" &
  pids+=("$!")
done
status=0
for pid in "${pids[@]}"; do wait "$pid" || status=1; done
[ -n "$(git -C "$dir" status --porcelain)" ] && echo "WARNING: a reviewer modified the checkout" >> "$out/summary.txt"
cat "$out/summary.txt"
exit "$status"
