#!/usr/bin/env python3
"""Emit {splits:{split:{task:n_rows}}} from the actual split CSVs.

This is the authoritative row-count source for the score.py completeness
check.  It reads (never modifies) the split files and records their hashes so
the scoring run is bound to the exact inputs used.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from admet_eval import common as C  # noqa: E402


def build(official_base, blind_base, template_path, schema_path, out):
    schema = C.load_and_check_schema(schema_path, template_path)
    tasks = [t["task"] for t in schema["tasks"]]
    doc = {"schema_version": 1,
           "template_sha256": C.sha256_file(template_path),
           "splits": {}, "files": {}}
    for split in C.SPLITS:
        per = {}
        files = {}
        for task in tasks:
            s = C.read_split(split, task, official_base, blind_base)
            per[task] = s["n_rows"]
            files[task] = {"path": s["path"], "sha256": s["sha256"], "n_rows": s["n_rows"]}
        doc["splits"][split] = per
        doc["files"][split] = files
    text = json.dumps(doc, ensure_ascii=False, indent=2)
    if out:
        d = os.path.dirname(os.path.abspath(out))
        os.makedirs(d, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    else:
        sys.stdout.write(text + "\n")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--official-base", default=C.DEFAULT_OFFICIAL_BASE)
    p.add_argument("--blind-base", default=C.DEFAULT_BLIND_BASE)
    p.add_argument("--template", default=os.path.join(C.DEFAULT_OFFICIAL_BASE, "submission_template.csv"))
    p.add_argument("--schema", required=True)
    p.add_argument("--out", default=None)
    a = p.parse_args(argv)
    try:
        return build(a.official_base, a.blind_base, a.template, a.schema, a.out)
    except C.ContractError as e:
        sys.stderr.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())