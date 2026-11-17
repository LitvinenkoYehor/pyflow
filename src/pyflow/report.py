from __future__ import annotations

from pyflow.results import RunResult


def format_report(result: RunResult) -> str:
    """Tekstowy raport przebiegu. Tylko czyta RunResult, niczego nie zmienia."""
    width = max((len(n) for n in result.order), default=4)
    width = max(width, 7)
    lines = [
        "Raport wykonania PyFlow",
        f"{'Zadanie':<{width}}  {'Status':<10}  Czas [ms]",
        "-" * (width + 24),
    ]
    for name in result.order:
        state = result.task_states[name]
        duration = state.duration
        time_text = "-" if duration is None else f"{duration * 1000:.3f}"
        lines.append(f"{name:<{width}}  {state.status.value:<10}  {time_text}")
        if state.error is not None:
            lines.append(f"    błąd: {state.error}")
        if state.skipped_because:
            lines.append(f"    pominięte przez: {', '.join(state.skipped_because)}")
    lines.append("-" * (width + 24))
    verdict = "SUKCES" if result.succeeded else "PORAŻKA"
    lines.append(f"Razem: {result.total_duration * 1000:.3f} ms ({verdict})")
    return "\n".join(lines)