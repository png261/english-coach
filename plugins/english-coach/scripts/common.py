"""Shared paths and settings for the English Coach scripts.

Settings come from these places, first match wins:
  1. ENGLISH_COACH=off in the environment (the kill switch, e.g. ENGLISH_COACH=off claude)
  2. /english-coach:pause
  3. ~/.claude/english-coach/config.json, written by /english-coach:level and :settings
  4. environment variables (ENGLISH_COACH, ENGLISH_COACH_LEVEL, ...)
  5. the defaults
ENGLISH_COACH_HOME overrides the folder (used by tests).
"""

import json
import os
from pathlib import Path

CHOICES = {
    "mode": ("always", "marker", "off"),
    "level": ("B2", "C1", "C2"),
    "unclear": ("rewrite", "tip"),
    "log": ("on", "off"),
}
DEFAULTS = {"mode": "always", "level": "C1", "unclear": "rewrite", "log": "on"}
ENV = {
    "mode": "ENGLISH_COACH",
    "level": "ENGLISH_COACH_LEVEL",
    "unclear": "ENGLISH_COACH_UNCLEAR",
    "log": "ENGLISH_COACH_LOG",
}


def home():
    return Path(os.environ.get("ENGLISH_COACH_HOME") or Path.home() / ".claude" / "english-coach")


def config_path():
    return home() / "config.json"


def log_path():
    return home() / "mistakes.jsonl"


def pick(name, value):
    """The allowed spelling of value for setting name, or None."""
    value = str(value or "").strip().lower()
    for option in CHOICES[name]:
        if value == option.lower():
            return option
    return None


def load_config():
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save_config(config):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def setting(name, config=None):
    """Return (value, source); source is "env", "paused", "command" or "default"."""
    config = load_config() if config is None else config
    env = pick(name, os.environ.get(ENV[name]))
    if name == "mode":
        if env == "off":
            return "off", "env"
        if config.get("paused") is True:
            return "off", "paused"
    from_command = pick(name, config.get(name))
    if from_command:
        return from_command, "command"
    if env:
        return env, "env"
    return DEFAULTS[name], "default"
