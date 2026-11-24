#!/usr/bin/env python3
"""Print the coaching notes English Coach saved, for /english-coach:review.

Usage: review.py [DAYS] | clear     (default: the last 7 days, newest 80 prompts)
"""

import json
import sys
from datetime import datetime, timedelta, timezone

import common

MAX_SHOWN = 80
MAX_TEXT = 200


def short(text):
    text = " / ".join(str(text or "").split("\n"))
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + "…"


def load(days):
    path = common.log_path()
    if not path.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            if datetime.fromisoformat(record["time"]) >= cutoff:
                records.append(record)
        except (ValueError, KeyError, TypeError):
            continue
    return records


def main(args):
    if args and args[0].lower() == "clear":
        path = common.log_path()
        if path.exists():
            path.unlink()
        print("✔ Deleted all saved coaching notes.")
        return
    days = int(args[0]) if args and args[0].isdigit() and int(args[0]) > 0 else 7
    records = load(days)
    if not records:
        print(f"No coaching notes saved in the last {days} days.")
        return
    shown = records[-MAX_SHOWN:]
    extra = f" (newest {len(shown)} shown)" if len(shown) < len(records) else ""
    noun = "prompt" if len(records) == 1 else "prompts"
    print(f"{len(records)} coached {noun} in the last {days} days{extra}:")
    for r in shown:
        print(f"- {short(r.get('original'))}  ->  {short(r.get('corrected'))}")
        for note in r.get("notes") or []:
            print(f"    • {short(note)}")
        if r.get("level_up"):
            print(f"    level-up: {short(r['level_up'])}")


if __name__ == "__main__":
    main(sys.argv[1:])
