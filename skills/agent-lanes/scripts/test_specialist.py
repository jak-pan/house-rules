#!/usr/bin/env python3
"""Launcher contract tests using synthetic executables, homes and canary records."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import contextlib
import io

ROOT = Path(__file__).resolve().parents[3]
LAUNCHER = Path(__file__).with_name("specialist.py")


class SpecialistTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="specialist-test-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.workdir = self.base / "checkout"
        self.workdir.mkdir()
        self.root = self.base / "rules"
        self.root.mkdir()
        self.user = self.base / "user"
        self.user.mkdir()
        self.home = self.base / "specialist-home"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.calls = self.base / "calls.jsonl"
        self.pack = self.base / "pack.txt"
        self.manifest = self.base / "manifest.json"
        self.out = self.base / "answer.txt"
        self.qualification = self.base / "canary.json"
        self.data = b"House Rules revision: " + b"a" * 40 + b"\n\nRequired skill text\r\nTask\n\n"
        self.pack.write_bytes(self.data)
        self.manifest.write_text(json.dumps({"house_rules_revision": "a" * 40,
            "files": [], "pack": {"sha256": hashlib.sha256(self.data).hexdigest()}}))
        self.env = {**os.environ, "HOME": str(self.user), "PATH": str(self.bin) + os.pathsep + os.environ["PATH"],
                    "FAKE_CALLS": str(self.calls), "FAKE_DEBUG": "[]"}
        for key in ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "KIMI_CODE_HOME"):
            self.env[key] = str(self.base / ("normal-" + key))
            Path(self.env[key]).mkdir()
        (Path(self.env["CODEX_HOME"]) / "config.toml").write_text("# normal test home\n")
        # The test process only executes these files, never an installed model CLI.
        fake = '''#!{python}
import json, os, pathlib, sys
tool = pathlib.Path(sys.argv[0]).name
args = sys.argv[1:]
if args == ["--version"]:
    print(tool + " fixture-1")
    sys.exit(0)
if args[:2] == ["debug", "prompt-input"]:
    print(os.environ["FAKE_DEBUG"])
    sys.exit(int(os.environ.get("FAKE_DEBUG_EXIT", "0")))
data = sys.stdin.buffer.read() if tool != "kimi" else args[args.index("-p") + 1].encode()
with open(os.environ["FAKE_CALLS"], "a") as f:
    f.write(json.dumps({{"tool":tool, "args":args, "pack":data.hex(), "cwd":os.getcwd(),
                        "home":os.environ.get("CODEX_HOME" if tool == "codex" else "KIMI_CODE_HOME")}}) + "\\n")
if tool == "claude":
    print(os.environ.get("FAKE_INIT", '{{"type":"system","subtype":"init","skills":[],"memory":[]}}'), flush=True)
    if os.environ.get("FAKE_BLOCK"):
        import time
        time.sleep(10)
    print(json.dumps({{"type":"result", "subtype":"success", "is_error":False, "result":"answer\\n"}}))
elif tool == "codex":
    if not os.environ.get("FAKE_NO_OUT"):
        pathlib.Path(args[args.index("-o") + 1]).write_text("answer\\n")
else:
    print("answer")
sys.exit(int(os.environ.get("FAKE_EXIT", "0")))
'''.format(python=sys.executable)
        for tool in ("codex", "claude", "kimi"):
            path = self.bin / tool
            path.write_text(fake)
            path.chmod(0o755)

    def register(self, tool):
        (self.root / "custom").mkdir(exist_ok=True)
        (self.root / "custom/sync.env").write_text(
            f'SPECIALIST_{"CODEX_HOME" if tool == "codex" else "KIMI_CODE_HOME"}="{self.home}"\n')
        (self.home / "config.toml").write_text("project_doc_max_bytes = 0\n")
        if tool == "codex":
            (self.home / "auth.json").write_text("{}")
        else:
            (self.home / "credentials").mkdir(exist_ok=True)
            (self.home / "credentials/kimi-code.json").write_text("{}")

    def qualify(self, tool, mode="rw", prevention=None, mcp=None):
        # Canary artifacts are existing evidence, not a launcher-owned cache.
        log = self.base / "canary.log"
        log.write_text("Synthetic isolation and write-denial evidence\n")
        config = self.home / "config.toml"
        record = {"tool": tool, "version": tool + " fixture-1", "mode": mode,
                  "home": str(self.home) if tool != "claude" else None,
                  "workdir": str(self.workdir), "isolation": True,
                  "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest() if tool != "claude" else None,
                  "evidence": {"path": str(log), "sha256": hashlib.sha256(log.read_bytes()).hexdigest()},
                  "write_prevention": prevention, "codex_prompt_input": [],
                  "write_test": {"baseline_allowed": True, "denied": True, "write_absent": True},
                  "mcp_sha256": hashlib.sha256(mcp.read_bytes()).hexdigest() if mcp else None,
                  "mcp_isolated": bool(mcp), "mcp_tool_succeeded": bool(mcp), "kimi_start": "empty"}
        self.qualification.write_text(json.dumps(record))
        return record

    def invoke(self, tool="claude", mode="rw", qualify=False, extra=(), readonly_mount=False):
        args = [sys.executable, "-B", str(LAUNCHER), "--root", str(self.root), "--tool", tool,
                "--pack", str(self.pack), "--manifest", str(self.manifest), "--workdir", str(self.workdir),
                "--mode", mode, "--out", str(self.out), *extra]
        if qualify:
            args += ["--qualification", str(self.qualification)]
        if readonly_mount:
            spec = importlib.util.spec_from_file_location("specialist_tested", LAUNCHER)
            launcher = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(launcher)
            out, err = io.StringIO(), io.StringIO()
            with mock.patch.dict(os.environ, self.env, clear=True), \
                    mock.patch.object(launcher.os, "statvfs", return_value=mock.Mock(f_flag=os.ST_RDONLY)), \
                    mock.patch.object(launcher.os, "getsid", return_value=-1), \
                    contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = launcher.main(args[3:])
            return subprocess.CompletedProcess(args, code, out.getvalue().encode(), err.getvalue().encode())
        return subprocess.run(args, env=self.env, capture_output=True, timeout=5)

    def called(self):
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def refused(self, result, check):
        self.assertEqual(result.returncode, 2, result.stderr.decode())
        self.assertIn(check, result.stderr.decode())
        self.assertEqual(self.called(), [])
        self.assertFalse(self.out.exists())

    def test_missing_and_mismatched_headers_refuse_before_model_call(self):
        for data in (b"Task\n", self.data.replace(b"a" * 40, b"b" * 40)):
            with self.subTest(data=data):
                self.pack.write_bytes(data)
                self.refused(self.invoke(), "header")

    def test_hash_mismatch_refuses_before_model_call(self):
        self.pack.write_bytes(self.data + b"changed")
        self.refused(self.invoke(), "hash")

    def test_manifest_requires_files_and_revision(self):
        for key in ("files", "house_rules_revision", "pack"):
            record = json.loads(self.manifest.read_text())
            record.pop(key)
            self.manifest.write_text(json.dumps(record))
            self.refused(self.invoke(), "manifest")
            self.set_manifest()

    def set_manifest(self):
        self.manifest.write_text(json.dumps({"house_rules_revision": "a" * 40, "files": [],
                                           "pack": {"sha256": hashlib.sha256(self.data).hexdigest()}}))

    def test_missing_registered_homes_and_login_state_refuse(self):
        for tool in ("codex", "kimi"):
            with self.subTest(tool=tool):
                self.refused(self.invoke(tool), "registered")
        self.register("codex")
        (self.home / "auth.json").unlink()
        self.refused(self.invoke("codex"), "login")

    def test_branded_and_unbranded_global_instructions_refuse(self):
        self.register("codex")
        self.qualify("codex")
        for name in ("AGENTS.md", "AGENTS.override.md"):
            for text in ("Operator task instructions", "<!-- house-rules:begin -->rules", "<!-- forge:begin -->rules", "<!-- groundwork:begin -->rules"):
                with self.subTest(name=name, text=text):
                    path = self.home / name
                    path.write_text(text)
                    self.refused(self.invoke("codex", qualify=True), str(path))
                    path.unlink()

    def test_enabled_third_party_and_new_skills_need_disable_entries(self):
        self.register("codex")
        self.qualify("codex")
        for name in ("third-party", "change-review"):
            path = self.user / ".agents/skills" / name / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text("skill")
            self.refused(self.invoke("codex", qualify=True), str(path.parent))

    def test_codex_debug_rejects_instruction_and_skill_messages_from_any_source(self):
        self.register("codex")
        self.qualify("codex")
        for text in ("Unbranded task instructions", "## Skills\nthird-party", "Project rules"):
            self.env["FAKE_DEBUG"] = json.dumps([{"type": "message", "role": "developer", "content": [{"type":"input_text", "text":text}]}])
            self.refused(self.invoke("codex", qualify=True), "prompt-input")

    def test_codex_debug_failure_and_unknown_format_refuse(self):
        self.register("codex")
        self.qualify("codex")
        for value in ("not json", "{}"):
            self.env["FAKE_DEBUG"] = value
            self.refused(self.invoke("codex", qualify=True), "prompt-input")
        self.env["FAKE_DEBUG"] = "[]"
        self.env["FAKE_DEBUG_EXIT"] = "7"
        self.refused(self.invoke("codex", qualify=True), "prompt-input")

    def test_read_only_without_qualified_write_prevention_refuses_every_tool(self):
        for tool in ("codex", "claude", "kimi"):
            with self.subTest(tool=tool):
                if tool != "claude":
                    self.register(tool)
                self.qualify(tool, "ro", "prompt")
                self.refused(self.invoke(tool, "ro", True), "write prevention")

    def test_unqualified_isolation_and_stale_versions_refuse(self):
        self.register("kimi")
        self.refused(self.invoke("kimi"), "qualification")
        record = self.qualify("kimi")
        record["version"] = "old version"
        self.qualification.write_text(json.dumps(record))
        self.refused(self.invoke("kimi", qualify=True), "version")

    def test_codex_arguments_each_mode_and_pack_bytes_unchanged(self):
        self.register("codex")
        for mode, sandbox in (("ro", "read-only"), ("rw", "workspace-write")):
            with self.subTest(mode=mode):
                self.qualify("codex", mode, "tool")
                result = self.invoke("codex", mode, True, ["--model", "model", "--effort", "high"])
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                call = self.called()[-1]
                self.assertEqual(bytes.fromhex(call["pack"]), self.data)
                self.assertEqual(call["home"], str(self.home))
                self.assertIn(sandbox, call["args"])
                self.assertIn("model_reasoning_effort=\"high\"", call["args"])
                for arg in ("--skip-git-repo-check", "project_doc_max_bytes=0", "-C", str(self.workdir), "-o", "-", "model"):
                    self.assertIn(arg, call["args"])
                self.assertEqual(self.out.read_text(), "answer\n")
                self.out.unlink()

    def test_claude_safe_mode_and_output_extraction_each_mode(self):
        for mode in ("ro", "rw"):
            self.qualify("claude", mode, "host")
            result = self.invoke("claude", mode, True, ["--model", "model"], readonly_mount=mode == "ro")
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            call = self.called()[-1]
            self.assertEqual(bytes.fromhex(call["pack"]), self.data)
            for arg in ("-p", "--safe-mode", "--output-format", "stream-json", "--verbose", "--permission-prompts", "none", "model"):
                self.assertIn(arg, call["args"])
            self.assertIn("--disallowedTools" if mode == "ro" else "--permission-mode", call["args"])
            self.assertEqual(self.out.read_text(), "answer\n")
            self.out.unlink()

    def test_claude_discovery_stops_child_at_initial_event(self):
        self.qualify("claude")
        for field in ("skills", "memory"):
            self.env["FAKE_INIT"] = json.dumps({"type":"system", "subtype":"init", "skills":[], "memory":[], field:["third party instructions"]})
            self.env["FAKE_BLOCK"] = "1"
            result = self.invoke(qualify=True)
            self.assertEqual(result.returncode, 2, result.stderr.decode())
            self.assertIn(field, result.stderr.decode())
            self.assertFalse(self.out.exists())

    def test_claude_missing_initial_metadata_refuses(self):
        self.qualify("claude")
        self.env["FAKE_INIT"] = '{"type":"system","subtype":"init"}'
        self.assertEqual(self.invoke(qualify=True).returncode, 2)

    def test_required_pack_skill_is_allowed_but_mcp_requires_matching_qualification(self):
        mcp = self.base / "mcp.json"
        mcp.write_text('{"mcpServers": {}}')
        self.refused(self.invoke(extra=["--mcp-config", str(mcp)]), "MCP")
        self.qualify("claude", mcp=mcp)
        result = self.invoke(qualify=True, extra=["--mcp-config", str(mcp)])
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertIn(str(mcp), self.called()[-1]["args"])
        self.assertIn("--safe-mode", self.called()[-1]["args"])
        self.out.unlink()
        self.calls.unlink()
        mcp.write_text("changed")
        self.refused(self.invoke(qualify=True, extra=["--mcp-config", str(mcp)]), "MCP")

    def test_kimi_empty_start_and_unchanged_pack_with_absolute_checkout(self):
        self.register("kimi")
        self.data += str(self.workdir).encode() + b"\n"
        self.pack.write_bytes(self.data)
        self.set_manifest()
        for mode in ("rw", "ro"):
            self.qualify("kimi", mode, "host")
            result = self.invoke("kimi", mode, True, ["--model", "model"], readonly_mount=mode == "ro")
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            call = self.called()[-1]
            self.assertNotEqual(call["cwd"], str(self.workdir))
            self.assertEqual(call["home"], str(self.home))
            self.assertEqual(bytes.fromhex(call["pack"]), self.data)
            self.assertIn("--skills-dir", call["args"])
            self.assertIn("model", call["args"])
            self.assertEqual(self.out.read_text(), "answer\n")
            self.out.unlink()

    def test_kimi_missing_absolute_checkout_and_unsupported_options_refuse(self):
        self.register("kimi")
        self.qualify("kimi")
        self.refused(self.invoke("kimi", qualify=True), "absolute checkout")
        self.refused(self.invoke("kimi", qualify=True, extra=["--effort", "high"]), "effort")
        self.refused(self.invoke("kimi", qualify=True, extra=["--mcp-config", str(self.pack)]), "MCP")

    def test_child_failure_is_visible_without_retry_or_success_output(self):
        self.qualify("claude")
        self.env["FAKE_EXIT"] = "9"
        result = self.invoke(qualify=True)
        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertIn("9", result.stderr.decode())
        self.assertIn("log", result.stderr.decode())
        self.assertEqual(len(self.called()), 1)
        self.assertFalse(self.out.exists())

    def test_success_without_codex_output_fails_visibly(self):
        self.register("codex")
        self.qualify("codex")
        self.env["FAKE_NO_OUT"] = "1"
        result = self.invoke("codex", qualify=True)
        self.assertEqual(result.returncode, 1, result.stderr.decode())
        self.assertFalse(self.out.exists())

    def test_existing_output_is_refused_without_overwrite(self):
        self.out.write_text("previous answer")
        result = self.invoke()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.out.read_text(), "previous answer")
        self.assertEqual(self.called(), [])

    def test_recorded_host_denial_does_not_allow_currently_writable_checkout(self):
        self.qualify("claude", "ro", "host")
        self.refused(self.invoke("claude", "ro", True), "read-only filesystem")

    def test_native_compiler_pack_reaches_claude_unchanged(self):
        revision = subprocess.run(["git", "--no-replace-objects", "-C", str(ROOT), "rev-parse", "HEAD"],
                                  capture_output=True, check=True).stdout.decode().strip()
        task = self.base / "task.txt"
        task.write_text("Objective: synthetic task\nDecisions: none\nPre-flight: fake tool only\n")
        destination = self.base / "compiled"
        compiled = subprocess.run([sys.executable, "-B", str(ROOT / "skills/pr-ready/scripts/prompt.py"),
            "--repo", str(ROOT), "--rev", revision, "--role", "reviewer", "--include", "skills/agent-lanes/SKILL.md",
            "--no-target", "--task", str(task), "--task-source", "specialist-test", "--out", str(destination)],
            input=b"", capture_output=True, timeout=5)
        self.assertEqual(compiled.returncode, 0, compiled.stderr.decode())
        self.pack, self.manifest = destination / "pack.txt", destination / "manifest.json"
        self.qualify("claude")
        result = self.invoke(qualify=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(bytes.fromhex(self.called()[0]["pack"]), self.pack.read_bytes())

    def test_changed_qualification_log_and_config_refuse_before_model_call(self):
        self.register("codex")
        self.qualify("codex")
        (self.base / "canary.log").write_text("changed evidence")
        self.refused(self.invoke("codex", qualify=True), "evidence")
        self.qualify("codex")
        with (self.home / "config.toml").open("a") as config:
            config.write("# changed native configuration\n")
        self.refused(self.invoke("codex", qualify=True), "config_sha256")

    def test_all_tool_child_failures_retain_logs_without_retry(self):
        for tool in ("codex", "kimi"):
            with self.subTest(tool=tool):
                self.register(tool)
                self.data += str(self.workdir).encode() + b"\n"
                self.pack.write_bytes(self.data)
                self.set_manifest()
                self.qualify(tool)
                self.env["FAKE_EXIT"] = "8"
                result = self.invoke(tool, qualify=True)
                self.assertEqual(result.returncode, 1, result.stderr.decode())
                self.assertIn("8", result.stderr.decode())
                self.assertEqual(len(self.called()), 1)
                self.assertFalse(self.out.exists())
                if tool == "kimi":
                    self.assertTrue(any(b"answer" in log.read_bytes() for log in self.base.glob("answer.txt-*.log")))
                self.calls.unlink()

    def test_dispatch_guidance_identifies_skills_before_opening_bodies(self):
        text = (ROOT / "skills/agent-lanes/SKILL.md").read_text()
        self.assertIn("## Subagent profiles", text)
        self.assertIn("descriptions before opening skill bodies", text)
        self.assertIn("--session", text)
        self.assertIn("unchanged pack and manifest", text)


if __name__ == "__main__":
    unittest.main()
