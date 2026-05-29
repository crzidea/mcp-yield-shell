"""Security: command allow/deny, cwd validation, env overlay, and redaction."""

from __future__ import annotations

import os
from pathlib import Path

from .config import Config


def validate_command(config: Config, command: str) -> str | None:
    """Return an error message if the command is denied, else None."""
    if config.deny_command_regex and config.deny_command_regex.search(command):
        return f"Command denied by policy: {command[:80]}"
    if config.allow_command_regex and not config.allow_command_regex.search(command):
        return f"Command not allowed by policy: {command[:80]}"
    return None


def resolve_cwd(config: Config, requested_cwd: str | None) -> tuple[str, str | None]:
    """Resolve and validate cwd. Returns (resolved_path, error_or_None)."""
    target = requested_cwd or config.default_cwd
    try:
        resolved = str(Path(target).resolve())
    except Exception as exc:
        return target, f"Invalid cwd: {exc}"
    if config.allowed_cwd_roots:
        if not any(resolved.startswith(str(Path(r).resolve())) for r in config.allowed_cwd_roots):
            return resolved, f"Cwd not under allowed roots: {resolved}"
    return resolved, None


def build_env(config: Config, overlay: dict[str, str] | None) -> dict[str, str]:
    """Merge overlay into parent env without exposing raw parent env in tool output."""
    env = dict(os.environ)
    if overlay:
        env.update(overlay)
    return env


def redact_text(config: Config, text: str) -> str:
    """Best-effort redaction of sensitive environment values from text."""
    env = os.environ
    for name, value in env.items():
        if config.redact_env_regex.search(name) and value:
            text = text.replace(value, f"[REDACTED:{name}]")
    return text
