# Code Agent Voice

简体中文 | [English](README.en.md)

给 Codex 和 Claude Code 用的语音提醒小助手。它通过 hooks 读取 agent 状态变化，并用 macOS
自带的 `say` 命令播报简短提示。

脚本只读取 hook payload，并根据事件类型决定是否播报。它不会审批、拒绝、改写或阻塞 Codex
或 Claude Code 的任何行为。

## 快速开始

```bash
git clone git@github.com:bmy78/code-agent-voice.git
cd code-agent-voice
python3 install.py all
```

安装后：

- Codex：运行 `/hooks`，检查新增 command hooks，并选择 trust。如未生效，重启 Codex 并 trust。
- Claude Code：如果没有立刻加载新 hook，请重启 Claude Code 或重新加载设置。

## 安装

只安装 Codex：

```bash
python3 install.py codex
```

只安装 Claude Code：

```bash
python3 install.py claude
```

两个都安装：

```bash
python3 install.py all
```

安装脚本会把共享文件写入：

```text
~/.code-agent-voice/notify.py
~/.code-agent-voice/config.json
```

并按选择更新：

```text
~/.codex/hooks.json
~/.claude/settings.json
```

Codex 安装后，在 Codex 里运行 `/hooks`，检查新增 command hooks，并选择 trust。
如未生效，重启 Codex 并 trust。
Claude Code 如果没有立刻加载新 hook，请重启 Claude Code 或重新加载设置。

## 支持范围

当前支持：

- Codex hooks
- Claude Code hooks
- macOS 语音播报
- Python 3.10 或更高版本

暂不支持：

- Windows/Linux 原生语音播报
- 手机推送
- Slack、Telegram、Webhook 等外部通知

## 功能

- Codex 请求审批时播报。
- Codex 工具失败、回合结束、任务完成时播报。
- Claude Code 请求审批或等待输入时播报。
- Claude Code 工具失败、回合结束时播报。
- 子 Agent 结束、会话开始、上下文压缩默认不播报，可通过配置开启。
- 支持统一配置文件和临时静音环境变量。
- macOS 上使用系统自带 `say` 命令；其他系统退回到 stderr 文本输出。

## 环境要求

- Python 3.10 或更高版本。
- Codex hooks 或 Claude Code hooks 支持。
- macOS 才能实际语音播报。

## 安全说明

Code Agent Voice 只读取 hook payload 并播报状态。它不会审批、拒绝、修改命令，也不会阻塞 Codex
或 Claude Code 的行为。

安装前可以查看 `templates/` 目录里的 hook 模板，安装器只会把对应 command hooks 合并进
`~/.codex/hooks.json` 和/或 `~/.claude/settings.json`。

## 测试

只看文案、不出声：

```bash
echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash"}' \
  | AGENT_VOICE_DRY_RUN=1 python3 notify.py --provider codex
```

```bash
echo '{"hook_event_name":"Notification","notification_type":"permission_prompt"}' \
  | AGENT_VOICE_DRY_RUN=1 python3 notify.py --provider claude
```

实际语音播报：

```bash
echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash"}' \
  | python3 ~/.code-agent-voice/notify.py --provider codex
```

```bash
echo '{"hook_event_name":"Notification","notification_type":"permission_prompt"}' \
  | python3 ~/.code-agent-voice/notify.py --provider claude
```

## 配置

安装脚本会创建 `~/.code-agent-voice/config.json`：

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

修改 `~/.code-agent-voice/config.json` 后无需重启，下一次 hook 触发时自动生效。

`SubagentStop` 默认关闭，避免复杂任务中频繁播报；如果你希望听到子 Agent 完成提醒，可以改为 `true`。

hook command 使用 `--provider codex` 或 `--provider claude` 区分来源；`AGENT_VOICE_PROVIDER` 仍作为兼容 fallback 支持。

临时关闭所有语音播报：

```bash
AGENT_VOICE_MUTE=1
```

这些值会触发静音：`1`、`true`、`yes`、`on`。其他值或未设置时不会静音。

兼容旧项目变量：

```bash
CODEX_AGENT_VOICE_MUTE=1   # 只在 Codex provider 下静音
CLAUDE_AGENT_VOICE_MUTE=1  # 只在 Claude provider 下静音
```

切换 macOS 语音：

```bash
echo '{"hook_event_name":"PermissionRequest","tool_name":"Bash"}' \
  | AGENT_VOICE=Meijia python3 notify.py --provider codex
```

```bash
echo '{"hook_event_name":"Notification","notification_type":"permission_prompt"}' \
  | AGENT_VOICE=Meijia python3 notify.py --provider claude
```

## 播报文案

- Codex 审批请求：`Codex 需要你确认操作。`
- Codex 工具错误：`Codex 执行命令失败。`
- Codex 回合结束：`Codex 当前回合已结束。`
- Codex 任务完成：`Codex 已完成当前任务。`
- Claude Code 审批请求：`Claude Code 需要你确认操作。`
- Claude Code 等待输入：`Claude Code 正在等待你的输入。`
- Claude Code 工具失败：`Claude Code 执行工具失败。`
- Claude Code 回合结束：`Claude Code 当前回合已结束。`

## 常见问题

### 没声音怎么办？

- 确认当前系统是 macOS。
- 运行 `say -v '?'` 查看可用 voice。
- 先用 `AGENT_VOICE_DRY_RUN=1` 确认脚本能输出文案。
- Codex 用户运行 `/hooks` 并 trust；如未生效，重启 Codex 并 trust。
- Claude Code 用户重启 Claude Code 或重新加载设置。

### 修改配置后要重启吗？

不用。修改 `~/.code-agent-voice/config.json` 后，下一次 hook 触发时自动生效。

### 可以改播报文案吗？

可以。编辑 `~/.code-agent-voice/config.json` 里的 `messages` 字段即可。

## 卸载

删除共享文件：

```bash
rm -rf ~/.code-agent-voice
```

然后编辑 `~/.codex/hooks.json` 和/或 `~/.claude/settings.json`，删除 command
指向 `~/.code-agent-voice/notify.py` 的 hook groups。
