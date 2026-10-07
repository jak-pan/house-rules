#!/usr/bin/env python3
"""Launch one verified specialist pack; no compilation, scheduling or retries."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("house_rules_sync", ROOT / "scripts/sync.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class Refusal(Exception):
    """Isolation or a required capability could not be established."""


class ChildFailure(Exception):
    """The launched child did not produce a successful result."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified_pack(pack, manifest):
    """Verify bytes once, then send exactly those bytes to the child."""
    data = pack.read_bytes()
    record = json.loads(manifest.read_bytes())
    if (not isinstance(record, dict) or not isinstance(record.get("files"), list) or
            not re.fullmatch(r"[0-9a-f]{40}", str(record.get("house_rules_revision", ""))) or
            not isinstance(record.get("pack"), dict)):
        raise Refusal("manifest requires house_rules_revision, files and pack.sha256")
    header = b"House Rules revision: " + record["house_rules_revision"].encode() + b"\n"
    if not data.startswith(header):
        raise Refusal("pack header is missing or does not match manifest revision")
    if digest(data) != record["pack"].get("sha256"):
        raise Refusal("pack hash does not match manifest pack.sha256")
    if record.get("omitted_shared_rules"):
        raise Refusal("specialist pack must include shared rules; do not compile with --session")
    data.decode("utf-8")
    return data


def specialist_home(args):
    """Use registered homes and the sync owner's checks, never a normal home."""
    if args.tool == "claude":
        return None
    key = "SPECIALIST_CODEX_HOME" if args.tool == "codex" else "SPECIALIST_KIMI_CODE_HOME"
    matches = [path for kind, path in sync.homes(args.root, Path.home()) if kind == key]
    if len(matches) != 1:
        raise Refusal(f"{key} requires exactly one registered specialist home")
    home = matches[0]
    findings = []
    sync.specialist_findings(args.root, Path.home(), key, home, findings, args.workdir)
    if findings:
        raise Refusal("; ".join(findings))
    # Presence is only installation preflight; the tool validates credentials.
    logged_in = (sync.is_file(home / "auth.json") if args.tool == "codex" else
                 sync.is_dir(home / "credentials") and
                 any(sync.is_file(path) for path in sync.children(home / "credentials")))
    if not logged_in:
        raise Refusal(f"missing {args.tool} login state in registered specialist home: {home}")
    return home


def qualification(args, home, env):
    """Consume caller-owned section 7.1 evidence; never create a qualification cache.

    The operator performing the canary attests its result. The launcher verifies
    the log, tool version and launch context, rather than qualifying a model by
    its answer or treating prompt restrictions as a filesystem boundary.
    """
    capability = "MCP" if args.mcp_config else "write prevention" if args.mode == "ro" else "isolation"
    if args.qualification is None:
        raise Refusal(f"{capability} qualification record is required for {args.tool}")
    record = json.loads(args.qualification.read_bytes())
    if not isinstance(record, dict):
        raise Refusal("qualification must be an object")
    version = subprocess.run([args.tool, "--version"], env=env, cwd=args.workdir,
                             capture_output=True, timeout=10)
    if version.returncode or record.get("version") != version.stdout.decode("utf-8").strip():
        raise Refusal("qualification tool version does not match installed version")
    expected = {"tool": args.tool, "home": str(home) if home else None,
                "workdir": str(args.workdir), "mode": args.mode, "isolation": True,
                "config_sha256": digest((home / "config.toml").read_bytes()) if home else None}
    for field, value in expected.items():
        if record.get(field) != value:
            raise Refusal(f"qualification does not match launch {field}")
    evidence = record.get("evidence")
    if (not isinstance(evidence, dict) or not isinstance(evidence.get("path"), str) or
            not Path(evidence["path"]).is_absolute() or
            digest(Path(evidence["path"]).read_bytes()) != evidence.get("sha256")):
        raise Refusal("qualification evidence log is missing or changed")
    if args.mode == "ro":
        supported = {"host", "tool"} if args.tool == "codex" else {"host"}
        if record.get("write_prevention") not in supported or record.get("write_test") != {
                "baseline_allowed": True, "denied": True, "write_absent": True}:
            raise Refusal("read-only write prevention is not qualified; a prompt restriction is insufficient")
        if record["write_prevention"] == "host":
            # Permission bits on an owned directory can be changed by a shell.
            # Support the native read-only filesystem boundary, not chmod or
            # an assertion that some unrelated host wrapper is still present.
            if (not hasattr(os, "statvfs") or not hasattr(os, "ST_RDONLY") or
                    not os.statvfs(args.workdir).f_flag & os.ST_RDONLY):
                raise Refusal("host write prevention requires a currently read-only filesystem at the checkout")
    if args.mcp_config and (record.get("mcp_sha256") != digest(args.mcp_config.read_bytes()) or
                            record.get("mcp_isolated") is not True or
                            record.get("mcp_tool_succeeded") is not True):
        raise Refusal("Claude safe-mode MCP capability is not qualified for this configuration")
    return record


