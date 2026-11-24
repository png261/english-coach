#!/usr/bin/env python3
"""Show or change English Coach settings, saved in ~/.claude/english-coach/config.json.

Usage: settings.py [show]
       settings.py level|mode|unclear|log [VALUE]    (no VALUE: show it)
       settings.py pause | resume
Changes apply from your next prompt; no restart needed.
"""

import sys

import common

SOURCES = {"env": "from {env}", "paused": "paused", "command": "", "default": "default"}


def why_off(source, name):
    if source == "env":
        return f"{common.ENV[name]}=off is set in your environment."
    if source == "paused":
        return "English Coach is paused. Run /english-coach:resume."
    return "mode is set to off. Run /english-coach:settings mode always."


def show(config):
    for name in common.CHOICES:
        value, source = common.setting(name, config)
        note = SOURCES[source].format(env=common.ENV[name])
        print(f"{name:8} {value}" + (f"   ({note})" if note else ""))


def main(args):
    config = common.load_config()
    command = args[0].lower() if args else "show"
    if command == "show":
        show(config)
    elif command == "pause":
        config["paused"] = True
        common.save_config(config)
        print("⏸ English Coach is paused. Run /english-coach:resume to turn it back on.")
    elif command == "resume":
        config.pop("paused", None)
        common.save_config(config)
        mode, source = common.setting("mode", config)
        if mode == "off":
            print("Note: English Coach is still off. " + why_off(source, "mode"))
        else:
            print("▶ English Coach is on again.")
    elif command in common.CHOICES:
        if len(args) < 2:
            print(f"{command}: {common.setting(command, config)[0]}")
            return
        value = common.pick(command, args[1])
        if not value:
            sys.exit(f"✘ {command} must be one of: {', '.join(common.CHOICES[command])}. Nothing was changed.")
        config[command] = value
        common.save_config(config)
        print(f"✔ {command} is now {value}. It applies from your next prompt.")
        effective, source = common.setting(command, config)
        if effective != value:
            print("Note: English Coach is still off. " + why_off(source, command))
    else:
        sys.exit(f"Unknown command {command!r}. Use: show | level | mode | unclear | log | pause | resume")


if __name__ == "__main__":
    main(sys.argv[1:])
