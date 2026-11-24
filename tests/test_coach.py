"""Tests for the English Coach hook. Run: python3 -m unittest discover -s tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "plugins/english-coach/scripts/coach.py"
HOME = tempfile.mkdtemp()  # empty English Coach folder: no saved settings


def run(prompt=None, env_extra=None, raw_stdin=None):
    """Run the hook like Claude Code does and return (exit_code, stdout)."""
    stdin = raw_stdin if raw_stdin is not None else json.dumps(
        {"hook_event_name": "UserPromptSubmit", "prompt": prompt, "session_id": "t"}
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith("ENGLISH_COACH")}
    env["ENGLISH_COACH_HOME"] = HOME
    env.update(env_extra or {})
    p = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin, capture_output=True, text=True, env=env, timeout=10,
    )
    return p.returncode, p.stdout


def context(stdout):
    """Extract the injected instruction, or None when the hook stayed silent."""
    if not stdout.strip():
        return None
    out = json.loads(stdout)
    hso = out["hookSpecificOutput"]
    assert hso["hookEventName"] == "UserPromptSubmit"
    return hso["additionalContext"]


ENGLISH = "I want my english is C1 so i prefer to use correct word"
VIETNAMESE = "sửa lỗi đăng nhập trả về 401 dù mật khẩu đúng"


class SkipRules(unittest.TestCase):
    def assertSilent(self, prompt, **kw):
        code, out = run(prompt, **kw)
        self.assertEqual(code, 0)
        self.assertIsNone(context(out), f"expected no output for {prompt!r}")

    def test_slash_commands(self):
        self.assertSilent("/help me with this please")

    def test_bypass_prefix(self):
        self.assertSilent("* add dark mode to the settings page")

    def test_memory_prefix(self):
        self.assertSilent("# always use rg instead of grep")

    def test_short_replies(self):
        for p in ["ok", "yes", "continue", "go ahead", "  ", ""]:
            self.assertSilent(p)

    def test_harness_messages(self):
        self.assertSilent("<task-notification>agent finished its work here</task-notification>")
        self.assertSilent("<command-name>/model</command-name>\n<command-args>opus</command-args>")

    def test_mode_off(self):
        self.assertSilent(ENGLISH, env_extra={"ENGLISH_COACH": "off"})

    def test_mode_off_any_case(self):
        self.assertSilent(ENGLISH, env_extra={"ENGLISH_COACH": " OFF "})

    def test_marker_mode_without_marker(self):
        self.assertSilent(ENGLISH, env_extra={"ENGLISH_COACH": "marker"})


class LanguageDetection(unittest.TestCase):
    def lang_line(self, prompt):
        ctx = context(run(prompt)[1])
        self.assertIsNotNone(ctx, f"expected coaching for {prompt!r}")
        return ctx.splitlines()[2]

    def test_vietnamese_without_accents(self):
        self.assertIn("in Vietnamese", self.lang_line("sua loi dang nhap bi 401"))

    def test_short_vietnamese_without_accents(self):
        self.assertIn("in Vietnamese", self.lang_line("sua loi"))

    def test_english_with_one_vietnamese_word_stays_english(self):
        self.assertIn("only if there are mistakes", self.lang_line("rename the biến count to total"))

    def test_english_with_accented_name_stays_english(self):
        self.assertIn("only if there are mistakes", self.lang_line("update the café menu page"))

    def test_english_sharing_a_few_vietnamese_spellings_stays_english(self):
        self.assertIn("only if there are mistakes", self.lang_line("ask Minh to review the la la land PR"))

    def test_prompt_starting_with_html_tag(self):
        self.assertIn("only if there are mistakes", self.lang_line("<div> is not centered on mobile"))

    def test_japanese(self):
        self.assertIn("in Japanese", self.lang_line("日本語でバグを直して"))

    def test_chinese(self):
        self.assertIn("in Chinese", self.lang_line("修复登录错误的问题"))

    def test_korean(self):
        self.assertIn("in Korean", self.lang_line("로그인 버그를 고쳐 주세요"))

    def test_short_spaceless_replies_are_skipped(self):
        for p in ["はい", "好的", "好的继续"]:
            self.assertIsNone(context(run(p)[1]), p)


class Coaching(unittest.TestCase):
    def test_english_prompt_gets_instruction(self):
        code, out = run(ENGLISH)
        ctx = context(out)
        self.assertEqual(code, 0)
        self.assertIn("C1", ctx)
        self.assertIn("diff", ctx)
        self.assertIn("rewrite", ctx)  # default unclear=rewrite
        self.assertNotIn("Vietnamese", ctx)

    def test_vietnamese_prompt_asks_for_translation(self):
        ctx = context(run(VIETNAMESE)[1])
        self.assertIn("Vietnamese", ctx)
        self.assertIn("English version", ctx)

    def test_short_vietnamese_still_checked(self):
        # Vietnamese packs meaning into few words; 3 words is a real request.
        self.assertIsNotNone(context(run("sửa lỗi đăng nhập")[1]))

    def test_three_word_request_is_checked(self):
        self.assertIsNotNone(context(run("fix the bug")[1]))

    def test_marker_mode_with_marker(self):
        ctx = context(run("en: " + ENGLISH, env_extra={"ENGLISH_COACH": "marker"})[1])
        self.assertIsNotNone(ctx)
        self.assertIn("en:", ctx)

    def test_level_setting(self):
        ctx = context(run(ENGLISH, env_extra={"ENGLISH_COACH_LEVEL": "b2"})[1])
        self.assertIn("B2", ctx)
        self.assertNotIn("C1", ctx)

    def test_repeat_mistakes_get_a_short_note(self):
        self.assertIn("(again)", context(run(ENGLISH)[1]))

    def test_unclear_tip_never_stops(self):
        ctx = context(run(ENGLISH, env_extra={"ENGLISH_COACH_UNCLEAR": "tip"})[1])
        self.assertNotIn("rewrite it", ctx)
        self.assertIn("Never stop", ctx)

    def test_invalid_settings_fall_back_to_defaults(self):
        ctx = context(run(ENGLISH, env_extra={
            "ENGLISH_COACH": "sometimes", "ENGLISH_COACH_LEVEL": "Z9", "ENGLISH_COACH_UNCLEAR": "???"})[1])
        self.assertIn("C1", ctx)
        self.assertIn("rewrite", ctx)

    def test_instruction_is_short(self):
        # ~4 chars per token: keep the injected text around 200 tokens or less.
        ctx = context(run(VIETNAMESE)[1])
        self.assertLess(len(ctx), 900, f"instruction too long: {len(ctx)} chars")


class FailOpen(unittest.TestCase):
    def test_broken_json(self):
        code, out = run(raw_stdin="{not json")
        self.assertEqual((code, out.strip()), (0, ""))

    def test_empty_stdin(self):
        code, out = run(raw_stdin="")
        self.assertEqual((code, out.strip()), (0, ""))

    def test_missing_prompt_field(self):
        code, out = run(raw_stdin=json.dumps({"hook_event_name": "UserPromptSubmit"}))
        self.assertEqual((code, out.strip()), (0, ""))


if __name__ == "__main__":
    unittest.main()