def prompt_context(data):
    """Compare native prompt items with the canary's clean capture, without text heuristics.

    Only the tool-generated environment context varies across captures. Every
    other instruction or skill item must match the qualified clean capture.
    """
    items = json.loads(data)
    if not isinstance(items, list):
        raise Refusal("unknown Codex prompt-input format")
    result = []
    for item in items:
        if not isinstance(item, dict):
            raise Refusal("unknown Codex prompt-input item")
        content = item.get("content", [])
        if (item.get("type") == "message" and item.get("role") == "user" and
                len(content) == 1 and isinstance(content[0], dict) and
                content[0].get("type") == "input_text" and
                re.fullmatch(r"<environment_context>.*</environment_context>\s*",
                             content[0].get("text", ""), re.S)):
            continue
        result.append(item)
    return result


def codex_preflight(args, env, record, log):
    command = ["codex", "debug", "prompt-input", "-c", "project_doc_max_bytes=0",
               "-s", "read-only" if args.mode == "ro" else "workspace-write", "-C", str(args.workdir)]
    command.extend(codex_options(args))
    capture = subprocess.run(command, env=env, cwd=args.workdir, capture_output=True, timeout=30)
    log.write(capture.stdout)
    log.write(capture.stderr)
    log.flush()
    if capture.returncode:
        raise Refusal(f"Codex prompt-input preflight exited {capture.returncode}")
    try:
        clean = record["codex_prompt_input"]
        if not isinstance(clean, list) or prompt_context(capture.stdout) != clean:
            raise Refusal("Codex prompt-input differs from qualified clean capture: additional instructions or discovered skills")
    except (KeyError, ValueError, TypeError) as error:
        raise Refusal("Codex prompt-input capture is missing or invalid") from error


def codex_options(args):
    options = ["-m", args.model] if args.model else []
    if args.effort:
        options += ["-c", "model_reasoning_effort=" + json.dumps(args.effort)]
    return options


def claude_result(command, data, args, env, log):
    """Inspect the initial event while the child runs and stop contaminated launches."""
    child = subprocess.Popen(command, cwd=args.workdir, env=env, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=log)
    initialized, result = False, None
    try:
        # Feed stdin concurrently: a large pack must not deadlock stream output.
        errors = []

        def feed():
            try:
                child.stdin.write(data)
                child.stdin.close()
            except OSError as error:
                errors.append(error)

        writer = threading.Thread(target=feed)
        writer.start()
        for line in child.stdout:
            log.write(line)
            log.flush()
            try:
                event = json.loads(line)
            except ValueError as error:
                raise Refusal("unknown Claude stream event format") from error
            if not isinstance(event, dict):
                raise Refusal("unknown Claude stream event format")
            if not initialized:
                if event.get("type") != "system" or event.get("subtype") != "init":
                    raise Refusal("Claude initial isolation event is missing")
                for field in ("skills", "memory"):
                    if field not in event or event[field] != []:
                        raise Refusal(f"Claude initial event has discovered {field} or missing {field} metadata")
                initialized = True
            elif event.get("type") == "result":
                if result is not None:
                    raise ChildFailure("Claude emitted multiple final results")
                if event.get("is_error") is not False or event.get("subtype") != "success":
                    raise ChildFailure("Claude final result reports failure")
                result = event.get("result")
        status = child.wait()
        writer.join()
        if status:
            raise ChildFailure(f"child exit status {status}")
        if errors:
            raise ChildFailure("child failed to consume verified pack")
        if not initialized:
            raise Refusal("Claude initial isolation event is missing")
        if not isinstance(result, str):
            raise ChildFailure("Claude final text result is missing")
        return result.encode("utf-8")
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        if "writer" in locals():
            writer.join()
        child.stdout.close()


