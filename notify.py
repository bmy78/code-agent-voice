#!/usr/bin/env python3
"""Voice notifier for coding agents such as Codex and Claude Code."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path.home() / ".code-agent-voice" / "config.json"
SUPPORTED_PROVIDERS = {"codex", "claude"}
TRUE_VALUES = {"1", "true", "yes", "on"}
LEGACY_MUTE_ENV = {
    "codex": "CODEX_AGENT_VOICE_MUTE",
    "claude": "CLAUDE_AGENT_VOICE_MUTE",
}
LEGACY_VOICE_ENV = ("CODEX_AGENT_VOICE", "CLAUDE_AGENT_VOICE")
DEFAULT_MESSAGES = {
    "codex": {
        "permission": "Codex 需要你确认操作。",
        "tool_failure": "Codex 执行命令失败。",
        "stop": "Codex 当前回合已结束。",
        "completed": "Codex 已完成当前任务。",
        "subagent_stop": "Codex 子 Agent 已结束。",
        "session_start": "Codex 会话已开始。",
        "pre_compact": "Codex 即将整理上下文。",
        "post_compact": "Codex 已整理上下文。",
    },
    "claude": {
        "permission": "Claude Code 需要你确认操作。",
        "idle": "Claude Code 正在等待你的输入。",
        "tool_failure": "Claude Code 执行工具失败。",
        "stop": "Claude Code 当前回合已结束。",
        "subagent_stop": "Claude Code 子 Agent 已结束。",
        "session_start": "Claude Code 会话已开始。",
        "pre_compact": "Claude Code 即将整理上下文。",
        "post_compact": "Claude Code 已整理上下文。",
    },
}
DEFAULT_CONFIG = {
    "enabled": True,
    "voice": "Tingting",
    "providers": {
        "codex": {
            "messages": DEFAULT_MESSAGES["codex"],
            "events": {
                "PermissionRequest": True,
                "PostToolUseError": True,
                "StopCompleted": True,
                "StopEnded": True,
                "SubagentStop": False,
                "SessionStart": False,
                "PreCompact": False,
                "PostCompact": False,
            },
        },
        "claude": {
            "messages": DEFAULT_MESSAGES["claude"],
            "events": {
                "Notification": {
                    "permission_prompt": True,
                    "idle_prompt": True,
                },
                "PermissionRequest": True,
                "PostToolUseFailure": True,
                "Stop": True,
                "SubagentStop": False,
                "SessionStart": False,
                "PreCompact": False,
                "PostCompact": False,
            },
        },
    },
}


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_CONFIG
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG
    if not isinstance(data, dict):
        return DEFAULT_CONFIG
    return merge_config(data)


def merge_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    merged["enabled"] = bool(config.get("enabled", merged["enabled"]))
    if "voice" in config:
        merged["voice"] = str(config["voice"])

    providers = config.get("providers")
    if isinstance(providers, dict):
        for provider, provider_config in providers.items():
            if provider not in merged["providers"] or not isinstance(provider_config, dict):
                continue
            events = provider_config.get("events")
            if isinstance(events, dict):
                merge_events(merged["providers"][provider]["events"], events)
            messages = provider_config.get("messages")
            if isinstance(messages, dict):
                merge_messages(merged["providers"][provider]["messages"], messages)
    return merged


def merge_events(target: dict[str, Any], events: dict[str, Any]) -> None:
    for key, value in events.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key].update(
                {nested_key: bool(nested_value) for nested_key, nested_value in value.items()}
            )
            continue
        target[key] = bool(value)


def merge_messages(target: dict[str, str], messages: dict[str, Any]) -> None:
    for key, value in messages.items():
        if key in target:
            target[key] = str(value)


def provider_from_env(env: dict[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    return str(values.get("AGENT_VOICE_PROVIDER") or "").lower()


def is_muted(provider: str, env: dict[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    if str(values.get("AGENT_VOICE_MUTE", "")).lower() in TRUE_VALUES:
        return True
    legacy_name = LEGACY_MUTE_ENV.get(provider)
    if not legacy_name:
        return False
    return str(values.get(legacy_name, "")).lower() in TRUE_VALUES


def looks_complete(text: str) -> bool:
    complete_words = ("完成", "已完成", "done", "fixed", "implemented", "通过测试")
    lowered = text.lower()
    return any(word in lowered for word in complete_words)


def codex_failed_tool_response(response: Any) -> bool:
    if not isinstance(response, dict):
        return False
    if response.get("error") or response.get("is_error") is True:
        return True
    exit_code = response.get("exit_code")
    if isinstance(exit_code, int) and exit_code != 0:
        return True
    status = str(response.get("status") or "").lower()
    return status in {"error", "failed", "failure"}


def event_enabled(events: dict[str, Any], event_key: str) -> bool:
    return bool(events.get(event_key, True))


def notification_enabled(events: dict[str, Any], notification_key: str) -> bool:
    notification = events.get("Notification", {})
    if not isinstance(notification, dict):
        return True
    return bool(notification.get(notification_key, True))


def build_message(
    event: dict[str, Any],
    provider: str | None = None,
    config: dict[str, Any] | None = None,
    env: dict[str, str] | None = None,
) -> str | None:
    """Build a spoken message for the provider selected by hook command env."""
    provider = (provider or provider_from_env(env)).lower()
    if provider not in SUPPORTED_PROVIDERS:
        return None

    config = merge_config(config or load_config())
    if not config.get("enabled", True) or is_muted(provider, env):
        return None

    provider_config = config["providers"][provider]
    if provider == "codex":
        return build_codex_message(event, provider_config)
    return build_claude_message(event, provider_config)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Speak a code-agent hook notification.")
    parser.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_PROVIDERS),
        help="Hook provider. Falls back to AGENT_VOICE_PROVIDER when omitted.",
    )
    return parser.parse_args(argv)


def build_codex_message(event: dict[str, Any], provider_config: dict[str, Any]) -> str | None:
    name = str(event.get("hook_event_name") or "")
    events = provider_config["events"]
    messages = provider_config["messages"]

    if name == "PermissionRequest":
        return messages["permission"] if event_enabled(events, "PermissionRequest") else None

    if name == "PostToolUse":
        if not codex_failed_tool_response(event.get("tool_response")):
            return None
        return messages["tool_failure"] if event_enabled(events, "PostToolUseError") else None

    if name == "Stop":
        last_message = str(event.get("last_assistant_message") or "")
        if looks_complete(last_message):
            return messages["completed"] if event_enabled(events, "StopCompleted") else None
        return messages["stop"] if event_enabled(events, "StopEnded") else None

    if name == "SubagentStop":
        return messages["subagent_stop"] if event_enabled(events, "SubagentStop") else None
    if name == "SessionStart":
        return messages["session_start"] if event_enabled(events, "SessionStart") else None
    if name == "PreCompact":
        return messages["pre_compact"] if event_enabled(events, "PreCompact") else None
    if name == "PostCompact":
        return messages["post_compact"] if event_enabled(events, "PostCompact") else None
    return None


def build_claude_message(event: dict[str, Any], provider_config: dict[str, Any]) -> str | None:
    name = str(event.get("hook_event_name") or "")
    events = provider_config["events"]
    messages = provider_config["messages"]

    if name == "Notification":
        kind = str(event.get("notification_type") or event.get("matcher") or event.get("type") or "")
        if kind == "permission_prompt":
            return messages["permission"] if notification_enabled(events, "permission_prompt") else None
        if kind == "idle_prompt":
            return messages["idle"] if notification_enabled(events, "idle_prompt") else None
        return None

    if name == "PermissionRequest":
        return messages["permission"] if event_enabled(events, "PermissionRequest") else None
    if name == "PostToolUseFailure":
        return messages["tool_failure"] if event_enabled(events, "PostToolUseFailure") else None
    if name == "Stop":
        return messages["stop"] if event_enabled(events, "Stop") else None
    if name == "SubagentStop":
        return messages["subagent_stop"] if event_enabled(events, "SubagentStop") else None
    if name == "SessionStart":
        return messages["session_start"] if event_enabled(events, "SessionStart") else None
    if name == "PreCompact":
        return messages["pre_compact"] if event_enabled(events, "PreCompact") else None
    if name == "PostCompact":
        return messages["post_compact"] if event_enabled(events, "PostCompact") else None
    return None


def read_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def voice_name(config: dict[str, Any], env: dict[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    for name in ("AGENT_VOICE", *LEGACY_VOICE_ENV):
        value = values.get(name)
        if value:
            return str(value)
    return str(config.get("voice", "Tingting"))


def speak(message: str, config: dict[str, Any] | None = None) -> None:
    if os.environ.get("AGENT_VOICE_DRY_RUN"):
        print(message)
        return

    config = merge_config(config or load_config())
    if platform.system() == "Darwin":
        subprocess.run(
            ["say", "-v", voice_name(config), message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return
    print(message, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config = load_config()
    message = build_message(read_event(), provider=args.provider, config=config, env=os.environ)
    if message:
        speak(message, config=config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
