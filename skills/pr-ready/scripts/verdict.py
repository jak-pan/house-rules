#!/usr/bin/env python3
"""Read a reviewer report's verdict, failing closed.

Usage: verdict.py <report.md>  → prints APPROVE or REQUEST_CHANGES; exit 1 if no verdict token.

A report can quote verdict strings (from the change under review, a prior round, or an
injected PR comment), and some CLIs glue progress text onto the verdict line, so position
cannot identify the real verdict. The rule is therefore conservative: any REQUEST_CHANGES
token means REQUEST_CHANGES; APPROVE requires every verdict token in the report to agree.
A conflicting report prints REQUEST_CHANGES and says so on stderr.
"""
import re
import sys
from pathlib import Path

TOKEN = re.compile(r"VERDICT:\s*(APPROVE|REQUEST_CHANGES)(?![\w-])")
# Emphasis may wrap the label, the value, or both; keep the underscore in REQUEST_CHANGES.
EMPHASIS = re.compile(r"\*{1,3}|_{1,3}(?![A-Z])|(?<![A-Z])_{1,3}")


def verdict(report: str) -> str | None:
    found = set(TOKEN.findall(EMPHASIS.sub("", report)))
    if not found:
        return None
    return "APPROVE" if found == {"APPROVE"} else "REQUEST_CHANGES"


def main() -> int:
    report = Path(sys.argv[1]).read_text()
    result = verdict(report)
    if result is None:
        return 1
    if result == "REQUEST_CHANGES" and "APPROVE" in set(TOKEN.findall(EMPHASIS.sub("", report))):
        print("conflicting verdict tokens; treated as REQUEST_CHANGES", file=sys.stderr)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