def launch(args, data, home, env, record, log, staging):
    if args.tool == "codex":
        codex_preflight(args, env, record, log)
        command = ["codex", "exec", "--skip-git-repo-check", "-c", "project_doc_max_bytes=0",
                   "-s", "read-only" if args.mode == "ro" else "workspace-write", "-C", str(args.workdir),
                   "-o", str(staging / "answer"), *codex_options(args), "-"]
        child = subprocess.run(command, cwd=args.workdir, env=env, input=data, stdout=log, stderr=log)
        answer = staging / "answer"
    elif args.tool == "claude":
        command = ["claude", "-p", "--safe-mode", "--output-format", "stream-json", "--verbose",
                   "--permission-prompts", "none"]
        command += (["--disallowedTools", "Edit", "Write", "NotebookEdit"] if args.mode == "ro" else
                    ["--permission-mode", "acceptEdits"])
        if args.model:
            command += ["--model", args.model]
        if args.mcp_config:
            command += ["--mcp-config", str(args.mcp_config)]
        answer = staging / "answer"
        answer.write_bytes(claude_result(command, data, args, env, log))
        return answer
    else:
        if record.get("kimi_start") != "empty":
            raise Refusal("Kimi empty-directory isolation is not qualified")
        if str(args.workdir) not in data.decode("utf-8"):
            raise Refusal("Kimi pack must name the absolute checkout for an empty-directory start")
        # Put startup and the empty skill scan under the registered, neutral home.
        with tempfile.TemporaryDirectory(prefix="specialist-", dir=home) as empty:
            skills = Path(empty) / "skills"
            skills.mkdir()
            command = ["kimi", "-p", data.decode("utf-8"), "--skills-dir", str(skills)]
            if args.model:
                command += ["-m", args.model]
            answer = staging / "answer"
            with answer.open("wb") as output:
                child = subprocess.run(command, cwd=empty, env=env, stdout=output, stderr=log)
    if child.returncode:
        if args.tool == "kimi":
            log.write(answer.read_bytes())
        raise ChildFailure(f"child exit status {child.returncode}")
    if not sync.is_file(answer):
        raise ChildFailure("child exited 0 without writing --out")
    return answer


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--tool", choices=("codex", "claude", "kimi"), required=True)
    parser.add_argument("--mode", choices=("ro", "rw"), required=True)
    for name in ("pack", "manifest", "workdir", "out"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--qualification", type=Path)
    parser.add_argument("--model")
    parser.add_argument("--effort")
    parser.add_argument("--mcp-config", type=Path)
    args = parser.parse_args(argv)
    started = time.monotonic()
    log_path = None
    try:
        args.workdir = args.workdir.resolve(strict=True)
        args.out = args.out.absolute()
        if not sync.is_dir(args.workdir):
            raise Refusal("workdir must be a directory")
        if sync.present(args.out):
            raise Refusal("--out already exists; retain each attempt's output")
        if args.effort and args.tool != "codex":
            raise Refusal(f"{args.tool} reasoning effort capability is unsupported")
        if args.mcp_config and args.tool != "claude":
            raise Refusal(f"explicit MCP configuration is unsupported for {args.tool}")
        if args.mcp_config:
            args.mcp_config = args.mcp_config.resolve(strict=True)
        if os.getppid() == 1 or (hasattr(os, "getsid") and os.getsid(0) == os.getpid()):
            raise Refusal("detached execution refused; use an attached background job")
        data = verified_pack(args.pack, args.manifest)
        home = specialist_home(args)
        env = os.environ.copy()
        if home:
            env["CODEX_HOME" if args.tool == "codex" else "KIMI_CODE_HOME"] = str(home)
        record = qualification(args, home, env)
        with tempfile.NamedTemporaryFile(prefix=args.out.name + "-", suffix=".log", dir=args.out.parent,
                                         delete=False) as log:
            log_path = Path(log.name)
            with tempfile.TemporaryDirectory(prefix="." + args.out.name + "-", dir=args.out.parent) as temporary:
                answer = launch(args, data, home, env, record, log, Path(temporary))
                # Native no-clobber publication: never overwrite an earlier result.
                os.link(answer, args.out)
        print(f"specialist: succeeded; pack {digest(data)}; log {log_path}; {time.monotonic() - started:.3f}s", file=sys.stderr)
        return 0
    except ChildFailure as error:
        print(f"specialist: {error}; log {log_path}; {time.monotonic() - started:.3f}s", file=sys.stderr)
        return 1
    except (Refusal, OSError, ValueError, UnicodeError, subprocess.SubprocessError) as error:
        message = " ".join(str(error).splitlines())
        print(f"specialist: refused: {message}" + (f"; log {log_path}" if log_path else "") +
              f"; {time.monotonic() - started:.3f}s", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
