"""Stable JSON CLI for agents and humans; never an arbitrary command proxy."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .common import HarnessError, resolve_inside, write_json


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="ADMET competition 159 engineering harness (Python 3.11+, no core dependencies)")
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2], help="project root; all file arguments are project-relative")
    sub = p.add_subparsers(dest="command", required=True)
    for name, help_text in [("status", "recover saved state and tasks"), ("doctor", "inspect available runtime and admission prerequisites"), ("check-context", "validate context links, discovery and size budgets")]:
        sub.add_parser(name, help=help_text)
    s = sub.add_parser("context", help="load one intent-selected skill, without recursive loading")
    s.add_argument("--skill", required=True)
    s = sub.add_parser("checkpoint", help="save a versioned task handoff with evidence hashes")
    s.add_argument("--input", required=True)
    s.add_argument("--expected-revision", required=True, type=int)
    s = sub.add_parser("check-data", help="check an approved official input manifest")
    s.add_argument("--manifest", default="config/data_manifest.json")
    s = sub.add_parser("adapter-digest", help="hash reviewed code-only model adapter")
    s.add_argument("--path", required=True)
    for name in ("plan", "run"):
        s = sub.add_parser(name, help="validate a formal run" if name == "plan" else "execute a formal run in the fixed Docker boundary")
        s.add_argument("--config", required=True)
    s = sub.add_parser("bundle", help="package one completed run's reviewed evidence without raw inputs")
    s.add_argument("--run-dir", required=True)
    s.add_argument("--output", required=True)
    s = sub.add_parser("inspect-template", help="inspect the original public template as strings")
    s.add_argument("--template", required=True)
    s = sub.add_parser("validate-submission", help="check CSV structure, metadata and finite predictions")
    s.add_argument("--template", required=True)
    s.add_argument("--submission", required=True)
    s.add_argument("--prediction-kind", choices=["score", "probability"], default="score")
    s.add_argument("--report", help="optional new JSON report path")
    s = sub.add_parser("export-submission", help="export a candidate and declared provenance; no upload")
    s.add_argument("--template", required=True)
    s.add_argument("--predictions", required=True)
    s.add_argument("--output", required=True)
    s.add_argument("--prediction-kind", choices=["score", "probability"], default="score")
    s = sub.add_parser("verify-candidate", help="cross-check candidate, prediction run and training checkpoint")
    s.add_argument("--submission", required=True)
    s = sub.add_parser("evaluate", help="compute explicitly defined local per-task metrics; no official total")
    s.add_argument("--records", required=True)
    s.add_argument("--task-schema", default="competition/task_schema.json")
    s.add_argument("--report", help="optional new JSON report path")
    return p


def dispatch(args: argparse.Namespace) -> dict:
    from . import context, runtime, submission
    root = args.root.resolve()
    path = lambda value, exists=True: resolve_inside(root, value, must_exist=exists)
    command = args.command
    if command == "status":
        return context.status(root)
    if command == "doctor":
        return context.doctor(root)
    if command == "check-context":
        return context.check_context(root)
    if command == "context":
        return context.get_context(root, args.skill)
    if command == "checkpoint":
        return context.save_handoff(root, path(args.input), args.expected_revision)
    if command == "check-data":
        return runtime.check_data(root, path(args.manifest))
    if command == "adapter-digest":
        return {"ok": True, **runtime.adapter_digest(root, path(args.path))}
    if command == "plan":
        return runtime.plan_run(root, path(args.config))
    if command == "run":
        return runtime.execute_run(root, path(args.config))
    if command == "bundle":
        return runtime.bundle_run(root, path(args.run_dir), path(args.output, False))
    if command == "inspect-template":
        return submission.inspect_template(path(args.template))
    if command == "validate-submission":
        return submission.validate_submission(path(args.template), path(args.submission), args.prediction_kind)
    if command == "export-submission":
        return submission.export_submission(path(args.template), path(args.predictions), path(args.output, False), args.prediction_kind)
    if command == "verify-candidate":
        from .candidate import verify_candidate
        return verify_candidate(root, path(args.submission))
    if command == "evaluate":
        from .evaluation import evaluate_records
        return evaluate_records(path(args.task_schema), path(args.records))
    raise HarnessError("UNKNOWN_COMMAND", "Unsupported command")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report = None
        if getattr(args, "report", None):
            report = resolve_inside(args.root.resolve(), args.report, must_exist=False)
            if report.exists():
                raise HarnessError("OUTPUT_EXISTS", "Choose a new report path")
        result = dispatch(args)
        if report:
            # Report paths are new evidence, never an excuse to overwrite inputs.
            report.parent.mkdir(parents=True, exist_ok=True)
            with report.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except HarnessError as exc:
        print(json.dumps({"ok": False, "error": exc.as_dict()}, ensure_ascii=False, indent=2, allow_nan=False))
        return 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": {"code": "IO_OR_SCHEMA_ERROR", "message": str(exc), "details": {"exception_type": type(exc).__name__}}}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
