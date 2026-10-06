#!/usr/bin/env python3
"""Synthetic homes and local Git remotes; no network or installed-home writes."""

import contextlib
import errno
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
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
        self.tmp = tempfile.TemporaryDirectory(prefix="house-rules-sync-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
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
        receipts = list((self.root / "custom/installations/runs").glob("sync-*.json"))
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
        self.assertEqual(len(list((self.root / "custom/installations/runs").glob("sync-*.json"))), 2)

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

    def test_shared_instruction_target_is_fixed_once_and_skill_repairs_complete(self):
        target = self.codex / "AGENTS.md"
        alias = self.kimi / "AGENTS.md"
        self.write(target, "Shared operator rules\n")
        alias.symlink_to(target)
        actions, *_ = sync.plan(self.root, self.home)
        self.assertEqual(len([action for action in actions if action["kind"] == "block"
                              and action["path"] == str(target)]), 1)
        self.clean()
        self.assertTrue(alias.is_symlink())
        self.assertEqual(target.read_text(), "Shared operator rules\n\n" +
                         sync.template(self.root) + "\n")
        for folder in (self.claude / "skills", self.home / ".agents/skills"):
            self.assertEqual((folder / "sample").resolve(), self.root / "skills/sample")
        for key, home, instruction in (("CODEX_HOME", self.codex, target),
                                       ("KIMI_CODE_HOME", self.kimi, alias)):
            inventory = json.loads(sync.inventory_path(self.root, key, home).read_text())
            self.assertEqual(inventory["instruction_file"], str(instruction))
            self.assertEqual(inventory["status"], "verified")
            changes = [change for change in inventory["changes"] if change["kind"] == "block"]
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0]["path"], str(target))
        self.assertEqual(self.invoke()[0], 0)

    def test_shared_instruction_alias_drift_is_refused(self):
        target = self.codex / "AGENTS.md"
        alias = self.kimi / "AGENTS.md"
        foreign = self.home / "foreign.md"
        self.write(target, "Shared operator rules\n")
        self.write(foreign, "Foreign rules\n")
        alias.symlink_to(target)
        real_plan = sync.plan

        def changed_plan(*args):
            result = real_plan(*args)
            alias.unlink()
            alias.symlink_to(foreign)
            return result

        with mock.patch.object(sync, "plan", side_effect=changed_plan):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertIn("changed since planning", err)
        self.assertEqual(target.read_text(), "Shared operator rules\n")
        self.assertEqual(foreign.read_text(), "Foreign rules\n")

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

        def write(destination, text, mode=0o600, **kwargs):
            if destination == path:
                raise OSError("fixture write failure")
            return real_write(destination, text, mode, **kwargs)

        with mock.patch.object(sync, "atomic_text", side_effect=write):
            code, out, err = self.invoke(True)
        self.assertEqual(code, 2)
        self.assertIn("fixture write failure", err)
        self.assertIn("receipt:", out)
        self.assertEqual(path.read_text(), "Old rules\n")
        receipts = [json.loads(p.read_text()) for p in (self.root / "custom/installations/runs").glob("sync-*.json")]
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


    def test_fix_now_01_refuses_instruction_and_skill_drift(self):
        path = self.claude / "CLAUDE.md"
        self.write(path, "Before\n")
        real_plan = sync.plan

        def changed_plan(*args):
            result = real_plan(*args)
            self.write(path, "New operator edit\n")
            return result

        with mock.patch.object(sync, "plan", side_effect=changed_plan):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertEqual(path.read_text(), "New operator edit\n")
        self.assertIn("changed", err)

        self.clean()
        link = self.claude / "skills/sample"
        link.unlink()
        self.link(link, self.root / "skills/removed")
        # An owned stale same-name link uses a recorded old root.
        old = self.base / "old"
        link.unlink()
        self.link(link, old / "skills/sample")
        self.receipt({"source_root": str(old)})

        def changed_link_plan(*args):
            result = real_plan(*args)
            link.unlink()
            self.link(link, self.home / "foreign")
            return result

        with mock.patch.object(sync, "plan", side_effect=changed_link_plan):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertEqual(os.readlink(link), str(self.home / "foreign"))

    def test_fix_now_01_refuses_instruction_edit_during_backup(self):
        path = self.claude / "CLAUDE.md"
        self.write(path, "Before\n")
        real_copy = shutil.copy2

        def copy(source, destination, **kwargs):
            result = real_copy(source, destination, **kwargs)
            if source == path:
                self.write(path, "Edited during backup\n")
            return result

        with mock.patch.object(shutil, "copy2", side_effect=copy):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertEqual(path.read_text(), "Edited during backup\n")

    def test_fix_now_01_refuses_instruction_edit_during_staging(self):
        path = self.claude / "CLAUDE.md"
        self.write(path, "Before\n")
        real_temporary = tempfile.NamedTemporaryFile

        def temporary(**kwargs):
            stream = real_temporary(**kwargs)
            real_write = stream.write

            def write(data):
                if Path(kwargs["dir"]) == path.parent:
                    self.write(path, "Edited during staging\n")
                return real_write(data)

            stream.write = write
            return stream

        with mock.patch.object(tempfile, "NamedTemporaryFile", side_effect=temporary):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertEqual(path.read_text(), "Edited during staging\n")

    def test_fix_now_01_refuses_revoked_copy_ownership(self):
        path = self.claude / "skills/sample"
        self.write(path / "SKILL.md", "Owned fixture\n")
        self.receipt({"copies": {str(path): sync.copy_hash(path)}})
        real_plan = sync.plan

        def plan(*args):
            result = real_plan(*args)
            self.receipt({"copies": {}})
            return result

        with mock.patch.object(sync, "plan", side_effect=plan):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertEqual((path / "SKILL.md").read_text(), "Owned fixture\n")
        self.assertFalse(path.is_symlink())

    def test_fix_now_02_aliased_skill_folders_keep_installation(self):
        self.clean()
        self.link(self.codex / "skills", self.home / ".agents/skills")
        code, out, err = self.invoke(True)
        self.assertEqual(code, 0, out + err)
        self.assertTrue((self.home / ".agents/skills/sample").is_symlink())

    def test_fix_now_03_backups_are_owner_only_under_permissive_umask(self):
        self.claude.chmod(0o700)
        self.write(self.claude / "CLAUDE.md", "Private fixture\n")
        before = os.umask(0)
        try:
            self.clean()
        finally:
            os.umask(before)
        runs = list((self.root / "custom/backups").iterdir())
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].stat().st_mode & 0o777, 0o700)

    def test_fix_now_04_acl_replacement_is_refused_without_widening_access(self):
        path = self.claude / "CLAUDE.md"
        self.write(path, "Restricted\n")
        if sys.platform == "darwin":
            acl = "everyone deny execute"
            subprocess.run(["chmod", "+a", acl, str(path)], check=True)
            self.addCleanup(subprocess.run, ["chmod", "-N", str(path)], check=True)
            code, _, err = self.invoke(True)
        else:
            # Native ACL inspection is covered above on macOS; exercise refusal
            # on platforms where the standard library cannot preserve file ACLs.
            with mock.patch.object(sync.sys, "platform", "win32"):
                code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertEqual(path.read_text(), "Restricted\n")
        self.assertIn("access restrictions", err)

    def test_fix_now_05_verification_error_does_not_print_instruction_bytes(self):
        real_plan = sync.plan
        count = 0
        private = "PRIVATE-FIXTURE-TEXT"

        def drift(*args):
            nonlocal count
            count += 1
            if count == 2:
                self.write(self.claude / "CLAUDE.md", private)
            return real_plan(*args)

        with mock.patch.object(sync, "plan", side_effect=drift):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2)
        self.assertNotIn(private, err)
        self.assertIn(str(self.claude / "CLAUDE.md"), err)
        self.assertIn("missing block", err)

    def test_fix_now_06_auxiliary_destinations_cannot_alias_system(self):
        for name in ("installations", "backups", "INDEX.md"):
            with self.subTest(name=name):
                system = self.codex / "skills/.system"
                system.mkdir(parents=True, exist_ok=True)
                custom = self.root / "custom"
                custom.mkdir(exist_ok=True)
                alias = custom / name
                self.link(alias, system)
                code, _, err = self.invoke(True)
                self.assertEqual(code, 2, err)
                self.assertIn("protected", err)
                self.assertEqual(list(system.iterdir()), [])
                alias.unlink()

    def test_fix_now_07_scan_failures_reach_caller(self):
        folder = self.root / "custom/installations"
        folder.mkdir(parents=True)
        real_scan = os.scandir

        def scan(path):
            if Path(path) == folder:
                raise PermissionError("unreadable receipts")
            return real_scan(path)

        with mock.patch.object(os, "scandir", side_effect=scan):
            with self.assertRaises(PermissionError):
                sync.ownership(self.root)

    def test_fix_now_07_unreadable_copy_subtree_reaches_caller(self):
        copied = self.base / "copied"
        self.write(copied / "nested/SKILL.md", "fixture")
        real_scan = os.scandir

        def scan_copy(path):
            if Path(path) == copied / "nested":
                raise PermissionError("unreadable subtree")
            return real_scan(path)

        with mock.patch.object(os, "scandir", side_effect=scan_copy):
            with self.assertRaises(PermissionError):
                sync.copy_hash(copied)

    def test_fix_now_08_atomic_writer_closes_before_replace_or_cleanup(self):
        real_temp = tempfile.NamedTemporaryFile
        streams = []
        real_replace = os.replace
        real_unlink = Path.unlink

        def temporary(**kwargs):
            stream = real_temp(**kwargs)
            streams.append(stream)
            return stream

        def replace(source, destination):
            self.assertTrue(streams[-1].closed)
            return real_replace(source, destination)

        def unlink(path, *args, **kwargs):
            if path.name.startswith(".sync-"):
                self.assertTrue(streams[-1].closed)
            return real_unlink(path, *args, **kwargs)

        path = self.base / "atomic"
        with mock.patch.object(tempfile, "NamedTemporaryFile", side_effect=temporary), \
                mock.patch.object(os, "fchmod", side_effect=AttributeError("Windows has no fchmod")), \
                mock.patch.object(os, "replace", side_effect=replace), \
                mock.patch.object(Path, "unlink", autospec=True, side_effect=unlink):
            sync.atomic_text(path, "fixture")
            self.assertEqual(path.read_text(), "fixture")
            with mock.patch.object(os, "replace", side_effect=OSError("replacement failed")):
                with self.assertRaisesRegex(OSError, "replacement failed"):
                    sync.atomic_text(path, "next")
        self.assertFalse(list(self.base.glob(".sync-*")))
        self.assertIn("Python 3.9 or later", (REPO / "INSTALL-AGENTS.md").read_text())

    def test_fix_now_09_owned_copy_moves_across_filesystems(self):
        copied = self.claude / "skills/sample"
        self.write(copied / "SKILL.md", "Owned copy\n")
        self.receipt({"copies": {str(copied): sync.copy_hash(copied)}})
        real_rename = os.rename

        def rename(source, destination, *args, **kwargs):
            if Path(source) == copied:
                raise OSError(errno.EXDEV, "cross-device fixture")
            return real_rename(source, destination, *args, **kwargs)

        with mock.patch.object(os, "rename", side_effect=rename):
            self.clean()
        self.assertTrue(copied.is_symlink())
        backups = list((self.root / "custom/backups").rglob("SKILL.md"))
        self.assertEqual([path.read_text() for path in backups], ["Owned copy\n"])

    def test_cross_filesystem_backup_preserves_edits_before_source_removal(self):
        for name in ("sample", "removed"):
            with self.subTest(name=name):
                copied = self.claude / "skills" / name
                self.write(copied / "SKILL.md", "Original owned copy\n")
                self.receipt({"copies": {str(copied): sync.copy_hash(copied)}})
                real_rename, real_copytree = os.rename, shutil.copytree

                def rename(source, destination, *args, **kwargs):
                    if Path(source) == copied:
                        raise OSError(errno.EXDEV, "cross-device fixture")
                    return real_rename(source, destination, *args, **kwargs)

                def copytree(source, destination, *args, **kwargs):
                    result = real_copytree(source, destination, *args, **kwargs)
                    if Path(source) == copied:
                        self.write(copied / "SKILL.md", "Edited during backup\n")
                    return result

                with mock.patch.object(os, "rename", side_effect=rename), \
                        mock.patch.object(shutil, "copytree", side_effect=copytree):
                    code, _, err = self.invoke(True)
                self.assertEqual(code, 2, err)
                self.assertIn("changed since planning", err)
                self.assertFalse(copied.is_symlink())
                self.assertEqual((copied / "SKILL.md").read_text(), "Edited during backup\n")
                backups = list((self.root / "custom/backups").rglob(f"{name}/SKILL.md"))
                self.assertEqual([path.read_text() for path in backups], ["Original owned copy\n"])
                receipts = [json.loads(path.read_text()) for path in
                            (self.root / "custom/installations/runs").iterdir()]
                failed = next(receipt for receipt in receipts if any(
                    change["path"] == str(copied) for change in receipt["changes"]))
                self.assertTrue(failed["status"].startswith("partial failure:"))
                change = next(change for change in failed["changes"] if change["path"] == str(copied))
                self.assertEqual(change["outcome"], "planned")
                self.assertTrue(Path(change["backup"]).is_dir())

    def test_fix_now_10_hidden_untracked_files_prevent_pull(self):
        self.git(self.root, "config", "status.showUntrackedFiles", "no")
        self.write(self.root / "hidden-untracked", "fixture")
        with mock.patch.object(sync, "git", wraps=sync.git) as calls:
            code, out, err = self.invoke(True)
        self.assertEqual(code, 1, err)
        self.assertIn("dirty", out)
        self.assertFalse(any("pull" in call.args for call in calls.call_args_list))

    def changed_during_fetch(self, mutation):
        self.write(self.origin / "remote", "fixture")
        self.commit(self.origin, ["remote"])
        real_git = sync.git

        def git(root, *args):
            result = real_git(root, *args)
            if "fetch" in args:
                if mutation == "dirty":
                    self.write(self.root / "dirty", "fixture")
                elif mutation == "branch":
                    self.git(self.root, "checkout", "-b", "other")
                else:
                    self.git(self.root, "commit", "--allow-empty", "-m", "Concurrent edit")
            return result

        with mock.patch.object(sync, "git", side_effect=git) as calls:
            code, out, err = self.invoke(True)
        self.assertEqual(code, 1, out + err)
        self.assertIn("changed during fetch", out)
        self.assertFalse(any("pull" in call.args for call in calls.call_args_list))

    def test_fix_now_10_rechecks_cleanliness_after_fetch(self):
        self.changed_during_fetch("dirty")

    def test_fix_now_10_rechecks_branch_after_fetch(self):
        self.changed_during_fetch("branch")

    def test_fix_now_10_rechecks_revision_after_fetch(self):
        self.changed_during_fetch("revision")

    def test_fix_now_10_rechecks_before_pull(self):
        self.write(self.origin / "remote", "fixture")
        self.commit(self.origin, ["remote"])
        real_git = sync.git

        def git(root, *args):
            result = real_git(root, *args)
            if "rev-list" in args:
                self.write(self.root / "concurrent-untracked", "fixture")
            return result

        with mock.patch.object(sync, "git", side_effect=git) as calls:
            code, out, err = self.invoke(True)
        self.assertEqual(code, 1, out + err)
        self.assertFalse(any("pull" in call.args for call in calls.call_args_list))

    def test_fix_now_11_source_alias_does_not_keep_old_written_target(self):
        old = self.base / "old-source"
        self.link(old, self.root)
        link = self.claude / "skills/sample"
        self.link(link, old / "skills/sample")
        self.receipt({"source_root": str(old)})
        self.clean()
        self.assertEqual(os.readlink(link), str(self.root / "skills/sample"))

    def test_fix_now_12_current_inventory_and_index_ignore_run_history(self):
        self.clean()
        self.clean()
        receipts = self.root / "custom/installations"
        current = [path for path in receipts.iterdir() if path.suffix == ".json"]
        self.assertEqual(len(current), 3)
        for path in current:
            data = json.loads(path.read_text())
            self.assertTrue(data["destinations"])
            self.assertIn("installed_hash", data["destinations"][0])
            self.assertIn(str(path.relative_to(self.root / "custom")), (self.root / "custom/INDEX.md").read_text())
        self.write(receipts / "runs/sync-ignored.json", "invalid historical JSON")
        self.assertEqual(self.invoke()[0], 0)
        real_read = Path.read_text
        reads = []

        def read(path, *args, **kwargs):
            reads.append(path)
            return real_read(path, *args, **kwargs)

        with mock.patch.object(Path, "read_text", autospec=True, side_effect=read), \
                mock.patch.object(os, "scandir", wraps=os.scandir) as scans:
            sync.ownership(self.root)
        self.assertEqual(sorted(reads), sorted(current))
        self.assertEqual([Path(call.args[0]) for call in scans.call_args_list], [receipts])
        self.assertEqual(len([path for path in receipts.iterdir()
                              if path.suffix == ".json"]), 3)

    def test_fix_now_12_inventory_failure_is_recorded_in_run_receipt(self):
        real_write = sync.atomic_text

        def write(path, text, *args, **kwargs):
            if path.name.startswith("home-"):
                raise OSError("fixture inventory failure")
            return real_write(path, text, *args, **kwargs)

        with mock.patch.object(sync, "atomic_text", side_effect=write):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        receipts = list((self.root / "custom/installations/runs").iterdir())
        self.assertEqual(len(receipts), 1)
        data = json.loads(receipts[0].read_text())
        self.assertIn("partial failure: fixture inventory failure", data["status"])

    def test_fix_now_13_named_home_instruction_duplicates_are_reported(self):
        self.clean()
        for name in ("AGENTS.md", "CLAUDE.md"):
            with self.subTest(name=name):
                path = self.home / name
                self.write(path, "Local rules\n<!-- forge:begin -->old<!-- forge:end -->")
                before = path.read_bytes()
                code, out, err = self.invoke(True)
                self.assertEqual(code, 1, out + err)
                self.assertIn("duplicate", out)
                self.assertIn(str(path), out)
                self.assertEqual(path.read_bytes(), before)
                path.unlink()

    def test_source_status_errors_preserve_installed_links(self):
        self.clean()
        real_stat = Path.stat
        real_is_dir, real_is_file = Path.is_dir, Path.is_file
        for denied in (self.root / "skills/sample", self.root / "skills/sample/SKILL.md"):
            with self.subTest(denied=denied):
                def stat(path, *args, **kwargs):
                    if path == denied:
                        raise PermissionError("source status unavailable")
                    return real_stat(path, *args, **kwargs)

                # Model Python 3.14's error-suppressing predicates on older Python too.
                def predicate(method):
                    return lambda path: False if path == denied else method(path)

                with mock.patch.object(Path, "stat", autospec=True, side_effect=stat), \
                        mock.patch.object(Path, "is_dir", autospec=True,
                                          side_effect=predicate(real_is_dir)), \
                        mock.patch.object(Path, "is_file", autospec=True,
                                          side_effect=predicate(real_is_file)):
                    code, _, err = self.invoke(True)
                self.assertEqual(code, 2, err)
                self.assertIn("source status unavailable", err)
                self.assertTrue((self.claude / "skills/sample").is_symlink())

    def test_changed_receipts_and_index_have_journaled_backups(self):
        self.clean()
        index = self.root / "custom/INDEX.md"
        self.write(index, "Operator index\n")
        paths = [sync.inventory_path(self.root, key, home)
                 for key, home in sync.homes(self.root, self.home)] + [index]
        before = {str(path): path.read_bytes() for path in paths}
        self.clean()
        runs = [json.loads(path.read_text()) for path in
                (self.root / "custom/installations/runs").iterdir()]
        latest = next(run for run in runs if any(change["path"] == str(index)
                                               for change in run["changes"]))
        for path, content in before.items():
            change = next(change for change in latest["changes"] if change["path"] == path)
            self.assertEqual(change["outcome"], "fixed")
            self.assertEqual(Path(change["backup"]).read_bytes(), content)

    def test_receipt_edit_after_ownership_read_is_preserved(self):
        self.clean()
        path = sync.inventory_path(self.root, "CLAUDE_CONFIG_DIR", self.claude)
        real_plan = sync.plan
        count = 0
        edited = None

        def plan(*args):
            nonlocal count, edited
            result = real_plan(*args)
            count += 1
            if count == 1:
                data = json.loads(path.read_text())
                data["previous_roots"].append(str(self.base / "previous-source"))
                edited = json.dumps(data)
                self.write(path, edited)
            return result

        with mock.patch.object(sync, "plan", side_effect=plan):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertIn("changed since", err)
        self.assertEqual(path.read_text(), edited)

    def test_removed_edited_copy_remains_a_conflict_with_ownership_evidence(self):
        self.clean()
        path = self.claude / "skills/sample"
        path.unlink()
        self.write(path / "SKILL.md", "Original copy\n")
        digest = sync.copy_hash(path)
        receipt_path = sync.inventory_path(self.root, "CLAUDE_CONFIG_DIR", self.claude)
        receipt = json.loads(receipt_path.read_text())
        receipt["copies"] = {str(path): digest}
        self.write(receipt_path, json.dumps(receipt))
        self.write(path / "SKILL.md", "Operator edit\n")
        self.write(self.root / "skills/other/SKILL.md", "# Other fixture\n")
        self.git(self.root, "add", "skills/other/SKILL.md")
        self.git(self.root, "rm", "skills/sample/SKILL.md")
        self.git(self.root, "commit", "-m", "Remove fixture skill")
        for fix in (False, True, False):
            with self.subTest(fix=fix):
                code, out, err = self.invoke(fix)
                self.assertEqual(code, 1, out + err)
                self.assertIn("conflict", out)
                self.assertIn(str(path), out)
                self.assertEqual((path / "SKILL.md").read_text(), "Operator edit\n")
                self.assertIn(digest, sync.ownership(self.root)[1][str(path)])

    def test_copy_digest_is_computed_once_per_validation_snapshot(self):
        path = self.claude / "skills/sample"
        self.write(path / "SKILL.md", "Owned fixture\n")
        self.receipt({"copies": {str(path): sync.copy_hash(path)}})
        with mock.patch.object(sync, "copy_hash", wraps=sync.copy_hash) as hashes:
            actions, *_ = sync.plan(self.root, self.home)
            action = next(action for action in actions if action["path"] == str(path))
            self.assertEqual(hashes.call_count, 1)
            sync.check_action(action, self.root)
            self.assertEqual(hashes.call_count, 2)
            sync.check_action(action, self.root)
            self.assertEqual(hashes.call_count, 3)

    def test_inventory_recursion_error_records_partial_failure_and_error_exit(self):
        with mock.patch.object(sync, "copy_hash", side_effect=RecursionError("inventory recursion")):
            code, _, err = self.invoke(True)
        self.assertEqual(code, 2, err)
        self.assertIn("inventory recursion", err)
        runs = list((self.root / "custom/installations/runs").iterdir())
        self.assertEqual(len(runs), 1)
        receipt = json.loads(runs[0].read_text())
        self.assertIn("partial failure: inventory recursion", receipt["status"])

    def test_fix_now_15_broken_default_homes_are_visible(self):
        self.claude.rmdir()
        for dangling in (False, True):
            with self.subTest(dangling=dangling):
                if dangling:
                    self.link(self.claude, self.home / "absent")
                else:
                    self.write(self.claude, "not a directory")
                try:
                    code, _, err = self.invoke()
                    self.assertEqual(code, 2, err)
                    self.assertIn(str(self.claude), err)
                finally:
                    self.claude.unlink()

    def test_fix_now_16_malformed_receipt_containers_return_error(self):
        for data in ({"previous_roots": None}, {"copies": []},
                     {"previous_roots": "not a list"}, {"copies": {"relative": "hash"}}):
            with self.subTest(data=data):
                self.receipt(data)
                code, _, err = self.invoke()
                self.assertEqual(code, 2, err)
                self.assertIn("fixture.json", err)

    def test_fix_now_17_report_disables_optional_git_locks(self):
        real_run = subprocess.run

        def run(command, **kwargs):
            if command[0] == "git":
                self.assertTrue("--no-optional-locks" in command or
                                kwargs.get("env", {}).get("GIT_OPTIONAL_LOCKS") == "0")
            return real_run(command, **kwargs)

        with mock.patch.object(subprocess, "run", side_effect=run):
            sync.update(self.root, False)


if __name__ == "__main__":
    unittest.main()
