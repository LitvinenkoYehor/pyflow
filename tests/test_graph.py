import pytest

from pyflow import (
    Task,
    Workflow,
    WorkflowValidationError,
    execution_layers,
    topological_order,
)


def make_task(name, *deps):
    return Task(
        name=name,
        function=lambda inputs, params: None,
        dependencies=frozenset(deps),
    )


def build(*tasks):
    wf = Workflow()
    for t in tasks:
        wf.add_task(t)
    return wf


def test_empty_workflow():
    wf = Workflow()
    assert topological_order(wf) == []
    assert execution_layers(wf) == []


def test_single_task():
    wf = build(make_task("a"))
    assert topological_order(wf) == ["a"]
    assert execution_layers(wf) == [["a"]]


def test_chain():
    wf = build(make_task("c", "b"), make_task("b", "a"), make_task("a"))
    assert topological_order(wf) == ["a", "b", "c"]
    assert execution_layers(wf) == [["a"], ["b"], ["c"]]


def test_independent_tasks_sorted_in_one_layer():
    wf = build(make_task("z"), make_task("a"), make_task("m"))
    assert execution_layers(wf) == [["a", "m", "z"]]


def test_diamond_layers():
    wf = build(
        make_task("extract"),
        make_task("clean_a", "extract"),
        make_task("clean_b", "extract"),
        make_task("report", "clean_a", "clean_b"),
    )
    assert execution_layers(wf) == [
        ["extract"],
        ["clean_a", "clean_b"],
        ["report"],
    ]


def test_missing_dependency():
    wf = build(make_task("a", "ghost"))
    with pytest.raises(WorkflowValidationError, match="ghost"):
        wf.validate()


def test_cycle():
    wf = build(make_task("a", "b"), make_task("b", "a"))
    with pytest.raises(WorkflowValidationError, match="cykl"):
        topological_order(wf)


def test_determinism_independent_of_insertion_order():
    tasks = [
        make_task("a"),
        make_task("b", "a"),
        make_task("c", "a"),
        make_task("d", "b", "c"),
    ]
    assert topological_order(build(*tasks)) == topological_order(
        build(*reversed(tasks))
    )


def test_each_task_after_its_dependencies():
    wf = build(
        make_task("d", "b", "c"),
        make_task("b", "a"),
        make_task("c", "a"),
        make_task("a"),
    )
    pos = {n: i for i, n in enumerate(topological_order(wf))}
    for name, task in wf.tasks.items():
        assert all(pos[d] < pos[name] for d in task.dependencies)