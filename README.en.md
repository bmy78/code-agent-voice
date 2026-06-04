# Code Agent Voice

[简体中文](README.md) | English

Voice notifications for Codex and Claude Code. It reads agent state changes
through hooks and speaks short prompts through the macOS built-in `say` command.

The script only reads hook payloads and decides whether to announce the event.
It never approves, denies, rewrites, or blocks Codex or Claude Code actions.

## Quick Start

```bash
git clone git@github.com:bmy78/code-agent-voice.git
cd code-agent-voice
python3 install.py all
```

After installation:

- Codex: run `/hooks`, review the added command hooks, and trust them. If the
  hook does not take effect, restart Codex and trust the hooks.
- Claude Code: if the hook is not picked up immediately, restart Claude Code or
  reload settings.

## Install

Install Codex hooks only:

```bash
python3 install.py codex
```

Install Claude Code hooks only:

```bash
python3 install.py claude
```

Install both:

```bash
python3 install.py all
```

The installer writes shared files to:

```text
~/.code-agent-voice/notify.py
~/.code-agent-voice/config.json
```

Depending on the selected target, it updates:

```text
~/.codex/hooks.json
~/.claude/settings.json
```

After Codex installation, run `/hooks` inside Codex, review the added command
hooks, and trust them. If the hook does not take effect, restart Codex and trust
the hooks.
If Claude Code does not pick up the hook immediately, restart Claude Code or
reload settings.

## Support

Currently supported:

- Codex hooks
- Claude Code hooks
- macOS voice output
- Python 3.10 or newer

Not currently supported:

- Native Windows/Linux voice output
- Mobile push notifications
- Slack, Telegram, Webhook, or other external notifications

## Features

- Speaks when Codex asks for approval.
- Speaks when Codex tool execution fails, a turn ends, or a task appears done.
- Speaks when Claude Code asks for approval or waits for user input.
- Speaks when Claude Code tool execution fails or a turn ends.
- Keeps subagent stop, session start, and context compaction quiet by default,
  with config switches available.
- Supports one shared config file and temporary environment-variable mute.
- Uses the macOS built-in `say` command. On other systems it falls back to text
  output on stderr.

## Requirements

- Python 3.10 or newer.
- Codex hooks or Claude Code hooks support.
- macOS for actual voice output through `say`.

## Safety

Code Agent Voice only reads hook payloads and announces status. It never
approves, denies, modifies commands, or blocks Codex or Claude Code behavior.

Before installing, you can review the hook templates in `templates/`. The
installer only merges the corresponding command hooks into `~/.codex/hooks.json`
and/or `~/.claude/settings.json`.

## Test

Print the announcement without speaking:

```bash
echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash"}' \
  | AGENT_VOICE_DRY_RUN=1 python3 notify.py --provider codex
```

```bash
echo '{"hook_event_name":"Notification","notification_type":"permission_prompt"}' \
  | AGENT_VOICE_DRY_RUN=1 python3 notify.py --provider claude
```

Speak through macOS `say`:

```bash
echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash"}' \
  | python3 ~/.code-agent-voice/notify.py --provider codex
```

```bash
echo '{"hook_event_name":"Notification","notification_type":"permission_prompt"}' \
  | python3 ~/.code-agent-voice/notify.py --provider claude
```

## Configuration

The installer creates `~/.code-agent-voice/config.json`:

```json
{
  "enabled": true,
  "voice": "Tingting",
  "providers": {
    "codex": {
      "events": {
        "PermissionRequest": true,
        "PostToolUseError": true,
        "StopCompleted": true,
        "StopEnded": true,
        "SubagentStop": false,
        "SessionStart": false,
        "PreCompact": false,
        "PostCompact": false
      },
      "messages": {
        "permission": "Codex 需要你确认操作。",
        "tool_failure": "Codex 执行命令失败。",
        "stop": "Codex 当前回合已结束。",
        "completed": "Codex 已完成当前任务。",
        "subagent_stop": "Codex 子 Agent 已结束。",
        "session_start": "Codex 会话已开始。",
        "pre_compact": "Codex 即将整理上下文。",
        "post_compact": "Codex 已整理上下文。"
      }
    },
    "claude": {
      "events": {
        "Notification": {
          "permission_prompt": true,
          "idle_prompt": true
        },
        "PermissionRequest": true,
        "PostToolUseFailure": true,
        "Stop": true,
        "SubagentStop": false,
        "SessionStart": false,
        "PreCompact": false,
        "PostCompact": false
      },
      "messages": {
        "permission": "Claude Code 需要你确认操作。",
        "idle": "Claude Code 正在等待你的输入。",
        "tool_failure": "Claude Code 执行工具失败。",
        "stop": "Claude Code 当前回合已结束。",
        "subagent_stop": "Claude Code 子 Agent 已结束。",
        "session_start": "Claude Code 会话已开始。",
        "pre_compact": "Claude Code 即将整理上下文。",
        "post_compact": "Claude Code 已整理上下文。"
      }
    }
  }
}
```

Changes to `~/.code-agent-voice/config.json` take effect on the next hook run. No restart is required.

`SubagentStop` is disabled by default to avoid noisy announcements during complex tasks. Set it to `true` if you want subagent completion reminders.

Hook commands use `--provider codex` or `--provider claude` to identify the source. `AGENT_VOICE_PROVIDER` remains supported as a compatibility fallback.

Temporarily mute all announcements:

```bash
AGENT_VOICE_MUTE=1
```

These values enable mute: `1`, `true`, `yes`, and `on`. Other values, or an
unset variable, do not mute announcements.

Legacy project variables are also supported:

```bash
CODEX_AGENT_VOICE_MUTE=1   # Mute only under the Codex provider
CLAUDE_AGENT_VOICE_MUTE=1  # Mute only under the Claude provider
```

Change the macOS voice:

```bash
echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash"}' \
  | AGENT_VOICE=Meijia python3 notify.py --provider codex
```

```bash
echo '{"hook_event_name":"Notification","notification_type":"permission_prompt"}' \
  | AGENT_VOICE=Meijia python3 notify.py --provider claude
```

## What It Says

- Codex approval request: `Codex 需要你确认操作。`
- Codex tool error: `Codex 执行命令失败。`
- Codex turn ended: `Codex 当前回合已结束。`
- Codex task completed: `Codex 已完成当前任务。`
- Claude Code approval request: `Claude Code 需要你确认操作。`
- Claude Code waiting for input: `Claude Code 正在等待你的输入。`
- Claude Code tool failure: `Claude Code 执行工具失败。`
- Claude Code turn ended: `Claude Code 当前回合已结束。`

## FAQ

### No sound?

- Make sure you are on macOS.
- Run `say -v '?'` to see available voices.
- Use `AGENT_VOICE_DRY_RUN=1` first to confirm the script prints a message.
- For Codex, run `/hooks` and trust the hooks. If it still does not work,
  restart Codex and trust the hooks.
- For Claude Code, restart Claude Code or reload settings.

### Do config changes require a restart?

No. Changes to `~/.code-agent-voice/config.json` take effect on the next hook
run.

### Can I customize the spoken messages?

Yes. Edit the `messages` fields in `~/.code-agent-voice/config.json`.

## Uninstall

Remove shared files:

```bash
rm -rf ~/.code-agent-voice
```

Then edit `~/.codex/hooks.json` and/or `~/.claude/settings.json`, removing hook
groups whose command points to `~/.code-agent-voice/notify.py`.
