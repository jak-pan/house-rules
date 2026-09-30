#!/usr/bin/env python3
"""Build the review handoff for a change mechanically, so the reviewer starts with the change in context.

  review-handoff.py <checkout> <base> <head> pack|diff|files

pack   changed files with line counts and the functions each hunk touches
diff   pack + the full diff (code with 10 lines of context, tests with 3)
files  pack + every changed non-test file in full at <head> (files over 60 KB: their diff instead)
       + the diff of test files
Lockfiles appear in the file list only.
"""
import re, subprocess, sys

FULL_LIMIT = 60_000
LOCK = re.compile(r"(^|/)([^/]*\.lock|package-lock\.json|pnpm-lock\.yaml|go\.sum)$")  # listed, not inlined
TEST = re.compile(r"(^|/)(tests?/|[^/]*_tests?\.rs$|tests?\.rs$|[^/]*\.test\.[jt]sx?$|test_[^/]*\.py$)")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, text=True).stdout


def pack(repo, rng):
    out = [f"# Review handoff: {rng}", "", "## Changed files (+added/-removed)"]
    for line in git(repo, "diff", "--numstat", rng).splitlines():
        add, rem, path = line.split("\t", 2)
        out.append(f"- {path} (+{add}/-{rem}){' [test]' if TEST.search(path) else ''}")
    out += ["", "## Functions touched (hunk headers)"]
    current, seen = None, set()
    for line in git(repo, "diff", "-U0", rng).splitlines():
        if line.startswith("+++ "):
            current = line[6:]
        elif line.startswith("@@") and current:
            ctx = line.split("@@", 2)[-1].strip()
            if ctx and (current, ctx) not in seen:
                seen.add((current, ctx))
                out.append(f"{current}: {ctx}")
    return "\n".join(out)


def main(repo, base, head, mode):
    rng = f"{base}...{head}"
    names = git(repo, "diff", "--name-only", "--diff-filter=AMR", rng).split()
    code = [n for n in names if not TEST.search(n) and not LOCK.search(n)]
    tests = [n for n in names if TEST.search(n)]
    parts = [pack(repo, rng)]
    if mode == "diff":
        parts += ["## Diff: code", git(repo, "diff", "-U10", rng, "--", *code) if code else "",
                  "## Diff: tests", git(repo, "diff", rng, "--", *tests) if tests else ""]
    elif mode == "files":
        for n in code:
            text = git(repo, "show", f"{head}:{n}")
            if len(text) <= FULL_LIMIT:
                parts.append(f"## File {n} (full, at {head[:12]})\n{text}")
            else:
                parts.append(f"## File {n} (large; diff only)\n{git(repo, 'diff', '-U10', rng, '--', n)}")
        deleted = git(repo, "diff", "--name-only", "--diff-filter=D", rng).split()
        if deleted:
            parts.append("## Deleted files\n" + "\n".join(deleted))
        parts += ["## Diff: tests", git(repo, "diff", rng, "--", *tests) if tests else ""]
    elif mode != "pack":
        sys.exit(__doc__)
    print("\n\n".join(parts))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
