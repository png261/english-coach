#!/usr/bin/env python3
"""Measure how many tokens the same developer text costs in Vietnamese vs English.

Method: ask Claude to repeat each text exactly, then read `output_tokens` from
`claude -p --output-format json`. Output tokens equal the tokens of the text
itself (plus ~0-2 for formatting), and each run is checked for an exact copy.
Uses your Claude Code login; ~8 short calls. Run: python3 experiments/vi_vs_en_tokens.py [model]
"""

import json
import subprocess
import sys
from pathlib import Path

MODEL = sys.argv[1] if len(sys.argv) > 1 else "opus"
PAIRS = json.loads((Path(__file__).parent / "texts.json").read_text(encoding="utf-8"))


def count(text):
    out = subprocess.run(
        ["claude", "-p", "--model", MODEL, "--setting-sources", "", "--output-format", "json",
         "Repeat the text below exactly, character for character, with nothing before or after it:\n\n" + text],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=180,
    ).stdout
    data = json.loads(out[out.index("{"):])
    return data["usage"]["output_tokens"], data["result"].strip() == text.strip()


rows, total_vi, total_en = [], 0, 0
for pair in PAIRS:
    vi, vi_ok = count(pair["vi"])
    en, en_ok = count(pair["en"])
    total_vi, total_en = total_vi + vi, total_en + en
    rows.append(f"| {pair['name']} | {vi} | {en} | +{(vi / en - 1) * 100:.0f}% | {'✅' if vi_ok and en_ok else '⚠️'} |")

print(f"Model: {MODEL}\n")
print("| Text | Vietnamese | English | Extra | Exact copy |\n|---|---|---|---|---|")
print("\n".join(rows))
print(f"| **Total** | **{total_vi}** | **{total_en}** | **+{(total_vi / total_en - 1) * 100:.0f}%** | |")
