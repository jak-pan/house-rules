#!/usr/bin/env python3
"""Print a worker or reviewer pack with the shared canon inlined.

Dispatchers prepend the selected pack to worker or reviewer prompts (skill `pr-ready` §1).
"""
import argparse
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "kind", nargs="?", choices=("workers", "reviewers"), default="workers"
    )
    print(pack(parser.parse_args().kind))
