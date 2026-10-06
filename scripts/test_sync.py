#!/usr/bin/env python3
"""Synthetic homes and local Git remotes; no network or installed-home writes."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts/sync.py"
SPEC = importlib.util.spec_from_file_location("sync", SCRIPT)
sync = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sync)


class SyncTests(unittest.TestCase):
    def setUp(self):
        scratch = REPO / ".tmp"
        scratch.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.env = mock.patch.dict(os.environ, {
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "Test Author", "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test Author", "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "GIT_TERMINAL_PROMPT": "0",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        for variable in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "KIMI_CODE_HOME"):
            os.environ.pop(variable, None)
        self.origin = self.base / "origin"
        self.origin.mkdir()
        self.git(self.origin, "init", "-b", "main")
        self.write(self.origin / ".gitignore", "custom/\n")
        shutil.copyfile(REPO / "INSTALL-AGENTS.md", self.origin / "INSTALL-AGENTS.md")
        self.write(self.origin / "skills/sample/SKILL.md", "# Sample\n")
        self.commit(self.origin, [".gitignore", "INSTALL-AGENTS.md", "skills/sample/SKILL.md"])
        self.root = self.base / "checkout"
        self.git(self.base, "clone", str(self.origin), str(self.root))
        self.home = self.base / "user"
        self.home.mkdir()
        self.claude = self.home / ".claude"
        self.codex = self.home / ".codex"
        self.kimi = self.home / ".kimi-code"
        self.claude.mkdir()
        self.kimi.mkdir()
        self.write(self.codex / "config.toml", "# fixture\n")
        patch = mock.patch.object(Path, "home", return_value=self.home)
        patch.start()
        self.addCleanup(patch.stop)

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, root, paths):
        self.git(root, "add", "--", *paths)
        self.git(root, "commit", "-m", "Fixture change")

    def invoke(self, fix=False):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = sync.main(["--root", str(self.root), *(["--fix"] if fix else [])])
        return code, out.getvalue(), err.getvalue()

    def clean(self):
        code, out, err = self.invoke(True)
        self.assertEqual(code, 0, out + err)
        return out

    def receipt(self, data):
        self.write(self.root / "custom/installations/fixture.json", json.dumps(data))

    def link(self, path, target):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target, target_is_directory=True)

    def test_compaction_wording_is_the_authoritative_template(self):
        self.assertIn("At session start and after every context compaction or reset, read "
                      f"`{self.root}/AGENTS.md`.", sync.template(self.root))

    def test_missing_link_stale_block_missing_block_report_fix_then_clean(self):
        original = "Operator rules\n<!-- house-rules:begin -->\nstale\n<!-- house-rules:end -->\nTail\n"
        self.write(self.claude / "CLAUDE.md", original)
        self.write(self.codex / "AGENTS.md", "Codex rules\n")
        before = sorted(str(path.relative_to(self.home)) for path in self.home.rglob("*"))
        code, out, err = self.invoke()
        self.assertEqual(code, 1, err)
        for reason in ("stale block", "missing block", "missing or stale skill link"):
            self.assertIn(reason, out)
        self.assertFalse((self.root / "custom").exists())
        self.assertEqual(before, sorted(str(path.relative_to(self.home)) for path in self.home.rglob("*")))
        self.assertEqual((self.claude / "CLAUDE.md").read_text(), original)
        self.clean()
        changed = (self.claude / "CLAUDE.md").read_text()
        self.assertTrue(changed.startswith("Operator rules\n"))
        self.assertTrue(changed.endswith("\nTail\n"))
        for folder in (self.claude / "skills", self.home / ".agents/skills"):
            self.assertEqual((folder / "sample").resolve(), self.root / "skills/sample")
        receipts = list((self.root / "custom/installations").glob("*.json"))
        self.assertEqual(len(receipts), 1)
        receipt = json.loads(receipts[0].read_text())
        self.assertEqual(receipt["status"], "verified")
        for change in receipt["changes"]:
            self.assertEqual(change["outcome"], "fixed")
            self.assertTrue(change.get("previously_absent") or Path(change["backup"]).exists())
        self.assertIn(original, [path.read_text() for path in (self.root / "custom/backups").rglob("CLAUDE.md")])
        code, out, err = self.invoke()
        self.assertEqual(code, 0, err)
        self.assertNotIn("REPORT:", out)
        self.assertIn("0 findings", out)
        self.clean()
        self.assertEqual(len(list((self.root / "custom/installations").glob("*.json"))), 2)

    def test_extra_homes_are_only_checked_when_configured(self):
        extra = self.home / "extra codex"
        self.write(extra / "config.toml", "# fixture\n")
        self.clean()
        self.assertFalse((extra / "AGENTS.md").exists())
        self.write(self.root / "custom/sync.env", f'CODEX_HOME="{extra}" # extra\n')
        code, out, err = self.invoke()
        self.assertEqual(code, 1, err)
        self.assertIn(str(extra / "AGENTS.md"), out)
        self.clean()
        self.assertIn(sync.template(self.root), (extra / "AGENTS.md").read_text())
        self.assertEqual(self.invoke()[0], 0)

    def test_extra_claude_and_kimi_homes_and_environment_defaults(self):
        extra_claude, extra_kimi = self.home / "claude extra", self.home / "kimi extra"
        extra_claude.mkdir()
        extra_kimi.mkdir()
        self.write(self.root / "custom/sync.env",
                   f'CLAUDE_CONFIG_DIR="{extra_claude}"\nKIMI_CODE_HOME="{extra_kimi}"\n')
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(extra_claude)}):
            self.clean()
        self.assertTrue((extra_claude / "skills/sample").is_symlink())
        self.assertTrue((extra_kimi / "AGENTS.md").exists())
        self.assertFalse((self.claude / "CLAUDE.md").exists())

    def test_bad_configuration_and_invalid_codex_home_fail_visibly(self):
        for text in ("UNKNOWN=/example\n", 'CODEX_HOME="relative"\n', "CODEX_HOME=$(false)\n"):
            with self.subTest(text=text):
                self.write(self.root / "custom/sync.env", text)
                code, _, err = self.invoke(True)
                self.assertEqual(code, 2)
                self.assertIn("ERROR:", err)
        (self.root / "custom/sync.env").unlink()
        with mock.patch.dict(os.environ, {"CODEX_HOME": str(self.home / "absent")}):
            code, _, err = self.invoke()
            self.assertEqual(code, 2)
            self.assertIn("CODEX_HOME", err)
        (self.codex / "config.toml").unlink()
        self.assertIn("not a Codex home", self.invoke()[2])

    def test_override_and_instruction_symlink_are_preserved(self):
        target = self.home / "instructions.md"
        self.write(target, "Local rules\n")
        (self.codex / "AGENTS.override.md").symlink_to(target)
        self.write(self.codex / "AGENTS.md", "Inactive rules\n")
        self.clean()
        self.assertTrue((self.codex / "AGENTS.override.md").is_symlink())
        self.assertIn(sync.template(self.root), target.read_text())
        self.assertEqual((self.codex / "AGENTS.md").read_text(), "Inactive rules\n")

    def test_legacy_markers_migrate_without_losing_surrounding_bytes(self):
        for family in ("forge", "groundwork"):
            with self.subTest(family=family):
                path = self.claude / "CLAUDE.md"
                self.write(path, f"Before\r\n<!-- {family}:begin -->\r\nold\r\n<!-- {family}:end -->\r\nAfter\r\n")
                path.chmod(0o640)
                self.clean()
                text = path.read_bytes()
                self.assertTrue(text.startswith(b"Before\r\n"))
                self.assertTrue(text.endswith(b"\r\nAfter\r\n"))
                self.assertEqual(path.stat().st_mode & 0o777, 0o640)

    def test_malformed_duplicate_reversed_and_mixed_markers_are_not_changed(self):
        path = self.claude / "CLAUDE.md"
        cases = ["<!-- forge:begin -->", "<!-- forge:end --><!-- forge:begin -->",
                 "<!-- forge:begin --><!-- house-rules:end -->",
                 sync.template(self.root) + sync.template(self.root)]
        for text in cases:
            with self.subTest(text=text):
                self.write(path, text)
                code, out, err = self.invoke(True)
                self.assertNotEqual(code, 0)
                self.assertIn("malformed or multiple", out)
                self.assertEqual(path.read_text(), text)

    def test_owned_removed_and_shadowing_links_are_backed_up_and_removed(self):
        self.clean()
        removed = self.home / ".agents/skills/removed"
        shadow = self.codex / "skills/sample"
        kimi_shadow = self.kimi / "skills/sample"
        self.link(removed, self.root / "skills/removed")
        self.link(shadow, self.root / "skills/sample")
        self.link(kimi_shadow, self.root / "skills/sample")
        system = self.codex / "skills/.system"
        self.write(system / "sample/SKILL.md", "Protected\n")
        self.link(system / "removed", self.root / "skills/removed")
        code, out, _ = self.invoke()
        self.assertEqual(code, 1)
        self.assertIn("removed skill", out)
        self.assertIn("shadowing skill", out)
        self.clean()
        for path in (removed, shadow, kimi_shadow):
            self.assertFalse(sync.present(path))
        self.assertEqual((system / "sample/SKILL.md").read_text(), "Protected\n")
        self.assertTrue((system / "removed").is_symlink())
        self.assertTrue(any(path.is_symlink() for path in (self.root / "custom/backups").rglob("removed")))

    def test_unrelated_files_directories_and_symlinks_are_never_overwritten(self):
        entries = [self.claude / "skills/sample", self.home / ".agents/skills/sample",
                   self.codex / "skills/sample", self.kimi / "skills/sample"]
        self.write(entries[0], "Foreign file\n")
        self.write(entries[1] / "SKILL.md", "Foreign directory\n")
        self.link(entries[2], self.home / "unrelated")
        self.link(entries[3], self.root / "skills/different-name")
        self.clean_conflicts(entries)
        self.assertEqual(entries[0].read_text(), "Foreign file\n")
        self.assertEqual((entries[1] / "SKILL.md").read_text(), "Foreign directory\n")
        self.assertEqual(os.readlink(entries[2]), str(self.home / "unrelated"))
        self.assertEqual(os.readlink(entries[3]), str(self.root / "skills/different-name"))

    def test_written_link_target_determines_ownership(self):
        path = self.claude / "skills/sample"
        target = self.root / "skills/sample"
        self.link(path, os.path.relpath(target, path.parent))
        self.assertEqual(path.resolve(), target)
        self.assertFalse(sync.owned(path, {str(self.root)}, {}))
        self.clean_conflicts([path])

    def test_skill_folder_alias_cannot_write_into_codex_system(self):
        self.clean()
        system = self.codex / "skills/.system"
        self.write(system / "marker", "Protected\n")
        folder = self.claude / "skills"
        folder.rename(self.claude / "original-skills")
        folder.symlink_to(system, target_is_directory=True)
        code, _, err = self.invoke(True)
        self.assertEqual(code, 2)
        self.assertIn("protected", err)
        self.assertFalse(sync.present(system / "sample"))
        self.assertEqual((system / "marker").read_text(), "Protected\n")

    def clean_conflicts(self, entries):
        code, out, err = self.invoke(True)
        self.assertEqual(code, 1, out + err)
        for entry in entries:
            self.assertIn(str(entry), out)
            self.assertTrue(sync.present(entry))

    def test_previous_receipt_root_and_receipt_matched_copies(self):
        old = self.base / "previous-source"
        link = self.claude / "skills/sample"
        removed = self.claude / "skills/removed"
        self.link(link, old / "skills/sample")
        self.link(removed, old / "skills/removed")
        copied = self.home / ".agents/skills/sample"
        self.write(copied / "SKILL.md", "Old owned copy\n")
        self.receipt({"source_root": str(old), "copies": {str(copied): sync.copy_hash(copied)}})
        self.clean()
        self.assertEqual(link.resolve(), self.root / "skills/sample")
        self.assertEqual(copied.resolve(), self.root / "skills/sample")
        self.assertFalse(sync.present(removed))
        copies = [path for path in (self.root / "custom/backups").rglob("sample")
                  if path.is_dir() and not path.is_symlink()]
        self.assertEqual(len(copies), 1)
        self.assertEqual((copies[0] / "SKILL.md").read_text(), "Old owned copy\n")
        self.assertEqual(self.invoke()[0], 0)

    def test_modified_receipt_copy_is_a_conflict(self):
        copied = self.claude / "skills/sample"
        self.write(copied / "SKILL.md", "Owned\n")
        self.receipt({"source_root": str(self.root), "copies": {str(copied): sync.copy_hash(copied)}})
        self.write(copied / "SKILL.md", "Operator changed\n")
        self.clean_conflicts([copied])
        self.assertEqual((copied / "SKILL.md").read_text(), "Operator changed\n")

    def test_partial_failure_is_visible_and_preserves_backup_and_receipt(self):
        self.clean()
        path = self.claude / "CLAUDE.md"
        self.write(path, "Old rules\n")
        real_write = sync.atomic_text

        def write(destination, text, mode=0o600):
            if destination == path:
                raise OSError("fixture write failure")
            return real_write(destination, text, mode)

        with mock.patch.object(sync, "atomic_text", side_effect=write):
            code, out, err = self.invoke(True)
        self.assertEqual(code, 2)
        self.assertIn("fixture write failure", err)
        self.assertIn("receipt:", out)
        self.assertEqual(path.read_text(), "Old rules\n")
        receipts = [json.loads(p.read_text()) for p in (self.root / "custom/installations").glob("*.json")]
        failed = next(r for r in receipts if r["status"].startswith("partial failure:"))
        self.assertEqual(Path(failed["changes"][0]["backup"]).read_text(), "Old rules\n")

    def test_dirty_checkout_is_reported_and_never_pulled(self):
        self.write(self.root / "untracked", "dirty\n")
        for fix in (False, True):
            with self.subTest(fix=fix), mock.patch.object(sync, "git", wraps=sync.git) as calls:
                code, out, _ = self.invoke(fix)
                self.assertEqual(code, 1)
                self.assertIn("dirty", out)
                self.assertFalse(any("pull" in call.args for call in calls.call_args_list))

    def test_diverged_and_ahead_checkouts_are_reported_and_never_pulled(self):
        self.write(self.root / "local", "local\n")
        self.commit(self.root, ["local"])
        self.assertIn("ahead", self.invoke()[1])
        self.write(self.origin / "remote", "remote\n")
        self.commit(self.origin, ["remote"])
        self.git(self.root, "fetch", "origin")
        for fix in (False, True):
            with self.subTest(fix=fix), mock.patch.object(sync, "git", wraps=sync.git) as calls:
                code, out, _ = self.invoke(fix)
                self.assertEqual(code, 1)
                self.assertIn("diverged", out)
                self.assertFalse(any("pull" in call.args for call in calls.call_args_list))

    def test_feature_branch_and_detached_head_are_not_pulled(self):
        self.git(self.root, "checkout", "-b", "work")
        self.assertIn("not main", self.invoke(True)[1])
        self.git(self.root, "checkout", "--detach")
        self.assertIn("detached HEAD", self.invoke(True)[1])

    def test_report_does_not_fetch_or_pull_and_fix_fast_forwards_before_verifying(self):
        self.clean()
        self.write(self.origin / "skills/new/SKILL.md", "# New\n")
        self.commit(self.origin, ["skills/new/SKILL.md"])
        old_head = self.git(self.root, "rev-parse", "HEAD")
        with mock.patch.object(sync, "git", wraps=sync.git) as calls:
            code, out, err = self.invoke()
            self.assertEqual(code, 1, out + err)
            self.assertFalse(any(set(call.args) & {"fetch", "pull"} for call in calls.call_args_list))
        self.assertEqual(old_head, self.git(self.root, "rev-parse", "HEAD"))
        self.clean()
        self.assertEqual(self.git(self.root, "rev-parse", "HEAD"), self.git(self.origin, "rev-parse", "HEAD"))
        self.assertTrue((self.home / ".agents/skills/new").is_symlink())
        self.assertEqual(self.invoke()[0], 0)

    def test_git_failure_reaches_caller(self):
        self.git(self.root, "remote", "set-url", "origin", str(self.base / "absent"))
        code, _, err = self.invoke()
        self.assertEqual(code, 2)
        self.assertIn("ERROR:", err)
        self.assertFalse((self.claude / "CLAUDE.md").exists())


if __name__ == "__main__":
    unittest.main()
