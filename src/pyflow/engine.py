from __future__ import annotations

from time import perf_counter
from types import MappingProxyType
from typing import Any

from pyflow.errors import TaskExecutionError
from pyflow.graph import topological_order
from pyflow.models import Workflow
from pyflow.results import RunResult, TaskState, TaskStatus


def run(workflow: Workflow, *, raise_on_failure: bool = False) -> RunResult:
    """Wykonaj workflow synchronicznie.

    Polityka błędów: po awarii zadania jego (bezpośrednie i pośrednie)
    następniki dostają SKIPPED, a zadania niezależne są DOKOŃCZONE.
    """
    workflow.validate()
    order = topological_order(workflow)

    states = {name: TaskState(name) for name in order}
    outputs: dict[str, Any] = {}
    run_start = perf_counter()

    for name in order:
        task = workflow.tasks[name]
        state = states[name]

        blocked = tuple(
            sorted(
                dep
                for dep in task.dependencies
                if states[dep].status is not TaskStatus.SUCCEEDED
            )
        )
        if blocked:
            state.status = TaskStatus.SKIPPED
            state.skipped_because = blocked
            continue

        inputs = MappingProxyType({dep: outputs[dep] for dep in sorted(task.dependencies)})

        state.status = TaskStatus.RUNNING
        state.started_at = perf_counter()
        try:
            value = task.function(inputs, task.params)
        except Exception as exc:  # błąd kodu użytkownika nie może zatrzymać silnika
            state.finished_at = perf_counter()
            error = TaskExecutionError(name, exc)
            error.__cause__ = exc
            state.status = TaskStatus.FAILED
            state.error = error
        else:
            state.finished_at = perf_counter()
            outputs[name] = value
            state.status = TaskStatus.SUCCEEDED

    result = RunResult(
        outputs=outputs,
        task_states=states,
        order=order,
        total_duration=perf_counter() - run_start,
    )
    if raise_on_failure:
        result.raise_for_failure()
    return result