#!/usr/bin/env python3
"""Print a Grok run's final assistant message.

Usage: grok_final.py <grok --output-format json output>

Grok's JSON `text` concatenates its narration ("I'll review ...") with the report, often gluing the
verdict onto a narration sentence. The session's chat_history.jsonl keeps each assistant message
separately, and the last one is the report. Falls back to `text` (with a note on stderr) when the
session file cannot be found; the verdict parser stays fail-closed either way.
"""
import glob
import json
import os
import sys


def final_message(result: dict, sessions_root: str) -> str | None:
    sid = result.get("sessionId")
    if not sid:
        return None
    paths = glob.glob(os.path.join(glob.escape(sessions_root), "*", glob.escape(sid), "chat_history.jsonl"))
    if len(paths) != 1:
        return None
    last = None
    with open(paths[0]) as history:
        for line in history:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") == "assistant" and isinstance(entry.get("content"), str):
                last = entry["content"]
    return last


def main() -> int:
    result = json.load(open(sys.argv[1]))
    text = final_message(result, os.path.expanduser("~/.grok/sessions"))
    if text is None:
        print("grok_final: session history not found; using the concatenated text", file=sys.stderr)
        text = result.get("text", "")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
