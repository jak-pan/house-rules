#!/usr/bin/env python3
"""Report or repair House Rules installations; see INSTALL-AGENTS.md §6."""

import argparse
import errno
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
    result = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *args],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def update(root, fix):
    """Never pull dirty, non-default, ahead or diverged checkouts."""
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        return ["checkout is dirty; not pulled"]
    branch = git(root, "branch", "--show-current")
    head = git(root, "rev-parse", "HEAD")
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
    available = subprocess.run(["git", "--no-optional-locks", "-C", str(root), "cat-file", "-e", revision],
                               capture_output=True, text=True)
    if available.returncode:
        if available.returncode != 1:
            raise ValueError(available.stderr.strip())
        return ["remote update available; run --fix to fetch and check ancestry"]
    ahead, behind = map(int, git(root, "rev-list", "--left-right", "--count",
                                f"HEAD...{revision}").split())
    if fix and (git(root, "branch", "--show-current") != branch or
                git(root, "rev-parse", "HEAD") != head or
                git(root, "status", "--porcelain", "--untracked-files=all")):
        return ["checkout changed during fetch; not pulled"]
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
        if present(path) and not path.is_dir():
            raise ValueError(f"{key} default home is not a directory: {path}")
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


def children(path):
    """Enumerate with errors intact on every supported Python version."""
    with os.scandir(path) as entries:
        return sorted(Path(entry.path) for entry in entries)


def copy_entries(path):
    for entry in children(path):
        yield entry
        if not entry.is_symlink() and entry.is_dir():
            yield from copy_entries(entry)


def copy_hash(path):
    """Hash a complete copy, including relative names, types and link targets."""
    digest = hashlib.sha256()
    for entry in sorted(copy_entries(path)):
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
    directory = root / "custom/installations"
    try:
        paths = children(directory)
    except FileNotFoundError:
        if present(directory):
            raise
        paths = []
    # Run receipts are history, never the current ownership inventory.
    for path in paths:
        if path.suffix != ".json" or path.name.startswith("sync-"):
            continue
        receipt = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(receipt, dict):
            raise ValueError(f"receipt must be an object: {path}")
        previous = receipt.get("previous_roots", [])
        copied = receipt.get("copies", {})
        if not isinstance(previous, list) or not isinstance(copied, dict):
            raise ValueError(f"invalid receipt containers: {path}")
        recorded = [receipt.get("source_root", str(root)), *previous]
        if any(not isinstance(value, str) or not Path(value).is_absolute() for value in recorded):
            raise ValueError(f"invalid receipt roots: {path}")
        roots.update(recorded)
        for destination, digest in copied.items():
            if (not isinstance(destination, str) or not Path(destination).is_absolute() or
                    not isinstance(digest, str)):
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


def protected_paths(selected):
    return [(path / "skills/.system").resolve()
            for key, path in selected if key == "CODEX_HOME"]


def check_protected(path, selected):
    resolved = path.resolve()
    if any(resolved == system or system in resolved.parents
           for system in protected_paths(selected)):
        raise ValueError(f"path aliases protected Codex .system content: {path}")


def skill_folders(selected, home):
    """Resolved directory identity is unique; an installation role wins."""
    folders = {}
    for key, product_home in selected:
        locations = ([(product_home / "skills", True)] if key == "CLAUDE_CONFIG_DIR" else
                     [(home / ".agents/skills", True), (product_home / "skills", False)])
        for path, install in locations:
            identity = path.resolve()
            previous = folders.get(identity)
            if previous is None or install and not previous[1]:
                folders[identity] = (path, install)
    return sorted(folders.values())


