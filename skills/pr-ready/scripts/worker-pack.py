#!/usr/bin/env python3
"""Print the worker pack: workers/common.md with the shared canon inlined.

Dispatchers prepend this to every implementer and fixer prompt (skill `pr-ready` §1).
"""
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def pack(kind: str = "workers") -> str:
    """Return `<kind>/common.md` without its title line, with {{CANON}} replaced."""
    common = (SKILL / kind / "common.md").read_text().split("\n\n", 1)[-1].strip()
    canon = (SKILL / "canon.md").read_text().split("\n\n", 1)[-1].strip()
    if "{{CANON}}" not in common:
        raise SystemExit(f"{kind}/common.md lacks the {{{{CANON}}}} line")
    return common.replace("{{CANON}}", canon)


if __name__ == "__main__":
    print(pack())
