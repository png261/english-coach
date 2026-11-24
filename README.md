# English Coach

**Turn your time with Claude Code into English practice.**

As developers, we now spend hours every day writing to Claude and other AI agents. That's more English writing than most English classes ever ask for. So why not turn that time into practice, and make the agent our English tutor?

English Coach is a Claude Code plugin that does exactly that. Before Claude does your task, it coaches you briefly on the prompt you just wrote:

- **📝 English**: a diff of your prompt (original → corrected, natural English) with up to 3 one-line notes. Vietnamese prompts get a natural English version.
- **⬆️ Level-up**: at most one more precise word or phrase for your target level (default **C1**), only when it is clearly better.
- **💡 Prompt tip**: at most one tip, only when a missing goal, context, "done when" or constraint would change the result.
- **⚠️ Too vague?** Claude doesn't start. It shows what's missing and asks you to rewrite the prompt yourself.

If your prompt is already good, you see nothing extra.

## Why English? It also saves tokens

We measured it. The same developer text costs **77% more tokens in Vietnamese** than in English on Claude Opus 5.5:

| Text | Vietnamese | English | Extra |
|---|---|---|---|
| Bug report prompt | 174 | 95 | +83% |
| Feature request prompt | 148 | 93 | +59% |
| Claude's explanation | 187 | 116 | +61% |
| Code review comment | 164 | 77 | +113% |
| **Total** | **673** | **381** | **+77%** |

That cost applies to everything written in Vietnamese: your prompts, and also Claude's replies, which are usually much longer and stay in the conversation for every later turn. Code, file contents and tool output cost the same in both languages, so the total session difference is smaller than 77%. But the prose part costs much more.

**How it was measured:** Claude repeats each text exactly, and we read `output_tokens` from `claude -p --output-format json`. Each copy is checked to be exact, and the setup is clean (`--setting-sources ''`), because extra settings add hidden tokens that hide the real difference. The texts are in [`experiments/texts.json`](experiments/texts.json). Re-run it yourself:

```
python3 experiments/vi_vs_en_tokens.py opus
```

So writing in English is better for you twice: you practice a skill you need, and your agent uses fewer tokens.

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
> giải thích ngắn gọn sự khác nhau giữa let và const trong javascript

📝 English
- giải thích ngắn gọn sự khác nhau giữa let và const trong javascript
+ Briefly explain the difference between let and const in JavaScript.
• briefly: fits "ngắn gọn" better than "shortly", which means "soon".
• difference between X and Y: the usual way to compare two things.
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
/plugin marketplace add png261/english-coach
/plugin install english-coach@english-coach
/reload-plugins
```

Requires `python3` on your `PATH` (macOS and Linux have it).

## C1 words while you wait (optional)

Replace the spinner text ("Thinking…") and the tip under it with C1 vocabulary for developers:

```
✻ Scrutinizing…
  C1 · mitigate (v): make less serious. "This patch mitigates the risk of data loss."
```

```
/english-coach:c1-spinner                # install: 30 C1 verbs + 60 C1 tips
/english-coach:c1-spinner install --mix  # keep Claude Code's built-in tips too
/english-coach:c1-spinner remove         # restore your previous spinner settings
```

Plugins can't change spinner settings by themselves, so this command writes `spinnerVerbs` and `spinnerTipsOverride` into `~/.claude/settings.json` once. Your old values are backed up and restored by `remove`. The command costs 0 tokens until you run it. The word list is in [`data/c1-spinner.json`](plugins/english-coach/data/c1-spinner.json); edit it and run install again.

## Settings

All optional. Add them to the `env` block of `~/.claude/settings.json`:

```json
{
  "env": {
    "ENGLISH_COACH": "always",
    "ENGLISH_COACH_LEVEL": "C1",
    "ENGLISH_COACH_UNCLEAR": "rewrite"
  }
}
```

| Variable | Values | Default |
|---|---|---|
| `ENGLISH_COACH` | `always`: every real prompt<br>`marker`: only prompts starting with `en:`<br>`off`: disabled | `always` |
| `ENGLISH_COACH_LEVEL` | `B2`, `C1`, `C2` | `C1` |
| `ENGLISH_COACH_UNCLEAR` | `rewrite`: stop and ask you to rewrite<br>`tip`: never stop, just give a tip | `rewrite` |

Turn it off for one session: `ENGLISH_COACH=off claude`

**Always skipped (0 tokens):** slash commands (`/…`), prompts starting with `*` (bypass) or `#`, system messages, and 1–2 word replies like "ok" or "go ahead".

## Cost and speed

- **No extra model call, no waiting.** The hook is a tiny local Python script (~0.03 s) that adds a short instruction. Your session's own model writes the coaching.
- **Measured:** about **+220 input tokens per prompt** (under 1% of a typical Claude Code turn), plus ~150–250 output tokens only when there's something to fix.

## How it works

A `UserPromptSubmit` hook ([`coach.py`](plugins/english-coach/scripts/coach.py)) reads your prompt, applies the skip rules, detects Vietnamese, and returns the coaching instruction as `additionalContext`. If anything goes wrong it prints nothing, so your prompt always goes through.

## Development

```
python3 -m unittest discover -s tests          # unit tests
claude --plugin-dir ./plugins/english-coach    # try it without installing
```

## Tiếng Việt

Lập trình viên giờ dành phần lớn thời gian làm việc với Claude và các AI agent. Vậy sao không biến chính thời gian đó thành giờ học tiếng Anh?

Mỗi prompt, Claude sẽ sửa tiếng Anh của bạn dạng diff (prompt tiếng Việt được chuyển sang tiếng Anh tự nhiên), gợi ý 1 từ chuẩn C1 và 1 mẹo viết prompt. Nếu prompt quá mơ hồ, Claude dừng lại và yêu cầu bạn tự viết lại. Không gọi thêm model, không phải chờ, chỉ tốn khoảng 220 token mỗi prompt.

Theo đo đạc, cùng một nội dung viết bằng tiếng Việt tốn **nhiều hơn 77% token** so với tiếng Anh. Viết prompt bằng tiếng Anh vừa giúp bạn luyện kỹ năng cần thiết, vừa giúp agent tiết kiệm token.

## License

MIT
