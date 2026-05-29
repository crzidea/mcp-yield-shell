"""Platform-isolated subprocess spawn helpers."""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from typing import Any


async def spawn_process(
    command: str,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> asyncio.subprocess.Process:
    """Spawn a subprocess shell command with stdout/stderr/stdin pipes.

    On POSIX, starts a new session so the shell and children form a
    process group that can be terminated together.
    """
    kwargs: dict[str, Any] = {
        "stdout": asyncio.subprocess.PIPE,
        "stderr": asyncio.subprocess.PIPE,
        "stdin": asyncio.subprocess.PIPE,
    }
    if cwd:
        kwargs["cwd"] = cwd
    if env:
        kwargs["env"] = env
    if sys.platform != "win32":
        kwargs["start_new_session"] = True

    proc = await asyncio.create_subprocess_shell(command, **kwargs)
    return proc


def get_signal(name: str) -> signal.Signals | None:
    """Map a signal name string to its OS signal value, or return None."""
    name = name.upper()
    if not name.startswith("SIG"):
        name = f"SIG{name}"
    try:
        return signal.Signals[name]
    except (KeyError, ValueError):
        return None


async def terminate_process(proc: asyncio.subprocess.Process) -> None:
    """Send SIGTERM (or equivalent) to the process group."""
    if sys.platform == "win32":
        proc.terminate()
    else:
        pid = proc.pid
        if pid is not None:
            try:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                proc.terminate()


async def kill_process(proc: asyncio.subprocess.Process) -> None:
    """Force kill the process group."""
    if sys.platform == "win32":
        proc.kill()
    else:
        pid = proc.pid
        if pid is not None:
            try:
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                proc.kill()
