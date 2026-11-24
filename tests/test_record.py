"""Tests for the Stop hook that saves coaching notes, and for review.py.
Run: python3 -m unittest discover -s tests"""

import json
import unittest
from datetime import datetime, timedelta, timezone

from helpers import Sandbox

COACHING = """📝 **English**
```diff
- Is there anythings i can improve it
+ Is there anything else I can improve in it?
```
- **anything** is never plural.
- Always write **I** as a capital letter.

⬆️ **C1:** *"What else could be improved?"* is shorter.

💡 **Prompt tip:** say what "it" is.

---

Here is the answer."""


def user(text):
    return {"type": "user", "message": {"role": "user", "content": text}}


def assistant(*blocks):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocks)}}


def text(t):
    return {"type": "text", "text": t}


def tool_use():
    return {"type": "tool_use", "id": "t1", "name": "REPL", "input": {}}


def tool_result():
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


class Record(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def stop(self, entries=None, last=None, session="s1", env=None):
        hook = {"hook_event_name": "Stop", "session_id": session}
        if entries is not None:
            path = self.box.home / "transcript.jsonl"
            path.write_text("".join(json.dumps(e) + "\n" for e in entries))
            hook["transcript_path"] = str(path)
        if last is not None:
            hook["last_assistant_message"] = last
        code, out = self.box.run("record.py", stdin=json.dumps(hook), env=env)
        self.assertEqual((code, out), (0, ""))

    def test_saves_coaching(self):
        self.stop([user("Is there anythings i can improve it"), assistant(text(COACHING))])
        [r] = self.box.log()
        self.assertEqual(r["original"], "Is there anythings i can improve it")
        self.assertEqual(r["corrected"], "Is there anything else I can improve in it?")
        self.assertEqual(r["notes"], ["**anything** is never plural.", "Always write **I** as a capital letter."])
        self.assertIn("What else could be improved?", r["level_up"])
        self.assertEqual(r["session"], "s1")

    def test_coaching_before_tool_calls(self):
        self.stop([user("x"), assistant(text(COACHING), tool_use()), tool_result(),
                   assistant(text("Done. All tests pass."))])
        self.assertEqual(len(self.box.log()), 1)

    def test_only_the_latest_turn_counts(self):
        self.stop([user("x"), assistant(text(COACHING)), user("thanks a lot for this"),
                   assistant(text("You're welcome."))])
        self.assertEqual(self.box.log(), [])

    def test_reply_without_coaching(self):
        self.stop([user("x"), assistant(text("📝 English is a section name. No diff here."))])
        self.assertEqual(self.box.log(), [])

    def test_same_turn_saved_once(self):
        entries = [user("x"), assistant(text(COACHING))]
        self.stop(entries)
        self.stop(entries)
        self.assertEqual(len(self.box.log()), 1)

    def test_last_assistant_message_fallback(self):
        self.stop(last=COACHING)
        self.assertEqual(len(self.box.log()), 1)

    def test_log_off(self):
        self.box.run("settings.py", "log", "off")
        self.stop([user("x"), assistant(text(COACHING))])
        self.assertEqual(self.box.log(), [])

    def test_bad_input_is_silent(self):
        for stdin in ["", "not json", "[]", json.dumps({"transcript_path": "/nope/missing.jsonl"})]:
            self.assertEqual(self.box.run("record.py", stdin=stdin), (0, ""))


class Review(unittest.TestCase):
    def setUp(self):
        self.box = Sandbox()

    def tearDown(self):
        self.box.close()

    def write_log(self, *ages_in_days):
        now = datetime.now(timezone.utc)
        lines = [json.dumps({"time": (now - timedelta(days=d)).isoformat(), "session": "s",
                             "original": f"old text {d}", "corrected": f"new text {d}",
                             "notes": [f"note {d}"], "level_up": None}) for d in ages_in_days]
        (self.box.home / "mistakes.jsonl").write_text("\n".join(lines) + "\n")

    def test_empty(self):
        self.assertIn("No coaching notes", self.box.run("review.py")[1])

    def test_recent_notes_only(self):
        self.write_log(1, 3, 20)
        out = self.box.run("review.py")[1]
        self.assertIn("2 coached prompts in the last 7 days", out)
        self.assertIn("old text 1  ->  new text 1", out)
        self.assertIn("• note 3", out)
        self.assertNotIn("text 20", out)
        self.assertIn("text 20", self.box.run("review.py", "30")[1])

    def test_clear(self):
        self.write_log(1)
        self.assertIn("Deleted", self.box.run("review.py", "clear")[1])
        self.assertEqual(self.box.log(), [])


if __name__ == "__main__":
    unittest.main()
