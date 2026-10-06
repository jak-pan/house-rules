#!/usr/bin/env python3
"""Extract human transcript text to private, incremental JSONL batches."""

from pathlib import Path
import hashlib
import json
import os
import re
import sys
import tempfile


class TranscriptError(ValueError):
    """An input cannot be processed without losing provenance or content."""


def object_line(line, path, position):
    try:
        record = json.loads(line)
    except (ValueError, UnicodeError) as error:
        raise TranscriptError(f"invalid JSON in {path} at byte {position}") from error
    if not isinstance(record, dict):
        raise TranscriptError(f"expected an object in {path} at byte {position}")
    return record


def object_field(record, key):
    field = record.get(key, {})
    if not isinstance(field, dict):
        raise TranscriptError(f"{key} must be an object")
    return field


def text_content(content, tool=None):
    if isinstance(content, str):
        return strip_injected(content, tool) if tool else content
    if not isinstance(content, list):
        raise TranscriptError("human message content must be text or content blocks")
    texts = []
    for block in content:
        if not isinstance(block, dict):
            raise TranscriptError("invalid human content block")
        if block.get("type") in ("text", "input_text"):
            if not isinstance(block.get("text"), str):
                raise TranscriptError("human text block is missing text")
            text = text_content(block["text"], tool)
            if text:
                texts.append(text)
        elif block.get("type") not in ("image", "input_image", "tool_result"):
            raise TranscriptError("unsupported human content block")
    return "\n".join(texts)


def strip_injected(text, tool):
    tags = ("task-notification", "teammate-message", "subagent_notification")
    if tool == "codex":
        tags += ("environment_context", "user_instructions", "turn_aborted", "skill")
    envelopes = r"<(?P<tag>" + "|".join(tags) + r")(?:\s[^<>]*)?>"
    if tool == "codex":
        envelopes += (r"|# AGENTS\.md instructions for [^\n]+\n[ \t\n]*"
                      r"<(?P<instructions>INSTRUCTIONS)>")
    parts = []
    position = 0
    for opening in re.finditer(envelopes, text):
        if opening.start() < position:
            continue
        tag = opening.group(opening.lastgroup)
        tokens = re.compile(r"<" + tag + r"(?:\s[^<>]*)?>|</" + tag + r">")
        depth = 1
        for token in tokens.finditer(text, opening.end()):
            depth += -1 if token.group().startswith("</") else 1
            if depth == 0:
                parts.append(text[position:opening.start()])
                position = token.end()
                break
    parts.append(text[position:])
    return "".join(parts)


def human_message(record, tool, session):
    if tool == "claude":
        origin = record.get("origin")
        if (record.get("type") != "user" or
                not isinstance(origin, dict) or origin.get("kind") != "human" or
                record.get("isMeta") or record.get("isSidechain")):
            return None
        text = text_content(object_field(record, "message").get("content"), tool)
        session = record.get("sessionId")
    elif tool == "codex":
        payload = object_field(record, "payload")
        if (record.get("type") != "response_item" or
                payload.get("type") != "message" or payload.get("role") != "user"):
            return None
        text = text_content(payload.get("content"), tool)
    else:
        # Kimi's user-history is typed input, not its agent conversation log.
        text = text_content(record.get("content"))
        if re.match(r"/[A-Za-z0-9_-]+(?::[A-Za-z0-9_-]+)*(?:\s|$)", text.strip()):
            return None
    if not text.strip():
        return None
    if not isinstance(session, str) or not session:
        raise TranscriptError("human message is missing a session identifier")
    timestamp = record.get("timestamp")
    if tool != "kimi" and (not isinstance(timestamp, str) or not timestamp):
        raise TranscriptError("human message is missing a timestamp")
    return {"tool": tool, "session": session, "timestamp": timestamp, "text": text}


def transcript_paths(root, tool):
    def report_error(error):
        raise error

    # Unlike Path.glob, walk's onerror exposes unreadable directories.
    for directory, directories, files in os.walk(root, onerror=report_error,
                                                followlinks=tool == "claude"):
        depth = len(Path(directory).relative_to(root).parts)
        directories.sort()
        if tool == "kimi" or tool == "claude" and depth == 1:
            directories.clear()
        if tool == "claude" and depth != 1:
            continue
        for filename in sorted(files):
            if filename.endswith(".jsonl"):
                yield (Path(directory) / filename).resolve(strict=True)


