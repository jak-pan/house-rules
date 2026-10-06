#!/usr/bin/env python3
"""Report or repair House Rules installations; see INSTALL-AGENTS.md §6."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
import uuid


MARKERS = re.compile(r"<!-- (house-rules|forge|groundwork):(begin|end) -->")


def present(path):
    return path.exists() or path.is_symlink()


def git(root, *args):
    result = subprocess.run(["git", "-C", str(root), *args],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def update(root, fix):
    """Never pull dirty, non-default, ahead or diverged checkouts."""
    if git(root, "status", "--porcelain"):
        return ["checkout is dirty; not pulled"]
    branch = git(root, "branch", "--show-current")
    remote = git(root, "ls-remote", "--symref", "origin", "HEAD")
    match = re.search(r"^ref: refs/heads/(.+)\s+HEAD$", remote, re.M)
    if not match:
        raise ValueError("origin does not advertise a default branch")
    default = match.group(1)
    if branch != default:
        return [f"checkout is on {branch or 'detached HEAD'}, not {default}; not pulled"]
    revision = remote.splitlines()[-1].split()[0]
    if fix:
        git(root, "fetch", "origin", default)
        revision = git(root, "rev-parse", "FETCH_HEAD")
    available = subprocess.run(["git", "-C", str(root), "cat-file", "-e", revision],
                               capture_output=True, text=True)
    if available.returncode:
        if available.returncode != 1:
            raise ValueError(available.stderr.strip())
        return ["remote update available; run --fix to fetch and check ancestry"]
    ahead, behind = map(int, git(root, "rev-list", "--left-right", "--count",
                                f"HEAD...{revision}").split())
    if ahead:
        return [f"checkout is {'diverged' if behind else 'ahead'}; not pulled"]
    if behind:
        if not fix:
            return ["checkout is behind its default branch; run --fix to update"]
        print(git(root, "pull", "--ff-only", "origin", default))
    return []


def template(root):
    """Derive the adapter from its single authoritative Markdown template."""
    text = (root / "INSTALL-AGENTS.md").read_text(encoding="utf-8")
    match = re.search(r"```markdown\n(.*?)\n\s*```", text, re.S)
    if not match:
        raise ValueError("managed block template is missing")
    block = "\n".join(line.removeprefix("   ") for line in match.group(1).splitlines())
    if not block.startswith("<!-- house-rules:begin -->") or not block.endswith(
            "<!-- house-rules:end -->"):
        raise ValueError("invalid managed block template")
    return block.replace("<HOUSE_RULES_ROOT>", str(root))


def homes(root, home):
    """Select present default homes and explicitly configured extra homes."""
    defaults = {
        "CLAUDE_CONFIG_DIR": Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude")),
        "CODEX_HOME": Path(os.environ.get("CODEX_HOME", home / ".codex")),
        "KIMI_CODE_HOME": Path(os.environ.get("KIMI_CODE_HOME", home / ".kimi-code")),
    }
    selected = []
    for key, path in defaults.items():
        if key in os.environ and (not path.is_absolute() or not path.is_dir()):
            raise ValueError(f"{key} must be an existing absolute directory")
        if path.is_dir():
            selected.append((key, path.absolute()))
    config = root / "custom/sync.env"
    if config.exists():
        for number, line in enumerate(config.read_text(encoding="utf-8").splitlines(), 1):
            tokens = shlex.split(line, comments=True)
            if not tokens:
                continue
            if len(tokens) != 1 or "=" not in tokens[0]:
                raise ValueError(f"{config}:{number}: expected KEY=path")
            key, value = tokens[0].split("=", 1)
            if key not in defaults or not value:
                raise ValueError(f"{config}:{number}: unknown key or empty home")
            path = Path(value).expanduser()
            if not path.is_absolute() or not path.is_dir():
                raise ValueError(f"{config}:{number}: home must be an existing absolute directory")
            selected.append((key, path))
    for key, path in selected:
        if not path.is_absolute():
            raise ValueError(f"{key} must be an absolute directory")
        if key == "CODEX_HOME" and not any((path / name).is_file()
                                           for name in ("config.toml", "auth.json")):
            raise ValueError(f"not a Codex home (no config.toml or auth.json): {path}")
    return list(dict.fromkeys(selected))


def copy_hash(path):
    """Hash a complete copy, including relative names, types and link targets."""
    digest = hashlib.sha256()
    for entry in sorted(path.rglob("*")):
        name = str(entry.relative_to(path))
        if entry.is_symlink():
            kind, value = "link", os.readlink(entry).encode()
        elif entry.is_file():
            kind, value = "file", entry.read_bytes()
        elif entry.is_dir():
            kind, value = "directory", b""
        else:
            raise ValueError(f"unsupported copy entry: {entry}")
        digest.update(json.dumps([name, kind, len(value)]).encode() + b"\0" + value)
    return digest.hexdigest()


def ownership(root):
    roots, copies = {str(root)}, {}
    for path in sorted((root / "custom/installations").glob("*.json")):
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            raise ValueError(f"receipt must be an object: {path}")
        recorded = [receipt.get("source_root", str(root)), *receipt.get("previous_roots", [])]
        if any(not isinstance(value, str) or not Path(value).is_absolute() for value in recorded):
            raise ValueError(f"invalid receipt roots: {path}")
        roots.update(recorded)
        for destination, digest in receipt.get("copies", {}).items():
            if not Path(destination).is_absolute() or not isinstance(digest, str):
                raise ValueError(f"invalid copy ownership: {path}")
            copies.setdefault(destination, set()).add(digest)
    return roots, copies


def owned(path, roots, copies):
    if path.is_symlink():
        target = os.readlink(path)
        # Compare the target as written; do not follow an unrelated alias into ownership.
        return target in {str(Path(root) / "skills" / path.name) for root in roots}
    return (path.is_dir() and str(path) in copies and
            copy_hash(path) in copies[str(path)])


def instruction_file(key, home):
    if key == "CLAUDE_CONFIG_DIR":
        return home / "CLAUDE.md"
    override = home / "AGENTS.override.md"
    return override if key == "CODEX_HOME" and present(override) else home / "AGENTS.md"


def plan(root, home):
    block = template(root)
    selected = homes(root, home)
    protected = [(path / "skills/.system").resolve()
                 for key, path in selected if key == "CODEX_HOME"]

    def check_protected(path):
        resolved = path.resolve()
        if any(resolved == system or system in resolved.parents for system in protected):
            raise ValueError(f"path aliases protected Codex .system content: {path}")

    roots, copies = ownership(root)
    skills = {path.name: path for path in sorted((root / "skills").iterdir())
              if path.is_dir() and (path / "SKILL.md").is_file()}
    if ".system" in skills:
        raise ValueError(".system is reserved; cannot install a House Rules skill there")
    actions, conflicts, folders = [], [], {}
    instructions = set()
    for key, product_home in selected:
        instructions.add(instruction_file(key, product_home))
        if key == "CLAUDE_CONFIG_DIR":
            folders[product_home / "skills"] = True
        else:
            folders[home / ".agents/skills"] = True
            folders.setdefault(product_home / "skills", False)
    for path in sorted(instructions):
        if path.is_symlink() and not path.is_file():
            conflicts.append(f"instruction symlink has no regular target: {path}")
            continue
        target = path.resolve()
        check_protected(target)
        text = target.read_bytes().decode("utf-8") if target.exists() else ""
        markers = list(MARKERS.finditer(text))
        if markers and (len(markers) != 2 or markers[0].group(2) != "begin" or
                        markers[1].group(2) != "end" or
                        markers[0].group(1) != markers[1].group(1)):
            conflicts.append(f"malformed or multiple managed blocks: {path}")
            continue
        if markers:
            start, end = markers[0].start(), markers[1].end()
            changed = text[:start] + block + text[end:]
            reason = "stale block"
        else:
            separator = "\n\n" if text and not text.endswith("\n") else "\n" if text else ""
            changed = text + separator + block + "\n"
            reason = "missing block"
        if changed != text:
            actions.append({"path": str(target), "kind": "block", "reason": reason,
                            "content": changed})
    for folder, install in sorted(folders.items()):
        check_protected(folder)
        entries = {path.name: path for path in folder.iterdir()} if folder.exists() else {}
        for name in sorted(set(skills) | set(entries)):
            if name == ".system":
                continue
            path = folder / name
            exists = present(path)
            ours = exists and owned(path, roots, copies)
            if install and name in skills:
                if exists and not ours:
                    conflicts.append(f"same-name skill conflict: {path}")
                elif not path.is_symlink() or path.resolve() != skills[name].resolve():
                    actions.append({"path": str(path), "kind": "link",
                                    "reason": "missing or stale skill link", "target": str(skills[name])})
            elif ours:
                actions.append({"path": str(path), "kind": "remove",
                                "reason": "shadowing skill" if name in skills else "removed skill"})
            elif exists and not install and name in skills:
                conflicts.append(f"same-name shadowing conflict: {path}")
    return actions, conflicts, selected, roots, block


def atomic_text(path, text, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".sync-", delete=False) as stream:
        staged = Path(stream.name)
        try:
            stream.write(text.encode("utf-8"))
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.replace(staged, path)
        finally:
            if staged.exists():
                staged.unlink()


def repair(root, actions, selected, roots, block):
    run = uuid.uuid4().hex
    receipt_path = root / f"custom/installations/sync-{run}.json"
    receipt = {"source_root": str(root), "previous_roots": sorted(roots - {str(root)}),
               "source_revision": git(root, "rev-parse", "HEAD"),
               "homes": [{"product": key, "home": str(path),
                          "instruction_file": str(instruction_file(key, path))}
                         for key, path in selected],
               "managed_block": block, "changes": [], "status": "in progress",
               "runtime_verification": "not run"}

    def save():
        atomic_text(receipt_path, json.dumps(receipt, indent=2) + "\n")

    save()
    try:
        for number, action in enumerate(actions):
            path = Path(action["path"])
            change = dict(action, outcome="planned", backup=None)
            receipt["changes"].append(change)
            mode = (path.stat().st_mode & 0o777
                    if action["kind"] == "block" and path.exists() else 0o600)
            if present(path):
                backup = root / f"custom/backups/sync-{run}/{number}/{path.name}"
                backup.parent.mkdir(parents=True, exist_ok=True)
                if not path.is_dir() or path.is_symlink():
                    shutil.copy2(path, backup, follow_symlinks=False)
                change["backup"] = str(backup)
            else:
                change["previously_absent"] = True
            save()  # Record the backup and intended write before changing the destination.
            if path.is_dir() and not path.is_symlink():
                # Move receipt-matched copies into the backup instead of deleting them.
                path.rename(Path(change["backup"]))
            if action["kind"] == "block":
                atomic_text(path, action["content"], mode)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                if present(path) and action["kind"] == "remove":
                    path.unlink()
                if action["kind"] == "link":
                    staged = path.with_name(f".sync-{run}-{number}")
                    try:
                        staged.symlink_to(action["target"], target_is_directory=True)
                        os.replace(staged, path)
                    finally:
                        if staged.is_symlink():
                            staged.unlink()
            change["outcome"] = "fixed"
            save()
        receipt["status"] = "repairs completed; verification pending"
    except (OSError, ValueError) as error:
        receipt["status"] = f"partial failure: {error}"
        raise
    finally:
        save()
        print(f"receipt: {receipt_path}")
    return receipt_path, receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root, started = args.root.resolve(), time.monotonic()
    try:
        update_findings = update(root, args.fix)
        actions, conflicts, selected, roots, block = plan(root, Path.home())
        for message in update_findings + conflicts:
            print(f"REPORT: {message}")
        for action in actions:
            print(f"REPORT: {action['reason']}: {action['path']}")
        if args.fix:
            receipt_path, receipt = repair(root, actions, selected, roots, block)
            remaining, conflicts, *_ = plan(root, Path.home())
            receipt["status"] = "verified" if not remaining and not conflicts else "verification failed"
            receipt["filesystem_verification"] = [*conflicts, *remaining]
            atomic_text(receipt_path, json.dumps(receipt, indent=2) + "\n")
            if remaining:
                raise ValueError(f"repairs left unresolved actions: {remaining}")
            actions = []
        findings = len(update_findings) + len(conflicts) + len(actions)
        print(f"{len(selected)} homes checked; {findings} findings; {time.monotonic() - started:.3f}s")
        return 1 if findings else 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stderr, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
