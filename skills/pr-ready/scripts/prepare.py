#!/usr/bin/env python3
"""Prepare local review, fix and PR context. Python 3.11+ stdlib and git; gh is optional."""
import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import quote, urlsplit

HERE = Path(__file__).resolve().parent
CODEX_LIMIT = 800_000
COMMENT_LIMIT = 4_000
SECTION = r"\d+[A-Za-z]?(?:\.\d+[A-Za-z]?)*"
SECTION_REF = re.compile(r"§\s*(" + SECTION + r")(?:\s*[–-]\s*§?\s*(" + SECTION + r"))?")
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


def resolve_base(repo, explicit=None, no_fetch=False):
    """Return the chosen ref, its remote and whether it is safe to merge."""
    remotes = git(repo, "remote").splitlines()
    remote = "upstream" if "upstream" in remotes else "origin" if "origin" in remotes else None
    if explicit:
        selected = next((r for r in remotes if explicit.startswith((r + "/", "refs/remotes/" + r + "/"))), None)
        git(repo, "rev-parse", "--verify", explicit + "^{commit}")
        if not selected or no_fetch:
            return explicit, selected or remote, not no_fetch
        remote = selected
        branch = explicit.removeprefix("refs/remotes/").removeprefix(remote + "/")
        base = explicit
        advertised_ok = True
    else:
        if not remote:
            raise PrepareError("no upstream or origin remote; specify --base REF")
        if no_fetch:
            raise PrepareError("--no-fetch requires --base REF")
        advertised = run(repo, "git", "ls-remote", "--symref", remote, "HEAD", "refs/heads/main", "refs/heads/master")
        advertised_ok = advertised.returncode == 0
        match = re.search(r"^ref: refs/heads/(.+)\s+HEAD$", advertised.stdout, re.M)
        if not advertised_ok:
            cached = run(repo, "git", "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD")
            if cached.returncode:
                raise PrepareError(f"ls-remote {remote} failed and no cached default branch exists; specify --base REF")
            base = cached.stdout.strip().removeprefix("refs/remotes/")
            git(repo, "rev-parse", "--verify", base + "^{commit}")
            print(f"warning: ls-remote {remote} failed: {advertised.stderr.strip()}; using cached base {base}; freshness could not be verified", file=sys.stderr)
            return base, remote, False
        branch = match[1] if match else next((b for b in ("main", "master")
                                              if re.search(r"\srefs/heads/" + b + r"$", advertised.stdout, re.M)), None)
        if not branch:
            raise PrepareError("remote advertises no default, main or master branch; specify --base REF")
        base = f"{remote}/{branch}"
    ref = f"refs/remotes/{remote}/{branch}"
    fetched = run(repo, "git", "fetch", remote, f"+refs/heads/{branch}:{ref}")
    if fetched.returncode:
        print(f"warning: fetch {base} failed: {fetched.stderr.strip()}", file=sys.stderr)
    git(repo, "rev-parse", "--verify", ref + "^{commit}")
    if fetched.returncode:
        print(f"warning: using cached base {base}; freshness could not be verified", file=sys.stderr)
    return base, remote, advertised_ok and fetched.returncode == 0


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


class GitHubUnavailable(Exception):
    pass


