"""Tests for /english-coach:level, :pause, :resume and :settings. Run: python3 -m unittest discover -s tests"""

import json
import unittest

from helpers import Sandbox

PROMPT = "please refactor the login handler"


class Settings(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def test_defaults(self):
        code, out = self.box.run("settings.py")
        self.assertEqual(code, 0)
        self.assertIn("level    C1   (default)", out)
        self.assertIn("mode     always", out)

    def test_level_changes_coaching(self):
        code, out = self.box.run("settings.py", "level", "b2")
        self.assertEqual(code, 0)
        self.assertIn("level is now B2", out)
        ctx = self.box.coach(PROMPT)
        self.assertIn("target B2", ctx)
        self.assertEqual(json.loads((self.box.home / "config.json").read_text())["level"], "B2")

    def test_level_without_value_shows_it(self):
        self.assertIn("level: C1", self.box.run("settings.py", "level")[1])

    def test_invalid_value_changes_nothing(self):
        code, out = self.box.run("settings.py", "level", "A1")
        self.assertNotEqual(code, 0)
        self.assertIn("B2, C1, C2", out)
        self.assertFalse((self.box.home / "config.json").exists())

    def test_command_beats_environment(self):
        self.box.run("settings.py", "level", "C2")
        self.assertIn("target C2", self.box.coach(PROMPT, env={"ENGLISH_COACH_LEVEL": "B2"}))

    def test_environment_used_without_command(self):
        self.assertIn("target B2", self.box.coach(PROMPT, env={"ENGLISH_COACH_LEVEL": "B2"}))

    def test_pause_and_resume(self):
        self.box.run("settings.py", "pause")
        self.assertIsNone(self.box.coach(PROMPT))
        self.assertIn("paused", self.box.run("settings.py")[1])
        code, out = self.box.run("settings.py", "resume")
        self.assertIn("on again", out)
        self.assertIsNotNone(self.box.coach(PROMPT))

    def test_pause_beats_environment_always(self):
        self.box.run("settings.py", "pause")
        self.assertIsNone(self.box.coach(PROMPT, env={"ENGLISH_COACH": "always"}))

    def test_environment_off_always_wins(self):
        self.box.run("settings.py", "mode", "always")
        self.assertIsNone(self.box.coach(PROMPT, env={"ENGLISH_COACH": "off"}))
        out = self.box.run("settings.py", "resume", env={"ENGLISH_COACH": "off"})[1]
        self.assertIn("ENGLISH_COACH=off", out)

    def test_mode_marker(self):
        self.box.run("settings.py", "mode", "marker")
        self.assertIsNone(self.box.coach(PROMPT))
        self.assertIsNotNone(self.box.coach("en: " + PROMPT))

    def test_broken_config_is_ignored(self):
        (self.box.home / "config.json").write_text("{ broken")
        self.assertIn("target C1", self.box.coach(PROMPT))

    def test_unknown_command(self):
        code, out = self.box.run("settings.py", "explode")
        self.assertNotEqual(code, 0)
        self.assertIn("pause", out)


if __name__ == "__main__":
    unittest.main()
