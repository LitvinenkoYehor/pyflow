from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from pyflow.errors import WorkflowValidationError

if TYPE_CHECKING:
    from pyflow.models import Workflow


def compute_layers(deps: Mapping[str, frozenset[str]]) -> list[list[str]]:
    """Algorytm Kahna warstwa po warstwie.

    Zakłada, że wszystkie zależności są zarejestrowane.
    Rzuca WorkflowValidationError, jeśli w grafie jest cykl.
    """
    indegree = {name: len(d) for name, d in deps.items()}
    dependents: dict[str, list[str]] = {name: [] for name in deps}
    for name, d in deps.items():
        for dep in d:
            dependents[dep].append(name)

    current = sorted(n for n, k in indegree.items() if k == 0)
    layers: list[list[str]] = []
    processed = 0

    while current:
        layers.append(current)
        processed += len(current)
        next_ready: list[str] = []
        for name in current:
            for child in dependents[name]:
                indegree[child] -= 1
                if indegree[child] == 0:
                    next_ready.append(child)
        current = sorted(next_ready)

    if processed != len(deps):
        stuck = sorted(n for n, k in indegree.items() if k > 0)
        raise WorkflowValidationError(
            f"Wykryto cykl; zadania zablokowane przez cykl: {stuck}"
        )
    return layers


def execution_layers(workflow: Workflow) -> list[list[str]]:
    workflow.validate()
    return compute_layers({n: t.dependencies for n, t in workflow.tasks.items()})


def topological_order(workflow: Workflow) -> list[str]:
    return [name for layer in execution_layers(workflow) for name in layer]