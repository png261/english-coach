"""Tests for the C1 spinner installer. Run: python3 -m unittest discover -s tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "plugins/english-coach"
SCRIPT = ROOT / "scripts/spinner.py"
WORDS = json.loads((ROOT / "data/c1-spinner.json").read_text())


class Spinner(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.settings = Path(self.dir.name) / "settings.json"
        self.backup = Path(self.dir.name) / "english-coach-spinner-backup.json"

    def tearDown(self):
        self.dir.cleanup()

    def run_cmd(self, *args):
        env = dict(os.environ, ENGLISH_COACH_SETTINGS=str(self.settings))
        p = subprocess.run([sys.executable, str(SCRIPT), *args],
                           capture_output=True, text=True, env=env, timeout=10)
        return p.returncode, p.stdout + p.stderr

    def read(self):
        return json.loads(self.settings.read_text())

    def test_word_list_is_valid(self):
        self.assertGreaterEqual(len(WORDS["verbs"]), 25)
        self.assertGreaterEqual(len(WORDS["tips"]), 50)
        self.assertTrue(all(isinstance(v, str) and v for v in WORDS["verbs"] + WORDS["tips"]))

    def test_install_into_missing_file(self):
        code, _ = self.run_cmd("install")
        self.assertEqual(code, 0)
        s = self.read()
        self.assertEqual(s["spinnerVerbs"], {"mode": "replace", "verbs": WORDS["verbs"]})
        self.assertEqual(s["spinnerTipsOverride"], {"excludeDefault": True, "tips": WORDS["tips"]})

    def test_no_argument_means_install(self):
        self.assertEqual(self.run_cmd()[0], 0)
        self.assertIn("spinnerVerbs", self.read())

    def test_install_keeps_other_settings(self):
        self.settings.write_text(json.dumps({"model": "opus", "env": {"A": "1"}}))
        self.run_cmd("install")
        s = self.read()
        self.assertEqual(s["model"], "opus")
        self.assertEqual(s["env"], {"A": "1"})

    def test_mix_keeps_builtin_tips(self):
        self.run_cmd("install", "--mix")
        self.assertFalse(self.read()["spinnerTipsOverride"]["excludeDefault"])

    def test_remove_restores_previous_values(self):
        old = {"mode": "append", "verbs": ["Brewing"]}
        self.settings.write_text(json.dumps({"spinnerVerbs": old, "model": "opus"}))
        self.run_cmd("install")
        self.run_cmd("install")  # twice: must not back up our own values
        code, _ = self.run_cmd("remove")
        self.assertEqual(code, 0)
        s = self.read()
        self.assertEqual(s["spinnerVerbs"], old)
        self.assertNotIn("spinnerTipsOverride", s)
        self.assertEqual(s["model"], "opus")
        self.assertFalse(self.backup.exists())

    def test_remove_without_install(self):
        self.settings.write_text(json.dumps({"model": "opus"}))
        code, out = self.run_cmd("remove")
        self.assertEqual(code, 0)
        self.assertEqual(self.read(), {"model": "opus"})
        self.assertIn("not installed", out)

    def test_invalid_json_is_left_untouched(self):
        self.settings.write_text("{ broken")
        code, out = self.run_cmd("install")
        self.assertNotEqual(code, 0)
        self.assertEqual(self.settings.read_text(), "{ broken")
        self.assertIn("not valid JSON", out)

    def test_status(self):
        self.assertIn("not installed", self.run_cmd("status")[1])
        self.run_cmd("install")
        self.assertIn("installed", self.run_cmd("status")[1])

    def test_unknown_command(self):
        code, out = self.run_cmd("explode")
        self.assertNotEqual(code, 0)
        self.assertIn("install", out)


if __name__ == "__main__":
    unittest.main()
