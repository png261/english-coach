#!/usr/bin/env python3
"""Put C1 English words in the Claude Code spinner, or take them out again.

Usage: spinner.py [install [--mix] | remove | status]   (default: install)

install  sets spinnerVerbs and spinnerTipsOverride in ~/.claude/settings.json
         (--mix keeps Claude Code's built-in tips alongside the C1 tips)
remove   restores whatever those two settings were before install
Your previous values are saved in ~/.claude/english-coach-spinner-backup.json.
ENGLISH_COACH_SETTINGS overrides the settings path (used by tests).
"""

import json
import os
import sys
from pathlib import Path

KEYS = ("spinnerVerbs", "spinnerTipsOverride")
WORDS_FILE = Path(__file__).resolve().parent.parent / "data/c1-spinner.json"
MISSING = "__missing__"


def paths():
    settings = Path(os.environ.get("ENGLISH_COACH_SETTINGS")
                    or Path.home() / ".claude" / "settings.json")
    return settings, settings.parent / "english-coach-spinner-backup.json"


def load(path):
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except ValueError:
        sys.exit(f"✘ {path} is not valid JSON. Fix it first; nothing was changed.")
    if not isinstance(data, dict):
        sys.exit(f"✘ {path} is not a JSON object; nothing was changed.")
    return data


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def install(mix):
    settings_path, backup_path = paths()
    settings = load(settings_path)
    words = json.loads(WORDS_FILE.read_text(encoding="utf-8"))
    if not backup_path.exists():  # keep the user's original values, not ours
        save(backup_path, {k: settings.get(k, MISSING) for k in KEYS})
    settings["spinnerVerbs"] = {"mode": "replace", "verbs": words["verbs"]}
    settings["spinnerTipsOverride"] = {"excludeDefault": not mix, "tips": words["tips"]}
    save(settings_path, settings)
    print(f"✔ Installed {len(words['verbs'])} C1 spinner verbs and {len(words['tips'])} C1 tips "
          f"in {settings_path}. Restart Claude Code if you don't see them yet.")


def remove():
    settings_path, backup_path = paths()
    if not backup_path.exists():
        print("C1 spinner is not installed; nothing to remove.")
        return
    settings = load(settings_path)
    for key, value in load(backup_path).items():
        if value == MISSING:
            settings.pop(key, None)
        else:
            settings[key] = value
    save(settings_path, settings)
    backup_path.unlink()
    print("✔ Removed the C1 spinner and restored your previous spinner settings.")


def status():
    print("C1 spinner is installed." if paths()[1].exists() else "C1 spinner is not installed.")


def main(args):
    command = args[0] if args else "install"
    if command == "install":
        install(mix="--mix" in args[1:])
    elif command == "remove":
        remove()
    elif command == "status":
        status()
    else:
        sys.exit(f"Unknown command {command!r}. Use: install [--mix] | remove | status")


if __name__ == "__main__":
    main(sys.argv[1:])
