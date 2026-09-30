#!/usr/bin/env bash
# Run a read-only review panel in parallel.
# Usage: review-panel.sh <name> <checkout> <base-prompt> [reviewer ...]
#   reviewer: a file stem in ../reviewers/ (default: generalist-<family> for each configured family)
# Config: ${REVIEW_PANEL_CONF:-<house-rules>/custom/review-panel.conf}, lines "<family> = <cli> <model> [tier] [effort]",
#   cli one of codex | grok | kimi. Families without a config line are skipped.
# Handoff: the change is put in context first (review-handoff.py): the full diff for codex, the
#   changed files and touched functions for other CLIs. Range: ${REVIEW_BASE:-origin's default branch}...HEAD.
# Output directory: ${REVIEW_PANEL_OUT:-<checkout>/.tmp/review-panel}/<name>/ with <reviewer>.md,
#   raw logs, and summary.txt (verdict and wall time per reviewer).
set -u
here=$(cd "$(dirname "$0")" && pwd)
reviewers_dir=$here/../reviewers
conf=${REVIEW_PANEL_CONF:-$here/../../../custom/review-panel.conf}
name=$1; dir=$(cd "$2" && pwd); base=$(cd "$(dirname "$3")" && pwd)/$(basename "$3"); shift 3
out=${REVIEW_PANEL_OUT:-$dir/.tmp/review-panel}/$name; mkdir -p "$out"
default_base() {
  git -C "$dir" rev-parse --abbrev-ref origin/HEAD 2>/dev/null && return
  for b in origin/main origin/master; do git -C "$dir" rev-parse -q --verify "$b" >/dev/null && { echo "$b"; return; }; done
}
review_base=${REVIEW_BASE:-$(default_base)}
[ -n "$review_base" ] || { echo "no base branch: set REVIEW_BASE" >&2; exit 2; }

family_cfg() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$conf" 2>/dev/null | head -1; }
frontmatter() { sed -n "s/^$2:[[:space:]]*//p" "$1" | head -1; }
body() { awk 'f>=2{print} /^---$/{f++}' "$1"; }

if [ $# -eq 0 ]; then
  for f in a b c; do [ -n "$(family_cfg $f)" ] && set -- "$@" "generalist-$f"; done
fi
[ $# -gt 0 ] || { echo "no reviewers: configure families in $conf" >&2; exit 2; }

run_one() {
  local r=$1 file=$reviewers_dir/$1.md
  local fam cfg cli model tier effort prompt=$out/$r.prompt t0
  fam=$(frontmatter "$file" family); cfg=$(family_cfg "$fam")
  [ -n "$cfg" ] || { echo "$r skipped: family $fam not configured" >> "$out/summary.txt"; return; }
  read -r cli model tier effort <<<"$cfg"; [ "$tier" = - ] && tier=
  local handoff=pack; [ "$cli" = codex ] && handoff=diff
  { "$here/review-handoff.py" "$dir" "$review_base" HEAD "$handoff"; echo; echo "# Task"
    cat "$base"; printf '\nLens: %s\n' "$r"; body "$file"; echo; sed 1,2d "$reviewers_dir/common.md"; } > "$prompt"
  t0=$(date +%s)
  case $cli in
    codex) codex exec --json --skip-git-repo-check -m "$model" -c model_reasoning_effort="${effort:-high}" \
             ${tier:+-c service_tier="\"$tier\""} -s read-only -C "$dir" -o "$out/$r.md" - < "$prompt" \
             > "$out/$r.jsonl" 2> "$out/$r.err" ;;
    grok)  (cd "$dir" && env GROK_CLAUDE_AGENTS_ENABLED=0 GROK_CLAUDE_SKILLS_ENABLED=0 GROK_CLAUDE_RULES_ENABLED=0 \
             GROK_CLAUDE_MCPS_ENABLED=0 GROK_CLAUDE_HOOKS_ENABLED=0 GROK_CURSOR_AGENTS_ENABLED=0 \
             GROK_CURSOR_SKILLS_ENABLED=0 GROK_CURSOR_RULES_ENABLED=0 \
             grok -m "$model" --reasoning-effort "${effort:-high}" --output-format json --always-approve --disable-web-search --prompt-file "$prompt" > "$out/$r.json" 2> "$out/$r.err")
           python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('text',''))" "$out/$r.json" > "$out/$r.md" 2>/dev/null ;;
    kimi)  (cd "$dir" && kimi -m "$model" -p "$(cat "$prompt")" > "$out/$r.md" 2> "$out/$r.err") ;;
    *)     echo "$r skipped: unknown cli $cli" >> "$out/summary.txt"; return ;;
  esac
  echo "$r $cli/$model wall=$(( $(date +%s) - t0 ))s verdict=$(grep -o -m1 'VERDICT: [A-Z_]*' "$out/$r.md" | cut -d' ' -f2)" >> "$out/summary.txt"
}

: > "$out/summary.txt"
"$here/review-panel-models.py" --check >&2 || true   # notice only: newer models available
for r in "$@"; do run_one "$r" & done
wait
[ -n "$(git -C "$dir" status --porcelain)" ] && echo "WARNING: a reviewer modified the checkout" >> "$out/summary.txt"
cat "$out/summary.txt"
