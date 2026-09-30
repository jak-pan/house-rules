#!/usr/bin/env python3
"""Prepare local review, fix and PR context. Python stdlib and git; gh is optional."""
import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote, urlsplit

HERE = Path(__file__).resolve().parent
CODEX_LIMIT = 800_000
LOCK = re.compile(r"(^|/)([^/]*\.lock|package-lock\.json|npm-shrinkwrap\.json|pnpm-lock\.yaml|go\.sum)$")
TEST = re.compile(r"(^|/)(tests?(/|\.)|test_[^/]*|[^/]*[_\-.](tests?|spec)\.[^/]+$)", re.I)


class PrepareError(Exception):
    pass


def run(repo, *args):
    return subprocess.run(args, cwd=repo, text=True, encoding="utf-8", errors="replace",
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git(repo, *args):
    result = run(repo, "git", *args)
    if result.returncode:
        raise PrepareError(result.stderr.strip() or "git command failed: " + " ".join(args))
    return result.stdout


def resolve_base(repo, explicit=None, updating=False):
    remotes = git(repo, "remote").splitlines()
    remote = "upstream" if "upstream" in remotes else "origin" if "origin" in remotes else None
    if explicit:
        for candidate in remotes:
            if explicit.startswith(candidate + "/"):
                remote = candidate
                break
        if updating and remote:
            git(repo, "fetch", remote)
        git(repo, "rev-parse", "--verify", explicit + "^{commit}")
        return explicit, remote
    if not remote:
        raise PrepareError("no upstream or origin remote; specify --base REF")
    advertised = run(repo, "git", "ls-remote", "--symref", remote, "HEAD")
    match = re.search(r"^ref: refs/heads/(.+)\s+HEAD$", advertised.stdout, re.M)
    branches = [match[1]] if match else ["main", "master"]
    for branch in branches:
        ref = f"refs/remotes/{remote}/{branch}"
        fetched = run(repo, "git", "fetch", remote, f"refs/heads/{branch}:{ref}")
        if fetched.returncode:
            print(f"warning: fetch {remote}/{branch} failed: {fetched.stderr.strip()}", file=sys.stderr)
            if updating:
                continue
        if run(repo, "git", "rev-parse", "--verify", ref + "^{commit}").returncode == 0:
            if fetched.returncode:
                print("warning: using cached base; freshness could not be verified", file=sys.stderr)
            return f"{remote}/{branch}", remote
    raise PrepareError("cannot fetch/resolve the base; specify --base REF")


def update(repo, base):
    if git(repo, "status", "--porcelain").strip():
        raise PrepareError("checkout is not clean; commit or stash changes before updating")
    git(repo, "symbolic-ref", "--quiet", "HEAD")
    result = run(repo, "git", "merge", "--no-edit", base)
    if result.returncode:
        conflicts = git(repo, "diff", "--name-only", "--diff-filter=U").strip()
        if conflicts:
            raise PrepareError("merge conflict; merge left in progress. Conflicted files:\n" + conflicts)
        raise PrepareError(result.stderr.strip() or result.stdout.strip())
    print(result.stdout.strip(), file=sys.stderr)


def web_remote(repo, remote):
    if not remote:
        return None
    url = git(repo, "remote", "get-url", remote).strip()
    if re.match(r"^[^/@]+@[^:]+:", url):
        url = "https://" + url.split("@", 1)[1].replace(":", "/", 1)
    parsed = urlsplit(url)
    if parsed.hostname not in ("github.com", "gitlab.com"):
        return None
    return "https://" + parsed.hostname + parsed.path.removesuffix(".git").rstrip("/")


def link(url, head, path, line=1):
    label = f"{path}:{line}"
    if not url:
        return label
    route = "/-/blob/" if urlsplit(url).hostname == "gitlab.com" else "/blob/"
    return f"[{label}]({url}{route}{head}/{quote(path, safe='/')}#L{line})"


def kind(path):
    p = Path(path)
    if "docs" in p.parts or p.suffix.lower() in (".md", ".rst", ".txt", ".adoc") and p.name != "CMakeLists.txt":
        return "docs"
    return "test" if TEST.search(path) else "source"


def changed_files(repo, rng):
    # Disabling renames keeps each path unambiguous, including deletions and unusual names.
    records = git(repo, "diff", "--no-renames", "--numstat", "-z", rng).split("\0")
    files = [tuple(record.split("\t", 2)) for record in records if record]
    return sorted(files, key=lambda row: (("source", "test", "docs").index(kind(row[2])), row[2]))


def gh_json(repo, *args):
    if not shutil.which("gh"):
        return {}
    result = run(repo, "gh", *args)
    if result.returncode:
        print("warning: GitHub context unavailable: " + result.stderr.strip(), file=sys.stderr)
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PrepareError("invalid gh JSON: " + str(exc)) from exc


def pr_context(repo, args, url):
    pr = {}
    if args.pr or url and urlsplit(url).hostname == "github.com":
        pr = gh_json(repo, "pr", "view", *([args.pr] if args.pr else []),
                     "--json", "url,title,body")
    issue = gh_json(repo, "issue", "view", args.issue, "--json", "url,title,body") if args.issue else {}
    pr_link = pr.get("url") or args.pr or "(none)"
    if args.pr and args.pr.isdigit() and url and urlsplit(url).hostname == "github.com":
        pr_link = pr.get("url") or f"{url}/pull/{args.pr}"
    return pr, issue, pr_link


def markdown_headings(doc):
    headings, fence = [], None
    for index, line in enumerate(doc.splitlines()):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading and fence is None:
            headings.append((index, len(heading[1]), heading[2]))
    return headings


def spec_sections(doc, wanted):
    lines, headings = doc.splitlines(), markdown_headings(doc)
    if not wanted:
        return [("Full document", 1, doc)]
    result = []
    for want in wanted:
        want = want.strip().lstrip("§").strip()
        matches = [(i, level, title) for i, level, title in headings
                   if title == want or re.match(re.escape(want) + r"(?:[.)]?(?:\s|$))", title)]
        if len(matches) != 1:
            raise PrepareError(f"spec section {want!r}: expected one heading, found {len(matches)}")
        start, level, title = matches[0]
        end = next((i for i, depth, _ in headings if i > start and depth <= level), len(lines))
        result.append((title, start + 1, "\n".join(lines[start + 1:end]).strip()))
    return result


def demote(doc):
    lines = doc.splitlines()
    for i, level, title in markdown_headings(doc):
        lines[i] = "#" * min(6, level + 2) + " " + title
    return "\n".join(lines)


def spec_part(repo, spec, tests, url, head, mode):
    out = ["# 4. Spec", "", "## Index"]
    if not spec:
        if tests:
            raise PrepareError("--tests requires --spec or a PR Design: line")
        return "\n".join(out + ["(No spec supplied.)"])
    path, _, selectors = spec.partition("#")
    doc = git(repo, "show", f"{head}:{path}")
    sections = spec_sections(doc, selectors.split(",") if selectors else [])
    rows = []
    for test in tests:
        matches = [(i, line) for i, line in enumerate(doc.splitlines(), 1)
                   if line.lstrip().startswith("|") and
                   line.strip().split("|")[1].strip().lstrip("`*_ ").startswith(test)]
        if not matches:
            raise PrepareError(f"acceptance test {test!r} not found")
        rows.extend(row for row in matches if row not in rows)
    for n, (title, line, _) in enumerate(sections, 1):
        out.append(f"- S{n}. {title} — {link(url, head, path, line)}")
    if rows:
        out.append(f"- S{len(sections) + 1}. Acceptance tests {', '.join(tests)} — {link(url, head, path, rows[0][0])}")
    if mode != "diff":
        for n, (title, line, body) in enumerate(sections, 1):
            out.extend(["", f"## S{n}. {title} ({path}:{line})", demote(body)])
        if rows:
            out.extend(["", f"## S{len(sections) + 1}. Acceptance tests", *[row for _, row in rows]])
    return "\n".join(out)


def change_part(repo, rng, files, url, head, mode):
    out = ["# 5. Change", f"Range: `{rng}`", "", "## Index"]
    for n, (added, removed, path) in enumerate(files, 1):
        note = " (lockfile: listed only)" if LOCK.search(path) else ""
        out.append(f"- F{n}. {path} — {kind(path)} +{added}/-{removed} — {link(url, head, path)}{note}")
    for n, (_, _, path) in enumerate(files, 1):
        if LOCK.search(path):
            continue
        diff = git(repo, "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
                   "-U0" if mode == "pack" else "-U3" if kind(path) == "test" else "-U10", rng, "--", path).rstrip()
        out.extend(["", f"## F{n}. {path}"])
        if mode == "pack":
            hunks = [line for line in diff.splitlines() if line.startswith("@@")]
            out.extend(["Touched functions (hunk headers):", *(hunks or ["(No textual hunks.)"])])
        else:
            fence = "`" * max(3, max((len(m[0]) + 1 for m in re.finditer(r"`+", diff)), default=3))
            out.extend([fence + "diff", diff, fence])
    return "\n".join(out)


def review(repo, args, base, remote):
    rng, head = f"{base}...HEAD", git(repo, "rev-parse", "HEAD").strip()
    url = web_remote(repo, remote)
    pr, issue, pr_link = pr_context(repo, args, url)
    summary = Path(args.summary).read_text() if args.summary else pr.get("body") or git(repo, "log", "--format=%s", f"{base}..HEAD").strip()
    spec = args.spec
    if spec is None:
        design = re.search(r"^Design:\s+(\S+?)(?:\s+\[([^\]]+)\])?\s*$", pr.get("body", ""), re.M)
        if design:
            spec = design[1] + ("#" + design[2].replace("§", "").replace(" ", "") if design[2] else "")
    lens = args.lens or {"codex": "generalist-a", "grok": "generalist-b", "kimi": "generalist-c"}[args.cli]
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", lens):
        raise PrepareError("invalid lens name")
    reviewers = HERE.parent / "reviewers"
    common = (reviewers / "common.md").read_text().split("\n\n", 1)[-1].strip()
    instructions = (reviewers / (lens + ".md")).read_text()
    instructions = re.sub(r"\A---\n.*?\n---\n", "", instructions, count=1, flags=re.S).strip()
    instructions = instructions.replace("the review bar below", "the review pack in section 1")
    mode = args.format or ("structured" if args.cli == "codex" else "pack")
    parts = ["# 1. Review pack\n" + common, "# 2. Instructions\n" + instructions,
             "\n".join(["# 3. Pull request and issue", f"Pull request: {pr_link}",
                        f"Title: {pr.get('title') or git(repo, 'log', '-1', '--format=%s').strip()}",
                        f"Issue: {issue.get('url') or args.issue or '(none)'}",
                        *([f"Issue title: {issue['title']}", issue.get("body", "")] if issue else []),
                        f"Range: `{rng}`; head: `{head}`", "", summary]),
             spec_part(repo, spec, [t.strip() for t in (args.tests or "").split(",") if t.strip()], url, head, mode)]
    files = changed_files(repo, rng)
    result = "\n\n".join(parts + [change_part(repo, rng, files, url, head, mode)])
    if args.cli == "codex" and len(result) > CODEX_LIMIT and mode != "pack":
        result = "Size guard: prompt exceeds 800,000 characters; change part uses pack (hunk headers).\n\n" + "\n\n".join(parts + [change_part(repo, rng, files, url, head, "pack")])
    return result


def cmake_tests(repo, paths):
    """Resolve literal add_test names through their executable's source list."""
    names, targets, registrations = set(), set(), []
    for file in git(repo, "ls-files", "-z").split("\0"):
        if not file or Path(file).name != "CMakeLists.txt" and not file.endswith(".cmake"):
            continue
        source = (repo / file).read_text(errors="replace")
        source = re.sub(r"^\s*#.*$", "", source, flags=re.M)
        commands = []
        pattern = r'\b(add_executable|add_test)\s*\(((?:"(?:\\.|[^"\\])*"|[^)"])*)\)'
        for match in re.finditer(pattern, source, re.I | re.S):
            try:
                tokens = shlex.split(match[2], comments=True)
            except ValueError as exc:
                raise PrepareError(f"cannot infer CMake tests from {file}: {exc}") from exc
            if tokens:
                commands.append((match[1].lower(), tokens))
        for command, tokens in commands:
            if command == "add_executable" and any((Path(file).parent / t).as_posix() in paths for t in tokens[1:]):
                targets.add(tokens[0])
        registrations.extend((file, tokens) for command, tokens in commands if command == "add_test")
    for file, tokens in registrations:
        name = tokens[1] if tokens[0] == "NAME" and len(tokens) > 1 else tokens[0]
        if "$" in name:
            continue
        referenced = any(t in targets or (Path(file).parent / t).as_posix() in paths for t in tokens)
        if referenced or file in paths:
            names.add(name)
    return sorted(names)


def test_commands(repo, files):
    paths = [path for _, _, path in files if (repo / path).is_file()]
    commands, unresolved = set(), []
    for path in paths:
        p = Path(path)
        if p.suffix == ".rs":
            manifest = next((parent / "Cargo.toml" for parent in (p.parent, *p.parent.parents)
                             if (repo / parent / "Cargo.toml").is_file()), None)
            if manifest:
                rel = p.relative_to(manifest.parent)
                prefix = ["cargo", "test", "--release"]
                if manifest.parent != Path("."):
                    prefix += ["--manifest-path", str(manifest)]
                if rel.parts[0] == "tests" and len(rel.parts) > 1:
                    target = Path(rel.parts[1]).stem
                    # tests/common.rs is a target; tests/common/mod.rs is shared support.
                    if len(rel.parts) > 2 and not (repo / manifest.parent / "tests" / target / "main.rs").is_file():
                        unresolved.append(path)
                        continue
                    commands.add(shlex.join(prefix + ["--test", target]))
                elif rel.parts[0] == "src":
                    modules = list(rel.with_suffix("").parts[1:])
                    if modules and modules[-1] in ("lib", "main", "mod"):
                        modules.pop()
                    if modules:
                        commands.add(shlex.join(prefix + ["::".join(modules)]))
                    else:
                        unresolved.append(path)
                continue
        if kind(path) == "test" and p.suffix == ".py":
            commands.add(shlex.join(["pytest", path]))
        elif kind(path) == "test":
            unresolved.append(path)
    if any(Path(p).name == "CMakeLists.txt" for p in git(repo, "ls-files", "-z").split("\0")):
        names = cmake_tests(repo, paths)
        if names:
            commands.add(shlex.join(["ctest", "-R", "^(" + "|".join(re.escape(n) for n in names) + ")$"]))
        unresolved.extend(p for p in paths if Path(p).suffix in (".c", ".cc", ".cpp", ".h", ".hpp") and p not in unresolved)
    return sorted(commands), sorted(set(unresolved))


def ownership(repo, remote):
    url = web_remote(repo, remote)
    if not shutil.which("gh") or not url or urlsplit(url).hostname != "github.com":
        return "unknown (GitHub ownership unavailable)"
    script = HERE.parent.parent / "upstream-contribution" / "scripts" / "repo-ownership.sh"
    result = run(repo, "bash", str(script), urlsplit(url).path.strip("/"))
    if result.returncode in (0, 1) and result.stdout.strip():
        return result.stdout.strip()
    print("warning: ownership check failed: " + result.stderr.strip(), file=sys.stderr)
    return "unknown (ownership check failed)"


def brief(repo, args, base, remote):
    rng = f"{base}...HEAD"
    files = changed_files(repo, rng)
    out = ["# " + ("Fixer brief" if args.command == "fix" else "PR-preparation brief"), f"Range: `{rng}`"]
    if args.command == "pr":
        out.extend(["\n## Commits", git(repo, "log", "--oneline", f"{base}..HEAD").strip()])
    out.append("\n## Changed files by kind")
    out.extend(f"- {kind(path)}: {path} (+{added}/-{removed})" for added, removed, path in files)
    commands, unresolved = test_commands(repo, files)
    out.extend(["\n## Targeted local gate (commands only; not run)",
                "Run from the checkout; run ctest from its configured build directory.", *commands])
    if unresolved:
        out.extend(["Confirm test targets for these files (static inference is incomplete):", *unresolved])
    if not commands:
        out.append("No targeted commands inferred; use the repository's declared gate and changed tests above.")
    if args.command == "fix":
        out.extend(["\n## Reviews to address", *args.reviews] if args.reviews else ["\n## Reviews to address", "(none supplied)"])
    else:
        status = ownership(repo, remote)
        out.extend(["\n## Ownership", status])
        if not status.startswith("owned "):
            out.append("Upstream-contribution checklist: prove on unmodified upstream; sweep existing work and contribution rules; fix, test and review locally; draft for operator approval. Nothing is posted without operator approval.")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("review", "fix", "pr"):
        p = sub.add_parser(command)
        p.add_argument("checkout", type=Path)
        p.add_argument("--base")
        if command == "review":
            for option in ("pr", "issue", "spec", "tests", "lens", "summary"):
                p.add_argument("--" + option)
            p.add_argument("--format", choices=("structured", "diff", "pack"))
            p.add_argument("--cli", choices=("codex", "grok", "kimi"), default="codex")
        if command == "fix":
            p.add_argument("--reviews", nargs="+", default=[])
    args = parser.parse_args(argv)
    try:
        repo = Path(git(args.checkout, "rev-parse", "--show-toplevel").strip())
        base, remote = resolve_base(repo, args.base, args.command != "review")
        print(f"range: {base}...HEAD", file=sys.stderr)
        if args.command == "review":
            print(review(repo, args, base, remote))
        else:
            update(repo, base)
            print(brief(repo, args, base, remote))
        return 0
    except (PrepareError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