def sources():
    home = Path.home()
    codex = [Path(os.environ.get("CODEX_HOME", home / ".codex"))]
    claude = [home / ".claude/projects"]
    for variable, roots in (("TRANSCRIPT_GAPS_CODEX_HOMES", codex),
                            ("TRANSCRIPT_GAPS_CLAUDE_ROOTS", claude)):
        roots.extend(Path(part).expanduser() for part in
                     os.environ.get(variable, "").split(os.pathsep) if part)
    kimi = Path(os.environ.get("KIMI_CODE_HOME", home / ".kimi-code")).expanduser()
    found = set()
    for tool, roots in (("claude", claude),
                        ("codex", [p.expanduser() / "sessions" for p in codex]),
                        ("kimi", [kimi / "user-history"])):
        for index, root in enumerate(roots):
            try:
                root.stat()
            except FileNotFoundError:
                if index > 0:
                    raise TranscriptError("configured extra transcript root does not exist")
                override = {"codex": "CODEX_HOME", "kimi": "KIMI_CODE_HOME"}.get(tool)
                if override and override in os.environ:
                    raise TranscriptError(f"configured {override} transcript root does not exist")
                continue
            if not root.is_dir():
                raise TranscriptError("transcript root is not a directory")
            for path in transcript_paths(root, tool):
                key = (tool, path)
                if key not in found:
                    found.add(key)
                    yield key


def read_source(tool, path, offset):
    messages = []
    with path.open("rb") as stream:
        end = os.fstat(stream.fileno()).st_size
        if end < offset:
            raise TranscriptError(f"transcript was truncated: {path}")
        session = path.stem
        agent_run = False
        if tool == "codex":
            meta = object_line(stream.readline(), path, 0)
            payload = object_field(meta, "payload")
            if (meta.get("type") != "session_meta" or
                    not isinstance(payload.get("originator"), str) or not payload["originator"] or
                    not isinstance(payload.get("id"), str) or not payload["id"]):
                raise TranscriptError(f"Codex session metadata is missing: {path}")
            session = payload["id"]
            source = payload.get("source")
            agent_run = payload["originator"] == "codex_exec" or (
                isinstance(source, dict) and "subagent" in source)
        stream.seek(offset)
        while stream.tell() < end:
            position = stream.tell()
            line = stream.readline(end - position)
            if not line.endswith(b"\n"):
                raise TranscriptError(f"incomplete transcript line in {path} at byte {position}")
            record = object_line(line, path, position)
            if not agent_run:
                message = human_message(record, tool, session)
                if message is not None:
                    messages.append(message)
    return messages, end


def state_directory():
    default = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    state = Path(os.environ.get("TRANSCRIPT_GAPS_STATE_DIR",
                                default / "house-rules/transcript-gaps")).expanduser().resolve()
    checkout = Path(__file__).resolve().parents[3]
    if state == checkout or checkout in state.parents:
        raise TranscriptError("state directory must be outside the House Rules checkout")
    for parent in (state, *state.parents):
        if parent.name in (".git", ".hg", ".svn") or any(
                (parent / marker).exists() for marker in (".git", ".hg", ".svn")):
            raise TranscriptError("state directory must be outside repositories")
    if (state / "last-run.json").is_symlink():
        raise TranscriptError("last-run marker must not be a symlink")
    return state


def atomic_write(path, text):
    # Temporary output stays in the validated state directory, with mode 0600.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
        temporary.replace(path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def extract():
    state = state_directory()
    marker = state / "last-run.json"
    offsets = {}
    if marker.exists():
        offsets = object_line(marker.read_bytes(), marker, 0)
        if any(not isinstance(path, str) or type(offset) is not int or offset < 0
               for path, offset in offsets.items()):
            raise TranscriptError("invalid last-run offsets")
    updated = dict(offsets)
    messages = []
    for tool, path in sources():
        key = tool + ":" + str(path)
        rows, end = read_source(tool, path, offsets.get(key, 0))
        messages.extend(rows)
        updated[key] = end
    if updated == offsets:
        return
    state.mkdir(parents=True, mode=0o700, exist_ok=True)
    encoded_marker = json.dumps(updated, sort_keys=True) + "\n"
    output = None
    if messages:
        digest = hashlib.sha256(encoded_marker.encode()).hexdigest()
        output = state / f"messages-{digest}.jsonl"
        atomic_write(output, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in messages))
    # Publish output before consuming the source offsets. A failed run is visible.
    atomic_write(marker, encoded_marker)
    if output is not None:
        print(output)


def main():
    try:
        extract()
    except (OSError, TranscriptError) as error:
        print(f"transcript_gaps: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
