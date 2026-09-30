#!/usr/bin/env bash
# Classify a GitHub repository as owned or external for the authenticated gh user.
# Owned: the repository owner is the user, or an organization where the user's
# membership is active. A fork is classified by its parent (where PRs land).
# Usage: repo-ownership.sh [owner/name]   (default: this checkout's origin)
# Output: "owned <owner/name>" or "external <owner/name>"; exit 0 owned, 1 external, 2 error.
set -euo pipefail

repo=${1:-}
if [[ -z $repo ]]; then
  url=$(git remote get-url origin) || { echo "no origin remote" >&2; exit 2; }
  repo=$(sed -E 's#^(git@[^:]+:|https?://[^/]+/)##; s#\.git$##' <<<"$url")
fi

target=$(gh api "repos/$repo" --jq 'if .fork then .parent.full_name else .full_name end') \
  || { echo "cannot read $repo" >&2; exit 2; }
owner=${target%%/*}
me=$(gh api user --jq .login)

if [[ $owner == "$me" ]]; then
  echo "owned $target"; exit 0
fi
state=$(gh api "user/memberships/orgs/$owner" --jq .state 2>/dev/null || true)
if [[ $state == active ]]; then
  echo "owned $target"; exit 0
fi
echo "external $target"; exit 1
