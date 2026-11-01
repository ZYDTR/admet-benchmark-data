#!/usr/bin/env python3
"""A quarantined synthetic format/evaluation demonstration, never competition training."""
import csv
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from admet_harness.common import write_json
from admet_harness.evaluation import evaluate_records
from admet_harness.submission import export_submission, inspect_template, validate_submission


def main() -> int:
    (ROOT / "local").mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="synthetic-demo-", dir=ROOT / "local"))
    template = directory / "synthetic-template.csv"
    with template.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\r\n")
        writer.writerow(["task", "sample_idx", "drug_id", "smiles", "y_pred", "metric"])
        writer.writerows([
            ["demo-class", "0", "001", "C", "", "AUROC"],
            ["demo-class", "1", "001", "CC", "", "AUROC"],
            ["demo-reg", "0", "", "O", "", "MAE"]])
    write_json(directory / "records.json", {"schema_version": 1, "run_id": "synthetic-demo-not-a-model",
        "model_artifact_sha256": "0" * 64, "predictions": [
            {"task": "demo-reg", "sample_idx": "0", "y_pred": -2.0},
            {"task": "demo-class", "sample_idx": "1", "y_pred": 1.5},
            {"task": "demo-class", "sample_idx": "0", "y_pred": -0.5}]})
    write_json(directory / "schema.json", {"schema_version": 1, "label_contract_status": "synthetic",
        "tasks": [{"task": "demo-class", "kind": "classification", "metric": "AUROC"},
                  {"task": "demo-reg", "kind": "regression", "metric": "MAE"}]})
    write_json(directory / "validation-records.json", {"schema_version": 1, "split_id": "synthetic-only", "records": [
        {"task": "demo-class", "sample_id": "0", "y_true": 0, "y_pred": -0.5},
        {"task": "demo-class", "sample_id": "1", "y_true": 1, "y_pred": 1.5},
        {"task": "demo-reg", "sample_id": "0", "y_true": -1.0, "y_pred": -2.0}]})
    exported = export_submission(template, directory / "records.json", directory / "synthetic-output.csv")
    report = {"ok": True, "scope": "synthetic_engineering_demo", "not_for_competition_submission": True,
              "formal_training_executed": False, "container_isolation_tested": False,
              "template": inspect_template(template), "export": exported,
              "validation": validate_submission(template, directory / "synthetic-output.csv"),
              "evaluation": evaluate_records(directory / "schema.json", directory / "validation-records.json")}
    write_json(directory / "report.json", report)
    print(json.dumps({"ok": True, "scope": report["scope"], "not_for_competition_submission": True,
                      "report": (directory / "report.json").relative_to(ROOT).as_posix(), "rows": 3,
                      "checked": ["string preservation", "duplicate drug IDs", "blank original ID", "key reordering", "unbounded classification scores", "local metrics"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
