import json

from csv_report import HERE, build_workflow
from pyflow import run


def test_csv_to_json_end_to_end(tmp_path):
    out = tmp_path / "report.json"
    result = run(build_workflow(HERE / "data" / "sales.csv", out))

    assert result.succeeded
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == {
        "rejected_rows": 3,
        "revenue_by_region": {"East": 600.0, "North": 6500.0, "South": 5401.5, "West": 480.0},
        "total_revenue": 12981.5,
        "valid_rows": 6,
    }


def test_missing_csv_gives_failed_pipeline(tmp_path):
    result = run(build_workflow(tmp_path / "nope.csv", tmp_path / "out.json"))
    assert not result.succeeded
    assert result.task_states["read_csv"].status.value == "FAILED"
    assert result.task_states["write_report"].status.value == "SKIPPED"