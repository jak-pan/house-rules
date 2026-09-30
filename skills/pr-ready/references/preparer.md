# Review preparer and panel launcher: behaviour reference

Details of `scripts/prepare.py` and `scripts/review-panel.sh`, moved out of the skill so the
loop stays readable. The skill states what to do; this file states exactly how the tools behave.

Give the reviewer the spec sections, previous review and round task as needed
  ([review template](references/review-prompt.md)). `scripts/review-panel.sh` runs
  the base resolver once, then `scripts/prepare.py review --base REF --no-fetch` per
  lens and CLI. Preparation failures, reviewer CLI failures, and reports without a
  `VERDICT: APPROVE` or `VERDICT: REQUEST_CHANGES` token anywhere in the report
  (Markdown emphasis is accepted; `scripts/verdict.py` fails closed: any `REQUEST_CHANGES`
  token means `REQUEST_CHANGES`, and `APPROVE` requires every token to agree)
  are recorded in `summary.txt` and make the panel exit nonzero. Unknown configured CLIs
  fail the reviewer; they are not successful skips. Each run resets `summary.txt` and removes each selected
  reviewer's previous report, raw logs and prompt before base resolution; a base-resolution
  failure is recorded in the new summary. Cleanup failures also make the panel exit nonzero. Before any output changes, panel names must match
  `[A-Za-z0-9][A-Za-z0-9._-]*` and the panel directory must resolve strictly beneath the
  configured output root, including through symlinks. Reviewer names must match
  `[a-z0-9-]+` and an existing file stem in `reviewers/`, with no duplicates. All cleanup
  paths and the summary must resolve beneath the panel directory, including through
  symlinks, or the panel refuses to run. Prompt order: stable rules and lens first, then the
  base-prompt file as summary/task, PR/issue context, requirements and change. Requirements
  are indexed as R1, R2, … with source links, most authoritative first: design/spec
  sections and acceptance-test rows, linked issues (title, labels, body), non-bot
  OWNER/MEMBER/COLLABORATOR comments oldest first, then the PR description (author claims).
  Without a PR or issue, range commit messages supply the task. Standalone use accepts
  `--pr`, repeatable `--issue`, `--spec PATH[#SEC,SEC]`, `--tests ID,ID`,
  `--test-prefix PREFIX` (default `PT`, the acceptance-test ID prefix, e.g. `PT1`)
  and `--summary FILE`. Use the repository's prefix, such as `--test-prefix AT` for `AT1`.
  Section references, ranges
  such as `§3A.2.5–§3A.2.6` (also `-`), and test IDs are collected from PR/issue bodies
  and range commit messages; ranges expand in document order. Inline reference titles
  (`§10.2 Actions` when the words match the heading's leading words, or an explicit
  parenthesized title `§10.2 (Actions)`) are compared with the heading. Trailing prose
  on a bare reference need not match. Title mismatches are reported at the top; the
  section is still included and flagged for verification. Nested ranges include each
  section body only once. Sections selected without a title, including
  range members, are marked in the index and individually at the top as
  "matched by number only; verify" to expose potentially stale numbering. Spec selection is
  limited to `--spec`, then an existing path in a `Design: <path> [§...]` line, then a
  Markdown path named in PR/issue/commit text, then a Markdown design/spec file edited
  by the change. Design lines outrank ordinary mentions across those sources; otherwise
  the first mention wins (PR, issues, then range commits), and edited candidates use
  lexical path order. Named paths match whole path tokens, including paths extracted
  from blob/raw/src URLs, never a suffix of a longer path. Before reading the selected
  document, `git cat-file -s` checks its size against a 2,000,000-byte limit. Oversized
  documents are reported and skipped; unresolved section/test references remain visible.
  Section tokens and test IDs resolve within the selected document. There is no document scoring or content scan. Hyphens are part of
  acceptance IDs: `AT1` does not match `AT1-case`. Linked issues come from PR-body
  `Refs/Closes/Fixes/Resolves #N`, `owner/repo#N`, issue URLs and `--issue`.
  GitHub reads use optional `gh`; unavailable automatic sources and unresolved references
  are reported at the top. An explicitly requested PR or issue that cannot be resolved
  is an error. Deleted maintainer accounts retain their comments with an unknown-author
  notice. Null PR and issue bodies are treated as empty. URL userinfo and credential-like
  query values are redacted from warnings, errors and prompts. A later GitHub read failure names the failed source and preserves already
  fetched context. Comments are capped at 4,000 characters with a cut notice.
  Codex defaults to `structured` (full diffs), others to `pack` (file index and hunk
  headers); `--format diff` omits spec content. `--format` overrides defaults;
  diff reads are bounded before prompt construction, using numstat first and streaming
  hunk headers for pack mode. Changed paths use NUL-delimited metadata and byte-preserving
  decoding, then literal Git pathspecs. Non-UTF-8 bytes are displayed as escapes and
  percent-encoded in links; NUL bytes are displayed as escapes. Size checks measure the
  final displayed prompt, including its terminating newline. Codex prompts over 800,000 characters fall back to pack for the change, then trim comments,
  issue bodies and spec sections in that order (largest first within each source type).
  Notices identify every trim. If the prompt still exceeds the limit after all trim
  steps, preparation exits nonzero without emitting a prompt; the error names the limit,
  final size and completed trims. The panel reports this as a preparation failure.
