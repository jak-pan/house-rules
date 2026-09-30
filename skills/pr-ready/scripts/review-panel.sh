#!/usr/bin/env bash
# Run a read-only review panel in parallel.
# Usage: review-panel.sh <name> <checkout> <base-prompt> [reviewer ...]
#   name: [A-Za-z0-9][A-Za-z0-9._-]*, a single directory name
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
output_root=${REVIEW_PANEL_OUT:-$dir/.tmp/review-panel}
out=$output_root/$name
family_cfg() { sed -n "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*//p" "$conf" 2>/dev/null | head -1; }
frontmatter() { sed -n "s/^$2:[[:space:]]*//p" "$1" | head -1; }

if [ $# -eq 0 ]; then
  for f in a b c; do [ -n "$(family_cfg $f)" ] && set -- "$@" "generalist-$f"; done
fi
[ $# -gt 0 ] || { echo "no reviewers: configure families in $conf" >&2; exit 2; }

# Validate the whole panel before creating, clearing or writing any output.
# Resolve symlinks as well as '..'; a lexical prefix check is not containment.
python3 - "$reviewers_dir" "$output_root" "$name" "$@" <<'PY' || exit 2
from pathlib import Path
import re
import sys

reviewers_dir, output_root, name, *reviewers = sys.argv[1:]
if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name):
    sys.exit(f"invalid panel name: {name!r}; expected [A-Za-z0-9][A-Za-z0-9._-]*")
if len(reviewers) != len(set(reviewers)):
    sys.exit("duplicate reviewer names are not allowed")
for reviewer in reviewers:
    if not re.fullmatch(r"[a-z0-9-]+", reviewer):
        sys.exit(f"invalid reviewer: {reviewer!r}; expected [a-z0-9-]+")
    if not (Path(reviewers_dir) / f"{reviewer}.md").is_file():
        sys.exit(f"invalid reviewer: {reviewer!r}; no matching reviewer file")

try:
    root = Path(output_root).resolve()
    panel = (root / name).resolve()
    if panel == root or not panel.is_relative_to(root):
        sys.exit(f"refusing panel directory outside output root: {panel}")
    paths = [panel / "summary.txt"]
    paths.extend(panel / f"{reviewer}.{suffix}" for reviewer in reviewers
                 for suffix in ("md", "jsonl", "json", "err", "prepare.err", "prompt"))
    for path in paths:
        resolved = path.resolve()
        if resolved == panel or not resolved.is_relative_to(panel):
            sys.exit(f"refusing cleanup path outside panel directory: {path}")
except (OSError, RuntimeError) as exc:
    sys.exit(f"cannot validate panel cleanup paths: {exc}")
PY
mkdir -p "$out" || exit 1

: > "$out/summary.txt" || exit 1
for r in "$@"; do
  # A reused panel directory must never supply evidence from a previous run.
  if ! rm -f -- "$out/$r.md" "$out/$r.jsonl" "$out/$r.json" \
      "$out/$r.err" "$out/$r.prepare.err" "$out/$r.prompt"; then
    echo "$r failed: clearing previous reviewer outputs" >> "$out/summary.txt"
    exit 1
  fi
done

base_args=(base "$dir")
[ -n "${REVIEW_BASE:-}" ] && base_args+=(--base "$REVIEW_BASE")
resolved_base=$("$here/prepare.py" "${base_args[@]}") || {
  echo "panel failed: base resolution" >> "$out/summary.txt"
  exit 1
}

run_one() {
  local r=$1 file=$reviewers_dir/$1.md
  local fam cfg cli model tier effort prompt=$out/$r.prompt t0 cli_status=0 verdict
  fam=$(frontmatter "$file" family); cfg=$(family_cfg "$fam")
  [ -n "$cfg" ] || { echo "$r failed: family $fam not configured" >> "$out/summary.txt"; return 1; }
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
    *)     echo "$r failed: unknown cli $cli" >> "$out/summary.txt"; return 1 ;;
  esac
  if [ "$cli_status" -ne 0 ]; then
    echo "$r failed: reviewer CLI (exit $cli_status; see $r.err)" >> "$out/summary.txt"
    return 1
  fi
  if ! verdict=$(python3 - "$out/$r.md" 2>> "$out/$r.err" <<'PYVERDICT'
import re
import sys
from pathlib import Path
report = Path(sys.argv[1]).read_text()
# JSON text may concatenate progress and the final verdict on the same line.
# Emphasis may wrap the label, the value, or both; preserve REQUEST_CHANGES.
report = re.sub(r"\*{1,3}|_{1,3}(?![A-Z])|(?<![A-Z])_{1,3}", "", report)
verdicts = re.findall(r"VERDICT:\s*(APPROVE|REQUEST_CHANGES)(?![\w-])", report)
if not verdicts:
    sys.exit(1)
print(verdicts[-1])
PYVERDICT
  ); then
    echo "$r failed: reviewer report missing valid VERDICT: APPROVE or VERDICT: REQUEST_CHANGES token (see $r.md and $r.err)" >> "$out/summary.txt"
    return 1
  fi
  echo "$r $cli/$model wall=$(( $(date +%s) - t0 ))s verdict=$verdict" >> "$out/summary.txt"
}

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
