# Better Prompt

Learn English and better prompting while you work in Claude Code.

On each prompt, Claude first coaches you briefly, then does the task:

- **📝 English**: a diff of your prompt (original → corrected, natural English) with up to 3 one-line notes. Vietnamese prompts get a natural English version.
- **⬆️ Level-up**: at most one more precise word or phrase for your target level (default **C1**), only when it is clearly better.
- **💡 Prompt tip**: at most one tip, only when a missing goal, context, "done when" or constraint would change the result.
- **⚠️ Too vague?** Claude doesn't start. It shows what's missing and asks you to rewrite the prompt yourself.

If your prompt is already good, you see nothing extra.

## Example

```
> what is the different between let and const in javascript, answer short

📝 English
- what is the different between let and const in javascript, answer short
+ What is the difference between let and const in JavaScript? Keep it short.
• "different" is an adjective. After "the", use the noun "difference".
• "Answer short" sounds unnatural. Say "keep it short" or "answer briefly".

⬆️ C1: "Briefly explain the difference between…" sounds more natural.

(…then the normal answer)
```

```
> fix the bug

⚠️ Your request needs more detail. "Fix the bug" doesn't say which bug, so I haven't
started. Please rewrite it and include: what's wrong, where, how to reproduce it,
and how we'll know it's fixed.
```

## Install

In Claude Code:

```
/plugin marketplace add png261/better-prompt
/plugin install better-prompt@better-prompt
/reload-plugins
```

Requires `python3` on your `PATH` (macOS and Linux have it).

## Settings

All optional. Add them to the `env` block of `~/.claude/settings.json`:

```json
{
  "env": {
    "BETTER_PROMPT": "always",
    "BETTER_PROMPT_LEVEL": "C1",
    "BETTER_PROMPT_UNCLEAR": "rewrite"
  }
}
```

| Variable | Values | Default |
|---|---|---|
| `BETTER_PROMPT` | `always`: every real prompt<br>`marker`: only prompts starting with `en:`<br>`off`: disabled | `always` |
| `BETTER_PROMPT_LEVEL` | `B2`, `C1`, `C2` | `C1` |
| `BETTER_PROMPT_UNCLEAR` | `rewrite`: stop and ask you to rewrite<br>`tip`: never stop, just give a tip | `rewrite` |

Turn it off for one session: `BETTER_PROMPT=off claude`

**Always skipped (0 tokens):** slash commands (`/…`), prompts starting with `*` (bypass) or `#`, system messages, and 1–2 word replies like "ok" or "go ahead".

## Cost and speed

- **No extra model call, no waiting.** The hook is a tiny local Python script (~0.03 s) that adds a short instruction. Your session's own model writes the coaching.
- **Measured:** about **+220 input tokens per prompt** (under 1% of a typical Claude Code turn), plus ~150–250 output tokens only when there's something to fix.

## How it works

A `UserPromptSubmit` hook ([`coach.py`](plugins/better-prompt/scripts/coach.py)) reads your prompt, applies the skip rules, detects Vietnamese, and returns the coaching instruction as `additionalContext`. If anything goes wrong it prints nothing, so your prompt always goes through.

## Development

```
python3 -m unittest discover -s tests          # unit tests
claude --plugin-dir ./plugins/better-prompt    # try it without installing
```

## Tiếng Việt

Plugin giúp bạn học tiếng Anh và viết prompt tốt hơn ngay khi dùng Claude Code. Mỗi prompt, Claude sẽ sửa tiếng Anh dạng diff (prompt tiếng Việt sẽ được dịch sang tiếng Anh tự nhiên), gợi ý 1 từ chuẩn C1, và 1 mẹo viết prompt. Nếu prompt quá mơ hồ, Claude sẽ dừng lại và yêu cầu bạn tự viết lại. Không gọi thêm model, không phải chờ, chỉ tốn khoảng 220 token mỗi prompt.

## License

MIT