def precondition(path):
    """Capture entry identity and metadata, including a written symlink target."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return {"parent": str(path.parent.resolve()), "entry": None}
    return {"parent": str(path.parent.resolve()),
            "entry": [info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid,
                      info.st_size, info.st_mtime_ns, info.st_ctime_ns],
            "link": os.readlink(path) if path.is_symlink() else None}


def plan(root, home):
    block = template(root)
    selected = homes(root, home)
    roots, copies = ownership(root)
    skills = {path.name: path for path in sorted((root / "skills").iterdir())
              if path.is_dir() and (path / "SKILL.md").is_file()}
    if ".system" in skills:
        raise ValueError(".system is reserved; cannot install a House Rules skill there")
    actions, conflicts = [], []
    instructions = {instruction_file(key, product_home) for key, product_home in selected}
    for path in (home / "AGENTS.md", home / "CLAUDE.md"):
        if path not in instructions and present(path) and MARKERS.search(
                path.read_bytes().decode("utf-8")):
            conflicts.append(f"duplicate home-level managed block: {path}")
    instruction_targets = {}
    for path in sorted(instructions):
        if path.is_symlink() and not path.is_file():
            conflicts.append(f"instruction symlink has no regular target: {path}")
            continue
        target = path.resolve()
        check_protected(target, selected)
        instruction_targets.setdefault(target, {})[str(path)] = precondition(path)
    for target, aliases in instruction_targets.items():
        before = precondition(target)
        text = target.read_bytes().decode("utf-8") if target.exists() else ""
        markers = list(MARKERS.finditer(text))
        if markers and (len(markers) != 2 or markers[0].group(2) != "begin" or
                        markers[1].group(2) != "end" or
                        markers[0].group(1) != markers[1].group(1)):
            conflicts.append(f"malformed or multiple managed blocks: {target}")
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
                            "content": changed, "before": before, "original": text,
                            "instructions": aliases})
    for folder, install in skill_folders(selected, home):
        check_protected(folder, selected)
        entries = {path.name: path for path in children(folder)} if folder.exists() else {}
        for name in sorted(set(skills) | set(entries)):
            if name == ".system":
                continue
            path = folder / name
            before = precondition(path)
            exists = present(path)
            ours = exists and owned(path, roots, copies)
            if install and name in skills:
                if exists and not ours:
                    conflicts.append(f"same-name skill conflict: {path}")
                elif not path.is_symlink() or os.readlink(path) != str(skills[name]):
                    actions.append({"path": str(path), "kind": "link",
                                    "reason": "missing or stale skill link", "target": str(skills[name]),
                                    "before": before, "copy_hash": copy_hash(path) if
                                    exists and not path.is_symlink() else None})
            elif ours:
                actions.append({"path": str(path), "kind": "remove",
                                "reason": "shadowing skill" if name in skills else "removed skill",
                                "before": before, "copy_hash": copy_hash(path) if
                                not path.is_symlink() else None})
            elif exists and not install and name in skills:
                conflicts.append(f"same-name shadowing conflict: {path}")
    return actions, conflicts, selected, roots, block


def check_action(action, root):
    path = Path(action["path"])
    if precondition(path) != action["before"]:
        raise ValueError(f"destination changed since planning: {path}")
    if action["kind"] == "block":
        for alias, before in action["instructions"].items():
            instruction = Path(alias)
            if precondition(instruction) != before or instruction.resolve() != path:
                raise ValueError(f"instructions changed since planning: {instruction}")
        if (path.read_bytes().decode("utf-8") if present(path) else "") != action["original"]:
            raise ValueError(f"instructions changed since planning: {path}")
    elif present(path):
        roots, copies = ownership(root)
        if not owned(path, roots, copies) or (action["copy_hash"] is not None and
                                             copy_hash(path) != action["copy_hash"]):
            raise ValueError(f"destination ownership changed since planning: {path}")


def check_access(path):
    """Refuse replacement when standard-library metadata cannot preserve ACLs."""
    if os.name == "nt":
        raise ValueError(f"cannot preserve existing file access restrictions on Windows: {path}")
    if sys.platform == "darwin":
        result = subprocess.run(["ls", "-lde", str(path)], check=True,
                                capture_output=True, text=True)
        if re.search(r"^\s*\d+: ", result.stdout, re.M):
            raise ValueError(f"cannot preserve file ACL access restrictions: {path}")
    elif sys.platform.startswith("linux"):
        if "system.posix_acl_access" in os.listxattr(path):
            raise ValueError(f"cannot preserve file ACL access restrictions: {path}")
    else:
        raise ValueError(f"cannot inspect file access restrictions on this platform: {path}")


def atomic_text(path, text, mode=0o600, *, selected=(), before_replace=None, preserve=None):
    check_protected(path, selected)
    check_protected(path.parent, selected)
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".sync-", delete=False) as stream:
            staged = Path(stream.name)
            stream.write(text.encode("utf-8"))
        # The handle must be closed before replacement and cleanup on Windows.
        check_protected(staged, selected)
        if preserve is not None:
            check_access(preserve)
            shutil.copystat(preserve, staged)
            previous, current = preserve.stat(), staged.stat()
            if (previous.st_uid, previous.st_gid) != (current.st_uid, current.st_gid):
                raise ValueError(f"cannot preserve file owner access restrictions: {preserve}")
        os.chmod(staged, mode)
        if before_replace is not None:
            before_replace()
        check_protected(path, selected)
        os.replace(staged, path)
    finally:
        if staged is not None and staged.exists():
            staged.unlink()


def private_backup_run(path, selected, *, create=True):
    check_protected(path, selected)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Windows' chmod cannot verify an owner-only directory ACL.
    if os.name == "nt":
        raise ValueError(f"cannot guarantee backup access restrictions on Windows: {path}")
    if create:
        path.mkdir(mode=0o700)
    check_access(path)
    info = path.lstat()
    if path.is_symlink() or info.st_mode & 0o777 != 0o700 or info.st_uid != os.getuid():
        raise ValueError(f"backup run directory is not owner-only: {path}")


def inventory_path(root, key, home):
    identity = hashlib.sha256(f"{key}\0{home.resolve()}".encode()).hexdigest()
    return root / f"custom/installations/home-{identity}.json"


def repair(root, actions, selected, roots, block):
    run = uuid.uuid4().hex
    receipt_path = root / f"custom/installations/runs/sync-{run}.json"
    backup_run = root / f"custom/backups/sync-{run}"
    for path in (receipt_path, backup_run, root / "custom/INDEX.md",
                 *(inventory_path(root, key, home) for key, home in selected)):
        check_protected(path, selected)
    receipt = {"source_root": str(root), "previous_roots": sorted(roots - {str(root)}),
               "source_revision": git(root, "rev-parse", "HEAD"),
               "homes": [{"product": key, "home": str(path),
                          "instruction_file": str(instruction_file(key, path))}
                         for key, path in selected],
               "managed_block": block, "changes": [], "status": "in progress",
               "runtime_verification": "not run"}

    def save():
        atomic_text(receipt_path, json.dumps(receipt, indent=2) + "\n", selected=selected)

    save()
    backup_ready = False
    try:
        for number, action in enumerate(actions):
            path = Path(action["path"])
            check_action(action, root)
            change = {key: action[key] for key in ("path", "kind", "reason", "target") if key in action}
            change.update(outcome="planned", backup=None)
            receipt["changes"].append(change)
            mode = (path.stat().st_mode & 0o777
                    if action["kind"] == "block" and path.exists() else 0o600)
            if present(path):
                private_backup_run(backup_run, selected, create=not backup_ready)
                backup_ready = True
                backup = backup_run / str(number) / path.name
                check_protected(backup, selected)
                backup.parent.mkdir(parents=True, exist_ok=True)
                if not path.is_dir() or path.is_symlink():
                    shutil.copy2(path, backup, follow_symlinks=False)
                change["backup"] = str(backup)
            else:
                change["previously_absent"] = True
            save()  # Record the backup and intended write before changing the destination.
            check_action(action, root)
            check_protected(path, selected)
            if path.is_dir() and not path.is_symlink():
                try:
                    os.rename(path, change["backup"])
                except OSError as error:
                    if error.errno != errno.EXDEV:
                        raise
                    shutil.copytree(path, change["backup"], symlinks=True)
                    # Copying must finish before the final source check and removal.
                    check_action(action, root)
                    check_protected(path, selected)
                    shutil.rmtree(path)
            if action["kind"] == "block":
                atomic_text(path, action["content"], mode, selected=selected,
                            preserve=path if present(path) else None,
                            before_replace=lambda: check_action(action, root))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                if present(path) and action["kind"] == "remove":
                    check_action(action, root)
                    path.unlink()
                if action["kind"] == "link":
                    staged = path.with_name(f".sync-{run}-{number}")
                    try:
                        check_protected(staged, selected)
                        staged.symlink_to(action["target"], target_is_directory=True)
                        if not change.get("backup") or not action["copy_hash"]:
                            check_action(action, root)
                        elif precondition(path) != {"parent": action["before"]["parent"], "entry": None}:
                            raise ValueError(f"destination changed after copy backup: {path}")
                        check_protected(path, selected)
                        os.replace(staged, path)
                    finally:
                        if staged.is_symlink():
                            staged.unlink()
            change["outcome"] = "fixed"
            save()
        receipt["status"] = "repairs completed; verification pending"
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        receipt["status"] = f"partial failure: {error}"
        raise
    finally:
        save()
        print(f"receipt: {receipt_path}")
    return receipt_path, receipt


def save_inventories(root, selected, roots, block, run_receipt):
    """Publish current per-home ownership; run history never participates in scans."""
    _, copies = ownership(root)
    source_hashes = {path.name: copy_hash(path) for path in children(root / "skills")
                     if path.is_dir() and (path / "SKILL.md").is_file()}
    for key, home in selected:
        instruction = instruction_file(key, home)
        destinations = [{"path": str(instruction), "kind": "instruction",
                         "installed_hash": hashlib.sha256(instruction.read_bytes()).hexdigest()
                         if instruction.is_file() else None}]
        current_copies = {}
        for folder, install in skill_folders([(key, home)], Path.home()):
            entries = {path.name: path for path in children(folder)} if folder.exists() else {}
            names = set(source_hashes) if install else set()
            names.update(name for name, path in entries.items() if owned(path, roots, copies))
            for name in sorted(names):
                path = folder / name
                ours = owned(path, roots, copies)
                digest = None
                if ours and path.is_dir():
                    digest = (source_hashes[name] if name in source_hashes and path.is_symlink() and
                              os.readlink(path) == str(root / "skills" / name)
                              else copy_hash(path))
                if ours and not path.is_symlink():
                    current_copies[str(path)] = digest
                destinations.append({"path": str(path), "kind": "link" if path.is_symlink()
                                     else "copy" if path.is_dir() else "absent or conflict",
                                     "target": os.readlink(path) if path.is_symlink() else None,
                                     "owned": ours, "installed_hash": digest})
        path = inventory_path(root, key, home)
        inventory = {"product": key, "home": str(home), "source_root": str(root),
                     "previous_roots": sorted(roots - {str(root)}),
                     "source_revision": run_receipt["source_revision"],
                     "instruction_file": str(instruction), "managed_block": block,
                     "destinations": destinations, "copies": current_copies,
                     "changes": [change for change in run_receipt["changes"]
                                 if change["path"] == str(instruction.resolve()) or
                                 any(Path(change["path"]).parent.resolve() == folder.resolve()
                                     for folder, _ in skill_folders([(key, home)], Path.home()))],
                     "status": run_receipt["status"],
                     "filesystem_verification": run_receipt["filesystem_verification"],
                     "runtime_verification": "not run"}
        atomic_text(path, json.dumps(inventory, indent=2) + "\n", selected=selected)
    index = root / "custom/INDEX.md"
    check_protected(index, selected)
    before = precondition(index)
    original = index.read_bytes().decode("utf-8") if present(index) else ""
    text = original or "# Machine-local capability index\n"
    begin, end = "<!-- house-rules:receipts:begin -->", "<!-- house-rules:receipts:end -->"
    pointers = [f"- [{path.name}]({path.relative_to(index.parent).as_posix()})"
                for path in children(root / "custom/installations") if path.name.startswith("home-")
                and path.suffix == ".json"]
    section = begin + "\n## House Rules installation receipts\n\n" + "\n".join(pointers) + "\n" + end
    if begin in text or end in text:
        if text.count(begin) != 1 or text.count(end) != 1 or text.index(begin) >= text.index(end):
            raise ValueError(f"malformed installation receipt pointers: {index}")
        text = text[:text.index(begin)] + section + text[text.index(end) + len(end):]
    else:
        text = text.rstrip("\n") + "\n\n" + section + "\n"

    def check_index():
        if precondition(index) != before:
            raise ValueError(f"index changed since reading: {index}")

    if text == original:
        check_index()
        return
    mode = index.stat().st_mode & 0o777 if present(index) else 0o600
    atomic_text(index, text, mode, selected=selected, before_replace=check_index,
                preserve=index if present(index) else None)


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
            try:
                remaining, conflicts, *_ = plan(root, Path.home())
                receipt["status"] = "verified" if not remaining and not conflicts else "verification failed"
                unresolved = [{"path": action["path"], "reason": action["reason"]}
                              for action in remaining]
                receipt["filesystem_verification"] = [*conflicts, *unresolved]
                save_inventories(root, selected, roots, block, receipt)
                if remaining:
                    descriptions = "; ".join(f"{item['reason']}: {item['path']}" for item in unresolved)
                    raise ValueError(f"repairs left unresolved actions: {descriptions}")
                actions = []
            except (OSError, ValueError, subprocess.CalledProcessError) as error:
                receipt["status"] = f"partial failure: {error}"
                raise
            finally:
                atomic_text(receipt_path, json.dumps(receipt, indent=2) + "\n", selected=selected)
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
