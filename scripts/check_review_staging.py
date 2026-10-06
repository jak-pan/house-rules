#!/usr/bin/env python3
"""Prepare every role and lens the way the review service does, and fail on any error.

The review service copies only prompts/, rules/ and skills/pr-ready/ from a House Rules commit,
then builds each role prompt and each lens review from that copy. This check copies the same
three folders into an empty directory, compiles every role with prompt.py, and runs
`prepare.py review` for every lens against a small fixture repository. Stdlib and git only.
Usage: check_review_staging.py [--root <house-rules checkout>]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

STAGED = ("prompts", "rules", "skills/pr-ready")
SECTIONS = ("# 1. Review pack", "# 2. Instructions", "# 3. Pull request and issue",
            "# 4. Requirements", "# 5. Change")
GIT_ENV = {"GIT_AUTHOR_NAME": "check", "GIT_AUTHOR_EMAIL": "check@example.invalid",
           "GIT_COMMITTER_NAME": "check", "GIT_COMMITTER_EMAIL": "check@example.invalid"}


def run(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV})


def fixture(path):
    """A repository with one base commit on main and one change on a branch."""
    path.mkdir()
    steps = [(None, ["git", "init", "-q", "-b", "main"]), ("base\n", ["git", "add", "a.txt"]),
             (None, ["git", "commit", "-qm", "base"]), (None, ["git", "checkout", "-q", "-b", "change"]),
             ("base\nchange\n", ["git", "commit", "-qam", "change"])]
    for text, args in steps:
        if text is not None:
            (path / "a.txt").write_text(text)
        result = run(args, path)
        if result.returncode:
            raise RuntimeError(f"fixture: {' '.join(args)}: {result.stderr.strip()}")


def check(root):
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "stage"
        for folder in STAGED:
            shutil.copytree(root / folder, stage / folder)
        scripts = stage / "skills/pr-ready/scripts"
        for role in sorted((stage / "prompts/roles").glob("*.md")):
            result = run([sys.executable, str(scripts / "prompt.py"), f"prompts/roles/{role.name}"], stage)
            if result.returncode or not result.stdout.strip():
                failures.append(f"role {role.stem}: {result.stderr.strip() or 'empty prompt'}")
        repo = Path(tmp) / "fixture"
        fixture(repo)
        lenses = [line.split()[0] for line in (scripts / "review-panel.lenses").read_text().splitlines()
                  if line.strip() and not line.startswith("#")]
        for lens in lenses:
            result = run([sys.executable, str(scripts / "prepare.py"), "review", str(repo), "--base", "main",
                          "--no-fetch", "--lens", lens, "--cli", "codex", "--format", "pack"], stage)
            missing = [s for s in SECTIONS if s not in result.stdout]
            if result.returncode or missing:
                detail = result.stderr.strip().splitlines()[-1:] or [f"missing {', '.join(missing)}"]
                failures.append(f"lens {lens}: {detail[0]}")
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    root = parser.parse_args(argv).root.resolve()
    failures = check(root)
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{'FAILED' if failures else 'OK'}: roles and lenses prepared from {', '.join(STAGED)} only")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
