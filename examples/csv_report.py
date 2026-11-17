"""Przyklad end-to-end: CSV -> czyszczenie -> agregacja -> raport JSON."""
from __future__ import annotations

import csv
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pyflow import Task, Workflow, format_report, run

HERE = Path(__file__).parent


def read_csv(inputs: Mapping[str, Any], params: Mapping[str, Any]) -> list[dict[str, str]]:
    with open(params["path"], newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean(inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
    valid: list[dict[str, Any]] = []
    rejected = 0
    for row in inputs["read_csv"]:
        try:
            quantity = int(row["quantity"])
            price = float(row["price"])
        except ValueError:
            rejected += 1
            continue
        if not row["region"].strip() or quantity <= 0 or price < 0:
            rejected += 1
            continue
        valid.append({"region": row["region"].strip(), "quantity": quantity, "price": price})
    return {"valid": valid, "rejected": rejected}


def aggregate(inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in inputs["clean"]["valid"]:
        totals[row["region"]] = totals.get(row["region"], 0.0) + row["quantity"] * row["price"]
    return {region: round(total, 2) for region, total in sorted(totals.items())}


def write_report(inputs: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
    report = {
        "revenue_by_region": inputs["aggregate"],
        "total_revenue": round(sum(inputs["aggregate"].values()), 2),
        "valid_rows": len(inputs["clean"]["valid"]),
        "rejected_rows": inputs["clean"]["rejected"],
    }
    Path(params["output"]).write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return report


def build_workflow(csv_path: Path, output_path: Path) -> Workflow:
    wf = Workflow()
    wf.add_task(Task("read_csv", read_csv, params={"path": str(csv_path)}))
    wf.add_task(Task("clean", clean, frozenset({"read_csv"})))
    wf.add_task(Task("aggregate", aggregate, frozenset({"clean"})))
    wf.add_task(
        Task("write_report", write_report, frozenset({"clean", "aggregate"}),
             params={"output": str(output_path)})
    )
    return wf


def main() -> None:
    wf = build_workflow(HERE / "data" / "sales.csv", HERE / "report.json")
    result = run(wf)
    print(format_report(result))


if __name__ == "__main__":
    main()