---
description: Pause English Coach in all sessions until you run /english-coach:resume.
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py *)
---

Run this command exactly:

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/settings.py pause
```

Then tell the user the result in one or two short lines. Do nothing else.
