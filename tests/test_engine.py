import pytest

from pyflow import (
    Task,
    TaskExecutionError,
    TaskStatus,
    Workflow,
    WorkflowValidationError,
    format_report,
    run,
)


def build(*tasks):
    wf = Workflow()
    for t in tasks:
        wf.add_task(t)
    return wf


def ok(value):
    return lambda inputs, params: value


def boom(inputs, params):
    raise ValueError("kaboom")


def test_empty_workflow():
    result = run(Workflow())
    assert result.outputs == {}
    assert result.task_states == {}
    assert result.succeeded is True


def test_results_flow_only_from_direct_dependencies():
    seen = {}

    def spy(inputs, params):
        seen.update(inputs)
        return "c-done"

    wf = build(
        Task("a", ok(1)),
        Task("b", lambda i, p: i["a"] + 1, frozenset({"a"})),
        Task("c", spy, frozenset({"b"})),
    )
    result = run(wf)
    assert result.outputs == {"a": 1, "b": 2, "c": "c-done"}
    assert seen == {"b": 2}  # tylko bezpośrednia zależność, bez "a"


def test_execution_order_respects_dependencies():
    calls = []

    def rec(name):
        def f(inputs, params):
            calls.append(name)
        return f

    wf = build(
        Task("report", rec("report"), frozenset({"clean_a", "clean_b"})),
        Task("clean_b", rec("clean_b"), frozenset({"extract"})),
        Task("clean_a", rec("clean_a"), frozenset({"extract"})),
        Task("extract", rec("extract")),
    )
    run(wf)
    assert calls == ["extract", "clean_a", "clean_b", "report"]


def test_params_are_passed():
    wf = build(Task("a", lambda i, p: p["x"] * 2, params={"x": 21}))
    assert run(wf).outputs["a"] == 42


def test_failure_marks_failed_and_skips_dependents_transitively():
    wf = build(
        Task("a", boom),
        Task("b", ok(1), frozenset({"a"})),
        Task("c", ok(1), frozenset({"b"})),
    )
    result = run(wf)
    states = {n: s.status for n, s in result.task_states.items()}
    assert states == {
        "a": TaskStatus.FAILED,
        "b": TaskStatus.SKIPPED,
        "c": TaskStatus.SKIPPED,
    }
    assert result.succeeded is False
    assert result.outputs == {}
    assert result.task_states["b"].skipped_because == ("a",)


def test_independent_task_is_still_executed_policy():
    wf = build(Task("bad", boom), Task("good", ok("fine")))
    result = run(wf)
    assert result.task_states["good"].status is TaskStatus.SUCCEEDED
    assert result.outputs == {"good": "fine"}


def test_error_contains_task_name_and_original_cause():
    result = run(build(Task("bad", boom)))
    error = result.task_states["bad"].error
    assert isinstance(error, TaskExecutionError)
    assert error.task_name == "bad"
    assert isinstance(error.__cause__, ValueError)
    assert "bad" in str(error)


def test_raise_on_failure_raises_task_execution_error():
    with pytest.raises(TaskExecutionError) as info:
        run(build(Task("bad", boom)), raise_on_failure=True)
    assert info.value.task_name == "bad"
    assert isinstance(info.value.__cause__, ValueError)


def test_invalid_workflow_is_rejected_before_running():
    called = []
    wf = build(Task("a", lambda i, p: called.append(1), frozenset({"ghost"})))
    with pytest.raises(WorkflowValidationError):
        run(wf)
    assert called == []


def test_timings_recorded():
    result = run(build(Task("a", ok(1))))
    state = result.task_states["a"]
    assert state.duration is not None and state.duration >= 0
    assert result.total_duration >= state.duration


def test_text_report_lists_every_step_and_total():
    wf = build(Task("a", ok(1)), Task("b", boom), Task("c", ok(1), frozenset({"b"})))
    text = format_report(run(wf))
    for needle in ("a", "SUCCEEDED", "FAILED", "SKIPPED", "Razem"):
        assert needle in text