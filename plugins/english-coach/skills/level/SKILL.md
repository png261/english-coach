---
description: Set your English Coach target level (B2, C1 or C2). No argument shows the current level.
disable-model-invocation: true
argument-hint: "[B2 | C1 | C2]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py *)
---

Run this command exactly:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py level $ARGUMENTS
```

Then tell the user the result in one or two short lines. Do nothing else.
