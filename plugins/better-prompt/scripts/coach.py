#!/usr/bin/env python3
"""Better Prompt: a UserPromptSubmit hook that turns each prompt into an English lesson.

It calls no model. It only adds a short instruction, so the session's own model
coaches the user (English diff, one level-up word, one prompt tip) and then does
the task. Settings (environment variables, all optional):
  BETTER_PROMPT          always | marker | off   (default: always)
  BETTER_PROMPT_LEVEL    B2 | C1 | C2            (default: C1)
  BETTER_PROMPT_UNCLEAR  rewrite | tip           (default: rewrite)
Fail-open: any problem means print nothing and exit 0.
"""

import json
import os
import re
import sys

MODES = ("always", "marker", "off")
LEVELS = ("B2", "C1", "C2")
UNCLEAR = ("rewrite", "tip")
MARKER = "en:"
MIN_WORDS = 3  # 1-2 word replies like "ok", "go ahead" are skipped
SKIP_PREFIXES = ("/", "*", "#", "<")  # commands, bypass, memory, harness messages

VIETNAMESE_CHARS = re.compile(
    "[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)


def setting(name, allowed, default):
    value = os.environ.get(name, "").strip()
    for option in allowed:
        if value.lower() == option.lower():
            return option
    return default


def build_instruction(level, vietnamese, unclear, marker):
    if vietnamese:
        english = (f"1. 📝 English: the prompt is in Vietnamese. Show a ```diff "
                   f"(- original, + natural {level} English version), then ≤2 notes on key words.")
    else:
        english = ("1. 📝 English: only if there are mistakes, a ```diff (- original, "
                   "+ corrected natural English), then ≤3 one-line notes on the rule.")
    if unclear == "rewrite":
        vague = ("Before any tool use: if the request is too vague to do well even with the conversation "
                 "context, do NOT start or explore: show ⚠️ what is missing and ask the user to rewrite it themselves.")
    else:
        vague = "Never stop for vagueness: do your best and put the advice in the 💡 tip."
    lines = [
        f"[Better Prompt: English coach, target {level}]",
        "Before your reply, coach the user's latest prompt (their own words; ignore code/logs):",
        english,
        f"2. ⬆️ {level}: ≤1 more precise word or phrase, only if clearly better; one-line why.",
        "3. 💡 Prompt tip: ≤1, only if missing goal/context/done-criteria/constraints would change the result.",
        "Omit empty sections. Write all coaching notes in simple English, very brief.",
        vague,
    ]
    if marker:
        lines.append(f'Ignore the leading "{MARKER}" marker.')
    return "\n".join(lines)


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
        prompt = data.get("prompt")
    except (ValueError, AttributeError):
        return
    if not isinstance(prompt, str):
        return

    mode = setting("BETTER_PROMPT", MODES, "always")
    level = setting("BETTER_PROMPT_LEVEL", LEVELS, "C1")
    unclear = setting("BETTER_PROMPT_UNCLEAR", UNCLEAR, "rewrite")
    if mode == "off":
        return

    text = prompt.strip()
    if mode == "marker":
        if not text.lower().startswith(MARKER):
            return
        text = text[len(MARKER):].strip()
    if not text or text.startswith(SKIP_PREFIXES):
        return

    vietnamese = bool(VIETNAMESE_CHARS.search(text))
    if not vietnamese and len(text.split()) < MIN_WORDS:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": build_instruction(level, vietnamese, unclear, mode == "marker"),
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail-open: never break the user's prompt
        pass
    sys.exit(0)