def gh_json(repo, *args):
    try:
        result = subprocess.run(["gh", *args], cwd=repo, text=True, encoding="utf-8",
                                errors="replace", capture_output=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GitHubUnavailable(str(exc)) from exc
    if result.returncode:
        if re.search(r"HTTP 404|no pull requests? found", result.stderr, re.I):
            return None
        raise GitHubUnavailable(result.stderr.strip() or "gh failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubUnavailable("invalid gh JSON: " + str(exc)) from exc


def issue_refs(text):
    # Bare numbers require a linking keyword; qualified references and URLs do not.
    ref = r"https://github\.com/[\w.-]+/[\w.-]+/issues/\d+|[\w.-]+/[\w.-]+#\d+"
    pattern = r"(?:" + ref + r")|\b(?:refs|closes|fixes|resolves)\s+((?:#\d+(?:\s*(?:,\s*(?:and\s+)?|and\s+))?)+)"
    found = []
    for match in re.finditer(pattern, text, re.I):
        found.extend(re.findall(r"#\d+", match[1]) if match[1] else [match[0]])
    return found


def issue_location(ref, url):
    match = re.fullmatch(r"https://github\.com/([\w.-]+/[\w.-]+)/issues/(\d+)/?", ref)
    if not match:
        match = re.fullmatch(r"([\w.-]+/[\w.-]+)#(\d+)", ref)
    if match:
        return match[1], match[2]
    if re.fullmatch(r"#?\d+", ref) and url and urlsplit(url).hostname == "github.com":
        return urlsplit(url).path.strip("/"), ref.lstrip("#")
    return None


def api_comments(repo, endpoint):
    pages = gh_json(repo, "api", "--method", "GET", "--paginate", "--slurp",
                    endpoint + "?per_page=100")
    if pages is None:
        raise GitHubUnavailable("comments not found: " + endpoint)
    return [comment for page in pages for comment in page]


def pr_context(repo, args, url):
    pr, issues, comments, notices, missing = {}, [], [], [], []
    texts = []
    refs = list(args.issue)
    pr_link = args.pr or "(none)"
    if args.pr and args.pr.isdigit() and url:
        pr_link = f"{url}/pull/{args.pr}"
    def unavailable(source, exc):
        notices.append(f"GitHub context unavailable for {source}: {exc}")

    def collect_comments(endpoint):
        try:
            comments.extend(api_comments(repo, endpoint))
        except GitHubUnavailable as exc:
            unavailable(endpoint, exc)

    if not shutil.which("gh"):
        notices.append("GitHub context unavailable; skipped linked issues, maintainer comments and PR description (sources 2–4): gh is not installed")
        missing.extend(ref if not ref.isdigit() else "#" + ref for ref in refs)
    else:
        if args.pr or url and urlsplit(url).hostname == "github.com":
            try:
                pr = gh_json(repo, "pr", "view", *([args.pr] if args.pr else []),
                             "--json", "url,title,body") or {}
            except GitHubUnavailable as exc:
                unavailable("PR description", exc)
            pr_link = pr.get("url") or pr_link
            texts.append(pr.get("body") or "")
        # A PR URL determines where bare issue numbers belong, including forks.
        issue_url = pr.get("url", "").split("/pull/")[0] or url
        refs.extend(issue_refs(pr.get("body", "")))
        seen = set()
        for ref in refs:
            location = issue_location(ref, issue_url)
            if not location or location in seen:
                if not location:
                    missing.append(ref)
                continue
            seen.add(location)
            owner_repo, number = location
            endpoint = f"repos/{owner_repo}/issues/{number}"
            try:
                issue = gh_json(repo, "api", "--method", "GET", endpoint)
            except GitHubUnavailable as exc:
                unavailable(endpoint, exc)
                continue
            if not issue or "pull_request" in issue:
                missing.append(ref if not ref.isdigit() else "#" + ref)
                continue
            issues.append(issue)
            texts.append(issue.get("body") or "")
            collect_comments(endpoint + "/comments")
        if pr.get("url"):
            match = re.fullmatch(r"https://github\.com/([\w.-]+/[\w.-]+)/pull/(\d+)", pr["url"])
            if match:
                owner_repo, number = match.groups()
                for endpoint in (f"issues/{number}/comments", f"pulls/{number}/comments", f"pulls/{number}/reviews"):
                    collect_comments(f"repos/{owner_repo}/{endpoint}")
    comments = [c for c in comments if c.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}
                and c.get("user", {}).get("type", "").lower() != "bot"
                and not c.get("user", {}).get("login", "").lower().endswith("[bot]")
                and c.get("body")]
    comments.sort(key=lambda c: (c.get("created_at") or c.get("submitted_at") or "", c.get("html_url", "")))
    return pr, issues, comments, pr_link, texts, missing, notices


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


def heading_matches(title, want):
    title = title.lstrip("§ ")
    return title == want or bool(re.match(re.escape(want) + r"(?:[.)]?(?:\s|$))", title))


def section_requests(text):
    return [(m[1], m[2]) for m in SECTION_REF.finditer(text)]


def section_titles(text):
    """Collect title candidates; only parentheses make the title explicit."""
    titles = {}
    for match in SECTION_REF.finditer(text):
        tail = text[match.end():]
        parenthesized = re.match(r"[ \t]+\(([^)\n]+)\)", tail)
        bare = re.match(r"[ \t]+([^\n§,;:()\[\]]+)", tail)
        title = parenthesized[1] if parenthesized else bare[1] if bare else ""
        if not parenthesized:
            title = re.split(r"\.(?:\s|$)|\s+[–—]\s+", title)[0].strip()
            # Conjunctions introduce the next reference, not a section title.
            title = re.sub(r"\s+(?:and|or)$", "", title)
            if re.match(r"^(?:and|or|to)\b", title):
                title = ""
        if title.strip():
            titles.setdefault(match[2] or match[1], set()).add((title.strip(), bool(parenthesized)))
    return titles


def normalized_title(title):
    return " ".join(title.strip("`*_ ").casefold().split())


def spec_sections(doc, wanted, missing, titles, notices, path):
    lines, headings = doc.splitlines(), markdown_headings(doc)
    if not wanted:
        return [("Full document", 1, doc, False)]
    # Bare prose is only a title when it shares the heading's leading words.
    # Parentheses explicitly declare a title, so a mismatch is actionable.
    verified = set()
    def prefix(left, right):
        return left == right or right.startswith(left + " ")
    for token, expected in titles.items():
        for n, (_, _, heading) in enumerate(headings):
            if not heading_matches(heading, token):
                continue
            actual = re.sub(r"^§?\s*" + re.escape(token) + r"[.)]?\s*", "", heading)
            leading = re.split(r"\s+[–—]\s+|\s*\(", actual)[0]
            matches, mismatches = [], []
            for title, explicit in sorted(expected):
                want, found = normalized_title(title), normalized_title(leading)
                if prefix(want, found) or (not explicit and prefix(found, want)):
                    matches.append(title)
                elif explicit:
                    mismatches.append(title)
            if matches and not mismatches:
                verified.add(n)
            for title in mismatches:
                notices.append(f"{path} §{token}: title mismatch; expected {title!r}, found {actual!r}; section included; verify.")
    selected = []
    for start, stop in wanted:
        bounds = []
        for token in (start, stop) if stop else (start,):
            matches = [n for n, (_, _, title) in enumerate(headings) if heading_matches(title, token)]
            if len(matches) != 1:
                missing.append("§" + token)
                bounds.append(None)
            else:
                bounds.append(matches[0])
        if stop and all(n is not None for n in bounds):
            if bounds[0] > bounds[1]:
                missing.append(f"§{start}–§{stop} (reversed range)")
            else:
                selected.extend(range(bounds[0], bounds[1] + 1))
        else:
            selected.extend(n for n in bounds if n is not None)
    result = []
    def section_end(n):
        return next((i for i, depth, _ in headings[n + 1:] if depth <= headings[n][1]), len(lines))
    selected = list(dict.fromkeys(selected))
    for n in selected:
        start, _, title = headings[n]
        # A selected ancestor already includes this entire section, even if the
        # child reference appeared first in the source text.
        if any(headings[parent][0] < start < section_end(parent) for parent in selected):
            continue
        body = "\n".join(lines[start + 1:section_end(n)]).strip()
        result.append((title, start + 1, body, n not in verified))
    return result


def discover_spec(repo, head, explicit, texts, files, wanted):
    paths = git(repo, "ls-tree", "-r", "--name-only", "-z", head).split("\0")
    if explicit:
        path = explicit.partition("#")[0]
        return path if path in paths else None
    for text in texts:
        design = re.search(r"^Design:\s+(\S+?)(?:\s+\[[^\]]*\])?\s*$", text, re.M)
        if design and design[1] in paths:
            return design[1]
        # Match repository paths inside ordinary prose, Markdown links and blob URLs.
        named = [(match.start(), path) for path in paths if path.lower().endswith(".md")
                 for match in [re.search(r"(?<![\w.-])" + re.escape(path) + r"(?![\w.-])", text)] if match]
        if named:
            return min(named)[1]
    def priority(path):
        return (0 if any(p in ("design", "spec", "specs") for p in Path(path).parts[:-1]) else 1, path)
    edited = [path for _, _, path in files if path in paths and path.lower().endswith(".md")
              and any(re.search(r"(?:^|[-_.])(design|spec|specs)(?:$|[-_.])", part, re.I)
                      for part in Path(path).parts)]
    if edited:
        return min(edited, key=priority)
    tokens = {token for pair in wanted for token in pair if token}
    scores = []
    for path in sorted((p for p in paths if p.startswith("docs/") and p.lower().endswith(".md")), key=priority):
        headings = markdown_headings(git(repo, "show", f"{head}:{path}"))
        score = sum(any(heading_matches(title, token) for _, _, title in headings) for token in tokens)
        if score:
            scores.append((score, path))
    return max(scores, key=lambda row: row[0])[1] if scores else None


def demote(doc):
    lines = doc.splitlines()
    for i, level, title in markdown_headings(doc):
        lines[i] = "#" * min(6, level + 2) + " " + title
    return "\n".join(lines)


def requirement_entries(repo, args, pr, issues, comments, texts, commits, files, url, head, missing, notices):
    entries = []
    def add(category, source, source_link, body):
        entries.append(dict(category=category, source=source, link=source_link, body=body))
    reference_text = "\n".join([*texts, *(body for _, body in commits)])
    wanted = []
    titles = section_titles(reference_text)
    if args.spec and "#" in args.spec:
        for selector in args.spec.partition("#")[2].split(","):
            selector = selector.strip()
            wanted.extend(section_requests("§" + selector.lstrip("§")) or [(selector, None)])
    wanted = list(dict.fromkeys([*wanted, *section_requests(reference_text)]))
    tests = list(dict.fromkeys([*[t.strip() for t in (args.tests or "").split(",") if t.strip()],
                              *re.findall(r"\b" + re.escape(args.test_prefix) + r"\d+\b", reference_text)]))
    path = discover_spec(repo, head, args.spec, texts, files, wanted)
    doc = None
    if args.spec and not path:
        missing.append(args.spec.partition("#")[0])
    if path:
        result = run(repo, "git", "show", f"{head}:{path}")
        if result.returncode:
            missing.append(path)
        else:
            doc = result.stdout
    if doc is None:
        missing.extend("§" + token for pair in wanted for token in pair if token)
        missing.extend(tests)
    else:
        def source_link(line):
            return link(url, head, path, line) if url else f"[{path}:{line}]({quote(path, safe='/')}#L{line})"
        # With only test references, include just those rows, not the entire document.
        sections = spec_sections(doc, wanted, missing, titles, notices, path) if wanted or not tests else []
        for title, line, body, number_only in sections:
            source = f"Design/spec {path} — {title}"
            if number_only:
                source += " (matched by number only; verify)"
                notices.append(f"{source} — {source_link(line)}")
            add("spec", source, source_link(line), demote(body))
        for test in tests:
            rows = [(n, row) for n, row in enumerate(doc.splitlines(), 1)
                    if row.lstrip().startswith("|") and re.search(r"(?<!\w)" + re.escape(test) + r"(?!\w)", row.split("|")[1])]
            if not rows:
                missing.append(test)
            for line, row in rows:
                add("spec", f"Acceptance test {test} — {path}", source_link(line), row)
    for issue in issues:
        labels = ", ".join(label["name"] for label in issue.get("labels", [])) or "(none)"
        add("issue", f"Issue #{issue['number']}: {issue['title']} (labels: {labels})",
            issue["html_url"], issue.get("body") or "")
    for comment in comments:
        body = comment["body"]
        source = f"Maintainer comment by {comment['user']['login']} ({comment['author_association']})"
        if len(body) > COMMENT_LIMIT:
            notices.append(f"Comment capped at {COMMENT_LIMIT:,} characters: {comment['html_url']}")
            body = body[:COMMENT_LIMIT] + "\n[Comment cut at character cap.]"
        add("comment", source, comment["html_url"], body)
    if pr:
        add("pr", "PR description (author claims): " + pr["title"], pr["url"], pr.get("body") or "")
    if not pr and not issues:
        for sha, body in commits:
            source_link = f"{url}/commit/{sha}" if url else f"[local checkout]({quote(str(repo), safe='/')}) (`git show {sha}`)"
            add("commit", "Commit message " + sha[:12], source_link, body)
    return entries


def requirements_part(entries, mode):
    out = ["# 4. Requirements", "", "## Index"]
    for n, entry in enumerate(entries, 1):
        out.append(f"- R{n}. {entry['source']} — {entry['link']}")
    if not entries:
        out.append("(No requirements found.)")
    for n, entry in enumerate(entries, 1):
        if mode == "diff" and entry["category"] == "spec":
            continue
        out.extend(["", f"## R{n}. {entry['source']}", entry["body"]])
    return "\n".join(out)


class DiffTooLarge(Exception):
    pass


def file_diff(repo, rng, path, mode, budget):
    """Bound every read, including a single enormous source line."""
    command = ["git", "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
               "-U0" if mode == "pack" else "-U3" if kind(path) == "test" else "-U10",
               rng, "--", ":(literal)" + path]
    with tempfile.TemporaryFile() as errors, subprocess.Popen(
        command, cwd=repo, stdout=subprocess.PIPE, stderr=errors
    ) as process:
        try:
            if mode == "pack":
                hunks, size, continuation = [], 0, False
                while chunk := process.stdout.readline(8192):
                    if not continuation and chunk.startswith(b"@@"):
                        header = chunk.decode("utf-8", errors="replace").rstrip()
                        if not chunk.endswith(b"\n"):
                            header += " [Hunk header cut at 8192 bytes.]"
                        size += len(header) + 1
                        if size > budget:
                            raise PrepareError(f"hunk headers exceed the change budget for {path}; narrow the review range")
                        hunks.append(header)
                    continuation = not chunk.endswith(b"\n")
                result = "\n".join(hunks)
            else:
                data = process.stdout.read(max(0, budget) + 1)
                if len(data) > budget:
                    raise DiffTooLarge()
                result = data.decode("utf-8", errors="replace").rstrip()
            if process.wait():
                errors.seek(0)
                raise PrepareError(errors.read().decode("utf-8", errors="replace").strip() or f"git diff failed for {path}")
            return result
        finally:
            # A bounded structured read may stop early before falling back to pack.
            if process.poll() is None:
                process.terminate()
            process.stdout.close()


def change_part(repo, rng, files, url, head, mode, budget=None):
    budget = CODEX_LIMIT if budget is None else max(0, budget)
    if mode != "pack" and sum(int(v) for row in files if not LOCK.search(row[2])
                              for v in row[:2] if v.isdigit()) > budget:
        raise DiffTooLarge()
    out = ["# 5. Change", f"Range: `{rng}`", "", "## Index"]
    for n, (added, removed, path) in enumerate(files, 1):
        note = " (lockfile: listed only)" if LOCK.search(path) else ""
        out.append(f"- F{n}. {path} — {kind(path)} +{added}/-{removed} — {link(url, head, path)}{note}")
    size = sum(len(line) + 1 for line in out)
    for n, (_, _, path) in enumerate(files, 1):
        if LOCK.search(path):
            continue
        diff = file_diff(repo, rng, path, mode, max(0, budget - size))
        header = f"## F{n}. {path}"
        out.extend(["", header])
        if mode == "pack":
            body = ["Touched functions (hunk headers):", diff or "(No textual hunks.)"]
        else:
            fence = "`" * max(3, max((len(m[0]) + 1 for m in re.finditer(r"`+", diff)), default=3))
            body = [fence + "diff", diff, fence]
        out.extend(body)
        size += len(header) + 2 + sum(len(line) + 1 for line in body)
        if mode != "pack" and size > budget:
            raise DiffTooLarge()
    return "\n".join(out)


def review(repo, args, base, remote):
    rng, head = f"{base}...HEAD", git(repo, "rev-parse", "HEAD").strip()
    url = web_remote(repo, remote)
    pr, issues, comments, pr_link, texts, missing, notices = pr_context(repo, args, url)
    log = git(repo, "log", "--reverse", "--format=%H%x00%B%x00", f"{base}..HEAD").split("\0")
    commits = [(log[n].strip(), log[n + 1].strip()) for n in range(0, len(log) - 1, 2)]
    summary = Path(args.summary).read_text() if args.summary else pr.get("title") or "\n".join(body.splitlines()[0] for _, body in commits if body)
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
                        "Issues: " + (", ".join(i["html_url"] for i in issues) or "(none)"),
                        f"Range: `{rng}`; head: `{head}`", "", summary])]
    files = changed_files(repo, rng)
    entries = requirement_entries(repo, args, pr, issues, comments, texts, commits, files, url, head, missing, notices)
    if missing:
        notices.insert(0, "not found: " + ", ".join(dict.fromkeys(missing)))
    # Numstat is already collected; the remaining budget bounds structured reads
    # before constructing a prompt. Pack streams bodies without retaining them.
    overhead = len("\n\n".join([*notices, *parts, requirements_part(entries, mode)])) + 2
    budget = max(0, CODEX_LIMIT - overhead) if args.cli == "codex" else CODEX_LIMIT
    packed = mode == "pack"
    try:
        change = change_part(repo, rng, files, url, head, mode, budget if mode != "pack" else None)
    except DiffTooLarge:
        packed = True
        notices.append(f"Size guard: prompt exceeds {CODEX_LIMIT:,} characters; change part uses pack (hunk headers).")
        change = change_part(repo, rng, files, url, head, "pack")
    trimmed = []
    def render():
        trim_notes = [f"Size guard: trimmed R{n + 1} ({entries[n]['category']}): {entries[n]['source']}" for n in trimmed]
        return "\n\n".join([*notices, *trim_notes, *parts, requirements_part(entries, mode), change])
    result = render()
    if args.cli == "codex" and len(result) > CODEX_LIMIT:
        if not packed:
            notices.append(f"Size guard: prompt exceeds {CODEX_LIMIT:,} characters; change part uses pack (hunk headers).")
            change = change_part(repo, rng, files, url, head, "pack")
            result = render()
        for category in ("comment", "issue", "spec"):
            candidates = sorted((n for n, e in enumerate(entries) if e["category"] == category
                                 and e["body"] and not (mode == "diff" and category == "spec")),
                                key=lambda n: len(entries[n]["body"]), reverse=True)
            for n in candidates:
                if len(result) <= CODEX_LIMIT:
                    break
                trimmed.append(n)
                # Include the trim notice in the budget before retaining a prefix.
                result = render()
                keep = max(0, len(entries[n]["body"]) - (len(result) - CODEX_LIMIT) - 64)
                entries[n]["body"] = entries[n]["body"][:keep] + "\n[Trimmed by size guard.]"
                result = render()
        if len(result) > CODEX_LIMIT:
            notices.append(f"Size guard: still exceeds {CODEX_LIMIT:,} characters after trimming; retained indexes, rules, task and author claims require a smaller input.")
            result = render()
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
                elif rel.as_posix() == "src/main.rs" or rel.parts[:2] == ("src", "bin"):
                    with (repo / manifest).open("rb") as source:
                        metadata = tomllib.load(source)
                    configured = next((target.get("name") for target in metadata.get("bin", [])
                                       if target.get("path") == rel.as_posix()), None)
                    target = configured or (metadata.get("package", {}).get("name") if rel.as_posix() == "src/main.rs"
                                            else Path(rel.parts[2]).stem if len(rel.parts) == 3
                                            else rel.parts[2] if len(rel.parts) >= 4 else None)
                    if target:
                        commands.add(shlex.join(prefix + ["--bin", target]))
                    else:
                        unresolved.append(path)
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


