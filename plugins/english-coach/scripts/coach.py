#!/usr/bin/env python3
"""English Coach: a UserPromptSubmit hook that turns each prompt into an English lesson.

It calls no model. It only adds a short instruction, so the session's own model
coaches the user (English diff, one level-up word, one prompt tip) and then does
the task. Settings (mode, level, unclear) come from common.setting():
/english-coach:level, :pause and :settings, or environment variables.
Fail-open: any problem means print nothing and exit 0.
"""

import json
import re
import sys

import common

MARKER = "en:"
MIN_WORDS = 3  # 1-2 word replies like "ok", "go ahead" are skipped
MIN_CHARS = 6  # same idea for languages written without spaces ("はい", "好的继续")
SKIP_PREFIXES = ("/", "*", "#")  # commands, bypass, memory
# Harness messages wrap the whole prompt in hyphenated tags, e.g.
# <task-notification>...</task-notification>. A prompt like "<div> is broken" is real.
HARNESS_MESSAGE = re.compile(r"<[a-z]+(?:-[a-z]+)+\b[^>]*>.*</[a-z]+(?:-[a-z]+)+>", re.DOTALL)

WORD = re.compile(r"[^\W\d_]+")
VIETNAMESE_CHARS = re.compile(
    "[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]",
    re.IGNORECASE,
)
# Common Vietnamese words typed without accents ("sua loi dang nhap").
# Words that are also common in English or code (the, can, do, day, them, roi, len...) are left out.
UNACCENTED_VIETNAMESE = frozenset("""
    khong duoc cua nhung voi giup sua loi dang nhap minh toi lam nay cai nao gi ve va
    cho trong mot cac nhieu neu thi la tao xoa chay kiem viec phai muon biet hieu giai
    thich ngan gon khac nhau giua tieng viet dung sai chua xong ghi bao gio sao vay nhe
    nha oi hien trang giao dien chuc nang tai xuong truoc sau nguoi nen
""".split())


def char_range(first, last):
    return re.compile(f"[{chr(first)}-{chr(last)}]")


KANA = char_range(0x3040, 0x30FF)
HAN = char_range(0x4E00, 0x9FFF)
HANGUL = char_range(0xAC00, 0xD7AF)
THAI = char_range(0x0E00, 0x0E7F)
SPACELESS = ("Chinese", "Japanese", "Thai")


def detect_language(text):
    """Name of the prompt's main language when it is not English, else None.

    A few foreign words in an English prompt ("rename the biến count") stay English:
    the foreign part must be at least half of the text.
    """
    letters = sum(1 for c in text if c.isalpha())
    if not letters:
        return None
    cjk = len(KANA.findall(text)) + len(HAN.findall(text))
    if cjk * 2 >= letters:
        return "Japanese" if KANA.search(text) else "Chinese"
    if len(HANGUL.findall(text)) * 2 >= letters:
        return "Korean"
    if len(THAI.findall(text)) * 2 >= letters:
        return "Thai"
    words = WORD.findall(text)
    accented = sum(1 for w in words if VIETNAMESE_CHARS.search(w))
    plain = sum(1 for w in words if w.lower() in UNACCENTED_VIETNAMESE)
    if (accented or plain >= 2) and (accented + plain) * 2 >= len(words):
        return "Vietnamese"
    return None


def build_instruction(level, language, unclear, marker):
    if language:
        english = (f"1. 📝 English: the prompt is in {language}. Show a ```diff "
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
        f"[English Coach: target {level}]",
        "Before your reply, coach the user's latest prompt (their own words; ignore code/logs):",
        english,
        f"2. ⬆️ {level}: ≤1 more precise word or phrase, only if clearly better; one-line why.",
        "3. 💡 Prompt tip: ≤1, only if missing goal/context/done-criteria/constraints would change the result.",
        "Omit empty sections. Write all coaching notes in simple English, very brief.",
        'A mistake you already explained earlier in this conversation: no rule again, '
        'just the fix in ≤6 words plus "(again)".',
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

    config = common.load_config()
    mode = common.setting("mode", config)[0]
    level = common.setting("level", config)[0]
    unclear = common.setting("unclear", config)[0]
    if mode == "off":
        return

    text = prompt.strip()
    if mode == "marker":
        if not text.lower().startswith(MARKER):
            return
        text = text[len(MARKER):].strip()
    if not text or text.startswith(SKIP_PREFIXES) or HARNESS_MESSAGE.fullmatch(text):
        return

    language = detect_language(text)
    if language in SPACELESS:
        if len("".join(text.split())) < MIN_CHARS:
            return
    elif language != "Vietnamese" and len(text.split()) < MIN_WORDS:
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": build_instruction(level, language, unclear, mode == "marker"),
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # fail-open: never break the user's prompt
        pass
    sys.exit(0)
