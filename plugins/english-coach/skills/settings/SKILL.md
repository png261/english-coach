---
description: Show or change English Coach settings: level, mode (always, marker, off), unclear (rewrite, tip) and log (on, off).
disable-model-invocation: true
argument-hint: "[show | level C1 | mode marker | unclear tip | log off]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py *)
---

Run this command exactly:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py $ARGUMENTS
```

Then show the user the result as it is, in a short code block if it has several lines. Do nothing else.
