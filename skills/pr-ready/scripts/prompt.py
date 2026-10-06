#!/usr/bin/env python3
"""Expand whole-file @rule includes from this checkout, using only the stdlib."""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
INCLUDE = re.compile(r"@rule house-rules:(.*)")
SHARED_RULES = frozenset(("rules/writing.md", "rules/git.md", "rules/priority-labels.md"))


class PromptError(Exception):
    """An input or included file cannot be expanded."""


def expand(text=None, *, file=None, root=ROOT, session=False):
    """Return expanded text and repository-relative files in depth-first include order.

    Repeated includes are expanded and listed each time. The optional entry file
    is listed first; stdin text has no entry path. No output is written on failure.
    Session builds validate declared shared owners but omit their include contents.
    Role builds and shared-rule declarations state the loading path.
    """
    root = Path(root).resolve()
    used = []
    shared_declared = False

    def visit(name, stack, *, include=False):
        nonlocal shared_declared
        if not name:
            raise PromptError("empty include path at repository root")
        if "\x00" in name:
            raise PromptError("NUL byte in include path")
        if "#" in name:
            raise PromptError(f"section references are not allowed: {name}")
        path = (root / name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(root):
            raise PromptError(f"path outside repository root: {name}")
        if path in stack:
            raise PromptError(f"include cycle: {name}")
        relative = path.relative_to(root).as_posix()
        with path.open(encoding="utf-8", newline="") as source:
            content = source.read()
        if include and relative in SHARED_RULES:
            shared_declared = True
        if session and include and relative in SHARED_RULES:
            return ""
        used.append(relative)
        return render(content, (*stack, path))

    def render(source, stack):
        parts = []
        for line in source.splitlines(keepends=True):
            match = INCLUDE.fullmatch(line.removesuffix("\n").removesuffix("\r"))
            parts.append(visit(match[1], stack, include=True) if match else line)
        return "".join(parts)

    try:
        result = visit(file, ()) if file is not None else render(text, ())
    except (OSError, UnicodeError, RuntimeError) as exc:
        raise PromptError(str(exc)) from exc
    if shared_declared or any(name.startswith("prompts/roles/") for name in used):
        loading = ("session; shared rules come from the live House Rules index."
                   if session else "compiled shared rules; canonical owners are included in this pack.")
        result = f"Loading path: {loading}\n\n" + result
    return result, used


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", help="file relative to the repository root; defaults to stdin")
    parser.add_argument("--list", action="store_true", help="list used paths in include order instead of text")
    parser.add_argument("--session", action="store_true", help="omit shared-rule includes loaded by the session index")
    args = parser.parse_args(argv)
    try:
        text = None if args.file is not None else sys.stdin.buffer.read().decode("utf-8")
        result, used = expand(text, file=args.file, session=args.session)
    except (PromptError, UnicodeError) as exc:
        print("prompt: " + " ".join(str(exc).splitlines()), file=sys.stderr)
        return 2
    output = "".join(path + "\n" for path in used) if args.list else result
    sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