def brief(repo, args, base, status, update_note):
    rng = f"{base}...HEAD"
    files = changed_files(repo, rng)
    out = ["# " + ("Fixer brief" if args.command == "fix" else "PR-preparation brief"), f"Range: `{rng}`"]
    out.extend(["\n## Branch update", update_note])
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
        out.extend(["\n## Ownership", status])
        if not status.startswith("owned "):
            out.append("Upstream-contribution checklist: prove on unmodified upstream; sweep existing work and contribution rules; fix, test and review locally; draft for operator approval. Nothing is posted without operator approval.")
    return "\n".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("review", "fix", "pr", "base"):
        p = sub.add_parser(command)
        p.add_argument("checkout", type=Path)
        p.add_argument("--base")
        p.add_argument("--no-fetch", action="store_true", help="use an already resolved --base without fetching")
        if command == "review":
            for option in ("pr", "spec", "tests", "lens", "summary"):
                p.add_argument("--" + option)
            p.add_argument("--issue", action="append", default=[])
            p.add_argument("--test-prefix", default="PT")
            p.add_argument("--format", choices=("structured", "diff", "pack"))
            p.add_argument("--cli", choices=("codex", "grok", "kimi"), default="codex")
        if command == "fix":
            p.add_argument("--reviews", nargs="+", default=[])
        if command in ("fix", "pr"):
            p.add_argument("--update", action="store_true", help="merge the base even on external repositories")
    args = parser.parse_args(argv)
    try:
        repo = Path(git(args.checkout, "rev-parse", "--show-toplevel").strip())
        base, remote, fresh = resolve_base(repo, args.base, args.no_fetch)
        print(f"range: {base}...HEAD", file=sys.stderr)
        if args.command == "base":
            print(base)
        elif args.command == "review":
            print(review(repo, args, base, remote))
        else:
            status = ownership(repo, remote)
            if not fresh:
                behind = git(repo, "rev-list", "--count", f"HEAD..{base}").strip()
                update_note = f"{behind} commit(s) behind cached base {base}. Base merge skipped; freshness could not be verified."
            elif status.startswith("external ") and not args.update:
                behind = git(repo, "rev-list", "--count", f"HEAD..{base}").strip()
                update_note = (f"{status}: {behind} commit(s) behind {base}. Base merge skipped; "
                               "leave the update method to the operator's instruction. --update forces a base merge.")
            else:
                update(repo, base)
                update_note = f"Merged {base} (or already up to date)."
            print(brief(repo, args, base, status, update_note))
        return 0
    except (PrepareError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
