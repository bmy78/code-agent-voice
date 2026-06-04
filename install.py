#!/usr/bin/env python3
"""Install Code Agent Voice hooks for Codex, Claude Code, or both."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys


ROOT = pathlib.Path(__file__).resolve().parent
INSTALL_DIR = pathlib.Path.home() / ".code-agent-voice"
SCRIPT_NAME = "notify.py"
CONFIG_NAME = "config.json"
CODEX_HOOKS_JSON = pathlib.Path.home() / ".codex" / "hooks.json"
CLAUDE_SETTINGS_JSON = pathlib.Path.home() / ".claude" / "settings.json"


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: pathlib.Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def hook_events(config: dict) -> dict:
    events = config.get("hooks", config)
    if not isinstance(events, dict):
        raise ValueError("hooks config must contain a JSON object")
    return events


def unique_groups(groups) -> list:
    unique = []
    for group in groups:
        if group not in unique:
            unique.append(group)
    return unique


def normalize_group(group: dict, provider: str) -> dict:
    normalized = json.loads(json.dumps(group))
    command = provider_command(provider)
    for hook in normalized.get("hooks", []):
        if hook.get("type") == "command":
            hook["command"] = command
    return normalized


def merge_hooks(current: dict, addition: dict, provider: str) -> dict:
    merged = {}
    for event_name, groups in hook_events(current).items():
        if not isinstance(groups, list):
            raise ValueError(f"{event_name} hook groups must be a list")
        merged[event_name] = unique_groups(groups)
    for event_name, groups in hook_events(addition).items():
        existing = merged.setdefault(event_name, [])
        if not isinstance(existing, list):
            raise ValueError(f"{event_name} hook groups must be a list")
        for group in groups:
            normalized = normalize_group(group, provider)
            if normalized not in existing:
                existing.append(normalized)
    return merged


def provider_command(provider: str) -> str:
    return f"python3 {INSTALL_DIR / SCRIPT_NAME} --provider {provider}"


def with_provider_command(template: dict, provider: str) -> dict:
    rewritten = json.loads(json.dumps(template))
    for groups in hook_events(rewritten).values():
        for group in groups:
            for hook in group.get("hooks", []):
                if hook.get("type") == "command":
                    hook["command"] = provider_command(provider)
    return rewritten


def install_shared_files() -> None:
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / SCRIPT_NAME, INSTALL_DIR / SCRIPT_NAME)
    config_path = INSTALL_DIR / CONFIG_NAME
    if not config_path.exists():
        shutil.copy2(ROOT / CONFIG_NAME, config_path)


def install_codex() -> None:
    install_shared_files()
    current = load_json(CODEX_HOOKS_JSON)
    template = load_json(ROOT / "templates" / "codex-hooks.json")
    merged = {"hooks": merge_hooks(current, template, "codex")}
    write_json(CODEX_HOOKS_JSON, merged)
    print(f"Installed Codex hooks in {CODEX_HOOKS_JSON}")


def install_claude() -> None:
    install_shared_files()
    current = load_json(CLAUDE_SETTINGS_JSON)
    template = load_json(ROOT / "templates" / "claude-hooks.json")
    merged = json.loads(json.dumps(current))
    merged["hooks"] = merge_hooks(current.get("hooks", {}), template, "claude")
    write_json(CLAUDE_SETTINGS_JSON, merged)
    print(f"Installed Claude Code hooks in {CLAUDE_SETTINGS_JSON}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install Code Agent Voice hooks.")
    parser.add_argument(
        "target",
        choices=("codex", "claude", "all"),
        help="Install hooks for Codex, Claude Code, or both.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.target in {"codex", "all"}:
        install_codex()
    if args.target in {"claude", "all"}:
        install_claude()
    print(f"Shared files installed in {INSTALL_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
