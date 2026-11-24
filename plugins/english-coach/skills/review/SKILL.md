---
description: Review your recent English mistakes saved by English Coach, and practice the top ones. Optional: number of days (default 7), or "clear" to delete the saved notes.
disable-model-invocation: true
argument-hint: "[days | clear]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py *)
---

Run this command exactly:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review.py $ARGUMENTS
```

If it printed a confirmation or says there are no notes, tell the user in one line and stop.

Otherwise, write a short review in simple English, using only that output:

1. **Top mistakes**: group the notes into the 3–5 mistakes that repeat most. For each one: the rule in one line, how many times it appeared, and one real example as `wrong → right`. Prompts whose original is not English are translations, not mistakes: leave them out of this list.
2. **Useful phrases**: up to 3 good phrases from the translations or level-up tips, if there are any.
3. **Focus**: one line on what to watch this week.
4. **Practice**: 3 short sentences that contain the top mistakes, for the user to fix. Put the answers at the very end, under "Answers".

Do nothing else and use no other tools.
