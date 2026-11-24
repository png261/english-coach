"""Run English Coach scripts like Claude Code does, against a temporary folder."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins/english-coach/scripts"


class Sandbox:
    """A temporary ENGLISH_COACH_HOME plus a clean environment."""

    def __init__(self, **env):
        self.dir = tempfile.TemporaryDirectory()
        self.home = Path(self.dir.name)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("ENGLISH_COACH")}
        self.env["ENGLISH_COACH_HOME"] = str(self.home)
        self.env.update(env)

    def run(self, script, *args, stdin="", env=None):
        p = subprocess.run([sys.executable, str(SCRIPTS / script), *args], input=stdin,
                           capture_output=True, text=True, timeout=10,
                           env={**self.env, **(env or {})})
        return p.returncode, p.stdout + p.stderr

    def coach(self, prompt, env=None):
        """The coaching instruction for prompt, or None when the hook stays silent."""
        code, out = self.run("coach.py", stdin=json.dumps({"prompt": prompt}), env=env)
        assert code == 0, out
        return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out.strip() else None

    def log(self):
        path = self.home / "mistakes.jsonl"
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines()]

    def close(self):
        self.dir.cleanup()
