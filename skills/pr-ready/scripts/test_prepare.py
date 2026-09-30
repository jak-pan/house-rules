#!/usr/bin/env python3
"""Local integration tests: no network, GitHub writes or model calls."""
import argparse
import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).with_name("prepare.py")
SPEC = importlib.util.spec_from_file_location("prepare", SCRIPT)
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # Ignore host Git aliases, hooks, signing and credentials; all remotes are local.
        self.env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Test Author", "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test Author", "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_TERMINAL_PROMPT": "0",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.origin = self.root / "origin"
        self.origin.mkdir()
        self.git(self.origin, "init", "-b", "trunk")
        self.write(self.origin, "src/core.py", "def action():\n    return 1\n")
        self.commit(self.origin, "Initial")
        self.repo = self.root / "checkout"
        self.git(self.root, "clone", str(self.origin), str(self.repo))
        self.git(self.repo, "checkout", "-b", "feature")

    def git(self, repo, *args):
        return subprocess.run(["git", "-C", str(repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, repo, name, content):
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def commit(self, repo, subject):
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", subject)

    def invoke(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = prepare.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def review(self, **kwargs):
        args = dict(pr=None, issue=None, spec=None, tests=None, lens="generalist-a",
                    summary=None, format=None, cli="codex")
        args.update(kwargs)
        return prepare.review(self.repo, argparse.Namespace(**args), "origin/trunk", "origin")

    def test_remote_default_overrides_stale_local_head_and_is_fetched(self):
        self.git(self.repo, "update-ref", "refs/remotes/origin/main", "HEAD")
        self.git(self.repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
        self.write(self.origin, "upstream.txt", "new upstream\n")
        self.commit(self.origin, "Upstream advances")
        base, remote = prepare.resolve_base(self.repo)
        self.assertEqual((base, remote), ("origin/trunk", "origin"))
        self.assertEqual(self.git(self.repo, "rev-parse", base), self.git(self.origin, "rev-parse", "HEAD"))

    def test_fork_prefers_upstream_and_explicit_base_wins(self):
        upstream = self.root / "upstream"
        self.git(self.root, "clone", str(self.origin), str(upstream))
        self.git(upstream, "branch", "-m", "stable")
        self.git(self.repo, "remote", "add", "upstream", str(upstream))
        self.assertEqual(prepare.resolve_base(self.repo), ("upstream/stable", "upstream"))
        self.assertEqual(prepare.resolve_base(self.repo, "origin/trunk"), ("origin/trunk", "origin"))

    def test_fallback_main_when_remote_head_is_unadvertised(self):
        self.git(self.origin, "branch", "-m", "main")
        bare = self.root / "bare"
        self.git(self.root, "clone", "--bare", str(self.origin), str(bare))
        self.git(bare, "symbolic-ref", "HEAD", "refs/heads/missing")
        self.git(self.repo, "remote", "set-url", "origin", str(bare))
        self.assertEqual(prepare.resolve_base(self.repo), ("origin/main", "origin"))

    def test_local_checkout_without_remote_accepts_explicit_base(self):
        self.git(self.repo, "remote", "remove", "origin")
        self.assertEqual(prepare.resolve_base(self.repo, "HEAD"), ("HEAD", None))
        with self.assertRaisesRegex(prepare.PrepareError, "specify --base"):
            prepare.resolve_base(self.repo)

    def add_review_change(self):
        self.write(self.repo, "src/core.py", "def action():\n    return 2\n")
        self.write(self.repo, "tests/test_core.py", "assert True\n")
        self.write(self.repo, "docs/design.md", "# Design\n## 1 Scope\nOutside content\n## 2 Behavior\nRequired behavior\n### 2.1 Detail\nNested detail\n```python\n# Not a heading\n```\n## 20 Other\nUnselected section\n## Acceptance\n| ID | Requirement |\n| --- | --- |\n| AT1-case | Included row |\n| AT2 | Excluded row |\n")
        self.write(self.repo, "Cargo.lock", "LOCK_ONLY_MARKER\n")
        self.write(self.repo, "odd name.py", "pass\n")
        self.commit(self.repo, "Implement behavior")

    def test_section_order_spec_numbers_acceptance_ids_sort_and_lockfiles(self):
        self.add_review_change()
        prompt = self.review(spec="docs/design.md#2", tests="AT1")
        positions = [prompt.index(f"# {n}. {title}") for n, title in enumerate(
            ["Review pack", "Instructions", "Pull request and issue", "Spec", "Change"], 1)]
        self.assertEqual(positions, sorted(positions))
        spec = prompt[positions[3]:positions[4]]
        self.assertIn("S1. 2 Behavior — docs/design.md:4", spec)
        self.assertIn("##### 2.1 Detail", spec)
        self.assertIn("# Not a heading", spec)
        self.assertIn("| AT1-case | Included row |", spec)
        self.assertNotIn("Excluded row", spec)
        self.assertNotIn("Unselected section", spec)
        files = prepare.changed_files(self.repo, "origin/trunk...HEAD")
        self.assertEqual([prepare.kind(f[2]) for f in files], ["source", "source", "source", "test", "docs"])
        change = prompt[positions[4]:]
        self.assertIn("Cargo.lock — source +1/-0", change)
        self.assertIn("(lockfile: listed only)", change)
        self.assertNotIn("LOCK_ONLY_MARKER", change)
        self.assertIn("odd name.py", change)
        self.assertIn("Implement behavior", prompt)

    def test_diff_has_only_spec_index_pack_has_hunks_and_cli_defaults(self):
        self.add_review_change()
        diff = self.review(spec="docs/design.md#2", format="diff")
        spec = diff.split("# 4. Spec", 1)[1].split("# 5. Change", 1)[0]
        self.assertIn("S1. 2 Behavior", spec)
        self.assertNotIn("Required behavior", spec)
        self.assertIn("```diff", diff)
        pack = self.review(cli="grok")
        self.assertIn("Touched functions (hunk headers)", pack)
        self.assertNotIn("```diff", pack)
        self.assertNotIn("+    return 2", pack)
        self.assertIn("```diff", self.review(cli="kimi", format="structured"))

    def test_pr_design_and_summary_precedence_with_optional_gh(self):
        self.add_review_change()
        summary = self.root / "summary.txt"
        summary.write_text("Round task override")
        pr = {"url": "https://example.invalid/pull/1", "title": "Change title",
              "body": "PR body\nDesign: docs/design.md [§2, §20]\n"}
        with mock.patch.object(prepare, "gh_json", return_value=pr):
            prompt = self.review(pr="1", summary=str(summary), tests="AT1")
        self.assertIn("Round task override", prompt)
        self.assertIn("S2. 20 Other", prompt)
        self.assertIn("Title: Change title", prompt)
        with mock.patch.object(prepare.shutil, "which", return_value=None):
            prompt = self.review(pr="1")
        self.assertIn("Implement behavior", prompt)

    def test_missing_spec_sections_or_tests_fail_visibly(self):
        self.add_review_change()
        with self.assertRaisesRegex(prepare.PrepareError, "expected one heading"):
            self.review(spec="docs/design.md#99")
        with self.assertRaisesRegex(prepare.PrepareError, "acceptance test"):
            self.review(spec="docs/design.md#2", tests="MISSING")

    def test_web_links_use_base_remote_and_head_sha(self):
        head = self.git(self.repo, "rev-parse", "HEAD")
        for remote, route in [("git@github.com:example/project.git", "/blob/"),
                              ("ssh://git@gitlab.com/example/group/project.git", "/-/blob/")]:
            self.git(self.repo, "remote", "set-url", "origin", remote)
            url = prepare.web_remote(self.repo, "origin")
            result = prepare.link(url, head, "src/has space.py", 3)
            self.assertIn(f"{route}{head}/src/has%20space.py#L3", result)
        self.assertEqual(prepare.link(None, head, "src/a.py", 3), "src/a.py:3")

    def test_codex_size_guard_counts_entire_prompt_and_preserves_context(self):
        self.write(self.repo, "large.py", "# " + "x" * 800_001 + "\n")
        self.commit(self.repo, "Large change")
        prompt = self.review()
        self.assertTrue(prompt.startswith("Size guard:"))
        self.assertIn("# 1. Review pack", prompt)
        self.assertIn("Large change", prompt)
        self.assertNotIn("```diff", prompt)
        self.assertIn("Touched functions", prompt)
        # Guard includes task/spec overhead, not just the raw diff size.
        summary = self.root / "summary.txt"
        summary.write_text("s" * 800_001)
        prompt = self.review(summary=str(summary))
        self.assertTrue(prompt.startswith("Size guard:"))
        self.assertIn(summary.read_text(), prompt)

    def test_fix_merge_conflict_stops_and_leaves_merge_in_progress(self):
        self.write(self.repo, "src/core.py", "feature change\n")
        self.commit(self.repo, "Feature")
        self.write(self.origin, "src/core.py", "base change\n")
        self.commit(self.origin, "Base")
        code, out, err = self.invoke("fix", str(self.repo))
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("range: origin/trunk...HEAD", err)
        self.assertIn("merge left in progress", err)
        self.assertIn("src/core.py", err)
        self.git(self.repo, "rev-parse", "--verify", "MERGE_HEAD")

    def test_fix_merges_without_rebasing_and_lists_reviews_without_running_tests(self):
        self.write(self.repo, "tests/test_feature.py", "raise RuntimeError('must not run')\n")
        self.commit(self.repo, "Feature")
        feature = self.git(self.repo, "rev-parse", "HEAD")
        self.write(self.origin, "upstream.py", "pass\n")
        self.commit(self.origin, "Base")
        code, out, err = self.invoke("fix", str(self.repo), "--reviews", "review-a.md", "review-b.md")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD^1"), feature)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD^2"), self.git(self.origin, "rev-parse", "HEAD"))
        self.assertIn("pytest tests/test_feature.py", out)
        self.assertIn("review-a.md\nreview-b.md", out)

    def test_rust_module_and_integration_filters(self):
        for path, content in {
            "Cargo.toml": '[package]\nname="sample"\nversion="0.1.0"\n',
            "src/net/codec.rs": "fn decode() {}\n",
            "src/net/mod.rs": "mod codec;\n",
            "tests/roundtrip.rs": "#[test] fn roundtrip() {}\n",
            "crates/helper/Cargo.toml": '[package]\nname="helper"\nversion="0.1.0"\n',
            "crates/helper/src/parse.rs": "fn parse() {}\n",
        }.items():
            self.write(self.repo, path, content)
        self.commit(self.repo, "Rust change")
        commands, _ = prepare.test_commands(self.repo, prepare.changed_files(self.repo, "origin/trunk...HEAD"))
        self.assertIn("cargo test --release net::codec", commands)
        self.assertIn("cargo test --release net", commands)
        self.assertIn("cargo test --release --test roundtrip", commands)
        self.assertIn("cargo test --release --manifest-path crates/helper/Cargo.toml parse", commands)
        self.assertNotIn("cargo test --release", commands)

    def test_ctest_registered_names_and_pytest_changed_files(self):
        self.write(self.repo, "CMakeLists.txt", 'add_executable(check_codec tests/codec.cpp)\nadd_test(NAME codec.roundtrip COMMAND check_codec "--case=(roundtrip)")\nadd_executable(check_other tests/other.cpp)\nadd_test(NAME other COMMAND check_other)\n')
        self.write(self.repo, "tests/codec.cpp", "int main() {}\n")
        self.write(self.repo, "tests/other.cpp", "int main() {}\n")
        self.commit(self.repo, "Baseline CMake")
        self.git(self.repo, "update-ref", "refs/remotes/origin/trunk", "HEAD")
        self.write(self.repo, "tests/codec.cpp", "int main() { return 0; }\n")
        self.write(self.repo, "tests/test_codec.py", "assert True\n")
        self.commit(self.repo, "Test change")
        commands, _ = prepare.test_commands(self.repo, prepare.changed_files(self.repo, "origin/trunk...HEAD"))
        self.assertIn("ctest -R '^(codec\\.roundtrip)$'", commands)
        self.assertIn("pytest tests/test_codec.py", commands)
        self.assertFalse(any("other" in command for command in commands))

    def test_ctest_registration_can_live_in_a_different_file(self):
        self.write(self.repo, "CMakeLists.txt", "add_test(NAME codec COMMAND check_codec)\n")
        self.write(self.repo, "tests/CMakeLists.txt", "add_executable(check_codec codec.cpp)\n")
        self.write(self.repo, "tests/codec.cpp", "int main() {}\n")
        self.commit(self.repo, "CMake layout")
        self.assertEqual(prepare.cmake_tests(self.repo, ["tests/codec.cpp"]), ["codec"])

    def test_panel_keeps_family_cli_options_and_summary_task(self):
        self.add_review_change()
        binaries = self.root / "bin"
        binaries.mkdir()
        stub = """#!/usr/bin/env python3
import json, os, pathlib, sys
cli = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
if cli == 'codex':
    pathlib.Path(args[args.index('-o') + 1]).write_text('VERDICT: APPROVE')
    assert '# 3. Pull request and issue' in sys.stdin.read()
elif cli == 'grok':
    assert os.environ['GROK_CLAUDE_AGENTS_ENABLED'] == '0'
    assert os.environ['GROK_CURSOR_SKILLS_ENABLED'] == '0'
    assert '--disable-web-search' in args
    print(json.dumps({'text': 'VERDICT: APPROVE'}))
else:
    assert 'Round task from file' in args[args.index('-p') + 1]
    print('VERDICT: APPROVE')
"""
        for cli in ("codex", "grok", "kimi"):
            path = binaries / cli
            path.write_text(stub)
            path.chmod(0o755)
        conf = self.root / "panel.conf"
        conf.write_text("a = codex test-model - high\nb = grok test-model - high\nc = kimi test-model\n")
        summary = self.root / "task.txt"
        summary.write_text("Round task from file")
        output = self.root / "output"
        env = dict(os.environ, PATH=str(binaries) + os.pathsep + os.environ["PATH"],
                   REVIEW_PANEL_CONF=str(conf), REVIEW_PANEL_OUT=str(output), REVIEW_BASE="origin/trunk")
        result = subprocess.run(["bash", str(SCRIPT.with_name("review-panel.sh")), "round",
                                 str(self.repo), str(summary)], capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("verdict=APPROVE"), 3, result.stdout + result.stderr)
        for family in ("a", "b", "c"):
            prompt = (output / "round" / f"generalist-{family}.prompt").read_text()
            self.assertIn("Round task from file", prompt.split("# 3. Pull request and issue")[1])
            self.assertEqual("```diff" in prompt, family == "a")

    def test_pr_brief_works_without_gh_and_classifies_owned_external(self):
        self.write(self.repo, "tests/test_new.py", "assert True\n")
        self.commit(self.repo, "Add regression")
        with mock.patch.object(prepare.shutil, "which", return_value=None):
            code, out, err = self.invoke("pr", str(self.repo))
        self.assertEqual(code, 0, err)
        self.assertIn("## Commits", out)
        self.assertIn("Add regression", out)
        self.assertIn("unknown", out)
        self.assertIn("Nothing is posted without operator approval", out)
        self.git(self.repo, "remote", "set-url", "origin", "https://github.com/example/project.git")
        for status, returncode in [("owned", 0), ("external", 1)]:
            with mock.patch.object(prepare.shutil, "which", return_value="gh"), mock.patch.object(
                prepare, "run", return_value=subprocess.CompletedProcess([], returncode, status + " example/project\n", "")
            ) as run:
                with mock.patch.object(prepare, "web_remote", return_value="https://github.com/example/project"):
                    self.assertEqual(prepare.ownership(self.repo, "origin"), status + " example/project")
                self.assertTrue(run.call_args.args[2].endswith("repo-ownership.sh"))


if __name__ == "__main__":
    unittest.main()
