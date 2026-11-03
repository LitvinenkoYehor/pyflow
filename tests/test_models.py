import pytest

from pyflow import Task, Workflow, WorkflowValidationError


def noop(inputs, params):
    return None


def test_empty_name_rejected():
    with pytest.raises(WorkflowValidationError):
        Task(name="", function=noop)


def test_self_dependency_rejected():
    with pytest.raises(WorkflowValidationError):
        Task(name="a", function=noop, dependencies=frozenset({"a"}))


def test_duplicate_task_rejected():
    wf = Workflow()
    wf.add_task(Task(name="a", function=noop))
    with pytest.raises(WorkflowValidationError):
        wf.add_task(Task(name="a", function=noop))


def test_params_are_copied():
    params = {"x": 1}
    task = Task(name="a", function=noop, params=params)
    params["x"] = 999
    assert task.params["x"] == 1


def test_dependencies_are_copied():
    deps = {"b"}
    task = Task(name="a", function=noop, dependencies=deps)
    deps.add("c")
    assert task.dependencies == frozenset({"b"})