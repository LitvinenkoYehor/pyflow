from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pyflow.errors import TaskExecutionError


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class TaskState:
    """Stan jednego zadania w trakcie i po przebiegu."""

    name: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: float | None = None   # time.perf_counter()
    finished_at: float | None = None  # time.perf_counter()
    error: TaskExecutionError | None = None
    skipped_because: tuple[str, ...] = ()

    @property
    def duration(self) -> float | None:
        if self.started_at is None or self.finished_at is None:
            return None
        return self.finished_at - self.started_at


@dataclass
class RunResult:
    """Wynik całego przebiegu workflow."""

    outputs: dict[str, Any] = field(default_factory=dict)
    task_states: dict[str, TaskState] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)  # kolejność planu
    total_duration: float = 0.0

    @property
    def succeeded(self) -> bool:
        return all(
            s.status is TaskStatus.SUCCEEDED for s in self.task_states.values()
        )

    @property
    def errors(self) -> dict[str, TaskExecutionError]:
        return {
            n: s.error for n, s in self.task_states.items() if s.error is not None
        }

    def raise_for_failure(self) -> None:
        """Rzuć pierwszy błąd (wg kolejności planu), jeśli jakiś był."""
        for name in self.order:
            error = self.task_states[name].error
            if error is not None:
                raise error