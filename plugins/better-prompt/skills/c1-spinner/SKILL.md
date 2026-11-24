---
description: Show C1 English words and example sentences in the Claude Code spinner while you wait. Use install, remove or status.
disable-model-invocation: true
argument-hint: "[install | install --mix | remove | status]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spinner.py *)
---

Run this command exactly (an empty argument means install):

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spinner.py $ARGUMENTS
```

Then tell the user the result in one or two short lines. Do nothing else.
