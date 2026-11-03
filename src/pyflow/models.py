from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from pyflow.errors import WorkflowValidationError
from pyflow.graph import compute_layers

TaskFunction = Callable[[Mapping[str, Any], Mapping[str, Any]], Any]


@dataclass(frozen=True)
class Task:
    """Zadanie: nazwa, funkcja function(inputs, params) i zależności."""

    name: str
    function: TaskFunction
    dependencies: frozenset[str] = frozenset()
    params: Mapping[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise WorkflowValidationError("Nazwa zadania nie może być pusta")

        deps = frozenset(self.dependencies)  # kopia
        if self.name in deps:
            raise WorkflowValidationError(
                f"Zadanie '{self.name}' nie może zależeć od samego siebie"
            )

        # frozen=True zabrania self.x = ..., więc piszemy przez object.__setattr__
        object.__setattr__(self, "dependencies", deps)
        object.__setattr__(self, "params", MappingProxyType(dict(self.params)))


class Workflow:
    """Zbiór zadań przechowywanych po nazwie."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    @property
    def tasks(self) -> Mapping[str, Task]:
        return MappingProxyType(self._tasks)  # tylko do odczytu

    def add_task(self, task: Task) -> None:
        if task.name in self._tasks:
            raise WorkflowValidationError(f"Duplikat nazwy zadania: '{task.name}'")
        self._tasks[task.name] = task

    def validate(self) -> None:
        # 1) brakujące zależności
        for name in sorted(self._tasks):
            missing = sorted(
                d for d in self._tasks[name].dependencies if d not in self._tasks
            )
            if missing:
                raise WorkflowValidationError(
                    f"Zadanie '{name}' zależy od niezarejestrowanych zadań: {missing}"
                )
        # 2) cykle (compute_layers rzuci wyjątek, jeśli cykl istnieje)
        compute_layers({n: t.dependencies for n, t in self._tasks.items()})