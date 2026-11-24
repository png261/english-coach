---
description: Turn English Coach back on after /english-coach:pause.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py *)
---

Run this command exactly:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py resume
```

Then tell the user the result in one or two short lines. Do nothing else.
