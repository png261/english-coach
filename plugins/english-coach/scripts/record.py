#!/usr/bin/env python3
"""English Coach: a Stop hook that saves each coaching note to a local log.

It reads Claude's reply to the latest prompt, finds the English section (the diff
and its notes), and appends one JSON line to ~/.claude/english-coach/mistakes.jsonl.
/english-coach:review reads that log. It calls no model.
Turn it off with: /english-coach:settings log off
Fail-open: any problem means print nothing and exit 0.
"""

import json
import re
import sys
from collections import deque
from datetime import datetime, timezone

import common

NOTE, UP, TIP = chr(0x1F4DD), chr(0x2B06), chr(0x1F4A1)  # the section emojis
DIFF = re.compile(r"```diff[^\n]*\n(.*?)```", re.DOTALL)
MAX_DIFF_DISTANCE = 300  # the diff must follow the English heading closely
TAIL_LINES = 3000  # transcript lines read from the end


def is_prompt(entry):
    """True for a transcript entry holding a prompt the user typed."""
    if entry.get("type") != "user" or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "text" for b in content)


def turn_text(path):
    """All of Claude's text since the latest prompt, from the transcript file."""
    with open(path, encoding="utf-8") as f:
        lines = deque(f, maxlen=TAIL_LINES)
    parts = []
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict):
            continue
        if is_prompt(entry):
            break
        if entry.get("type") == "assistant":
            content = (entry.get("message") or {}).get("content") or []
            for block in reversed(content if isinstance(content, list) else []):
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text") or "")
    return "\n".join(reversed(parts))


def clean(line):
    return line[1:].strip()


def parse(text):
    """The coaching in a reply as a dict, or None when there is none."""
    start = text.find(NOTE)
    if start < 0:
        return None
    part = text[start:]
    end = re.search(r"^\s*---\s*$", part, re.MULTILINE)
    if end:
        part = part[:end.start()]
    diff = DIFF.search(part)
    if not diff or diff.start() > MAX_DIFF_DISTANCE:
        return None
    rows = diff.group(1).splitlines()
    original = [clean(r) for r in rows if r.startswith("-")]
    corrected = [clean(r) for r in rows if r.startswith("+")]
    if not original or not corrected:
        return None
    notes, level_up = [], None
    for line in part[diff.end():].splitlines():
        s = line.strip()
        if s.startswith(TIP):
            break
        if s.startswith(UP):
            level_up = s.split(":", 1)[-1].strip(" *") or None
            break
        if s[:2] in ("- ", "* ", "• "):
            notes.append(s[2:].strip())
    return {
        "original": "\n".join(original),
        "corrected": "\n".join(corrected),
        "notes": notes,
        "level_up": level_up,
    }


def already_saved(path, record):
    if not path.exists():
        return False
    with open(path, encoding="utf-8") as f:
        for line in deque(f, maxlen=20):
            try:
                old = json.loads(line)
            except ValueError:
                continue
            if (old.get("session"), old.get("original")) == (record["session"], record["original"]):
                return True
    return False


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return
    if not isinstance(data, dict) or common.setting("log")[0] == "off":
        return
    found = None
    if data.get("transcript_path"):
        found = parse(turn_text(data["transcript_path"]))
    if not found and isinstance(data.get("last_assistant_message"), str):
        found = parse(data["last_assistant_message"])
    if not found:
        return
    record = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session": data.get("session_id"),
        **found,
    }
    path = common.log_path()
    if already_saved(path, record):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail-open: never break the session
        pass
    sys.exit(0)
