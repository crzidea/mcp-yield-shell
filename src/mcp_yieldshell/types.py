"""Types for process status and tool response shapes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProcessStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    TIMED_OUT = "timed_out"
    FAILED = "failed"


@dataclass
class ProcessInfo:
    process_id: str
    pid: int | None
    command: str
    cwd: str
    name: str | None
    status: ProcessStatus
    exit_code: int | None = None
    signal: str | None = None
    started_at: float = 0.0
    ended_at: float | None = None
    duration_ms: float = 0.0
    start_monotonic: float = 0.0


