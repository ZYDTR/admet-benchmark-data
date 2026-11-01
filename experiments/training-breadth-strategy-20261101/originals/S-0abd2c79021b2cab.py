"""Re-run every preparation check that CAN run here and write ``checks.json``.

    python3 run_checks.py [--out checks.json]

Each check records: name, command, exit code, PASS/FAIL/SKIP, and the reason for a
skip.  Nothing is marked PASS unless the command actually ran and exited 0 in this
environment.  Checks that need torch/rdkit/chemprop/numpy or the 34.9 MB
checkpoint are recorded as SKIP with the exact blocking error, never as PASS.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.dirname(HERE)
DATA = os.path.join(MODEL_DIR, "input", "data")
TEMPLATE = os.path.join(DATA, "official", "submission_template.csv")
TEMPLATE_SHA256 = "8ee41589d2c98e7b93081c058b3f928ac09bea4b3ffc899fa13677051e9baa20"
TEMPLATE_ROWS = 16379


def _run(name, cmd, note=None):
    proc = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    return {
        "check": name,
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "note": note,
        "output_tail": tail[-3:],
    }


def _skip(name, command, reason):
    return {"check": name, "command": command, "exit_code": None,
            "status": "SKIP", "note": reason}


def _digest_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _import_probe():
    out = {}
    for name in ("numpy", "torch", "rdkit", "chemprop", "pandas", "sklearn", "pytest"):
        code = (f"import importlib,json\ntry:\n import {name}\n"
                f" print(json.dumps({{'{name}': getattr(__import__('{name}'), '__version__', 'unknown')}}))\n"
                "except Exception as e:\n"
                f" print(json.dumps({{'{name}': None, 'error': repr(e)}}))")
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        try:
            out.update(json.loads(proc.stdout.strip().splitlines()[-1]))
        except Exception:
            out[name] = {"error": proc.stdout + proc.stderr}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=os.path.join(HERE, "checks.json"))
    args = ap.parse_args(argv)

    checks = []
    checks.append(_run("unit_tests_stdlib_synthetic",
                       [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                       "data contract, products, metrics, cache, submission on synthetic packs"))
    checks.append(_run("compileall", [sys.executable, "-m", "compileall", "-q", "."]))
    for script in ("encode_features.py", "train_heads.py", "predict_valid.py",
                   "predict_test.py", "score.py", "make_asset_lock.py"):
        checks.append(_run(f"cli_help_{script}", [sys.executable, script, "--help"]))
    checks.append(_run("read_only_real_pack_listing",
                       [sys.executable, "-c",
                        "import dataio;t=dataio.list_tasks(%r);"
                        "print(len(t),t[:3])" % DATA],
                       "22 tasks enumerated from input/data"))

    tpl_sha = _digest_file(TEMPLATE)
    import csv
    with open(TEMPLATE, encoding="utf-8-sig", newline="") as fh:
        n_tpl = sum(1 for _ in csv.DictReader(fh))
    checks.append({
        "check": "template_pin", "command": "sha256+rowcount of submission_template.csv",
        "exit_code": 0,
        "status": "PASS" if (tpl_sha == TEMPLATE_SHA256 and n_tpl == TEMPLATE_ROWS) else "FAIL",
        "note": f"sha256={tpl_sha} rows={n_tpl}",
    })

    deps = _import_probe()
    blockers = {k: v for k, v in deps.items()
                if not isinstance(v, str) or v is None or isinstance(v, dict)}
    for name, cmd, reason in (
        ("encoder_weight_loading", "python3 -c 'import chemeleon_encoder'",
         "needs torch+chemprop+rdkit and chemeleon_mp.pt"),
        ("feature_extraction_real_batch", "python3 encode_features.py --data-root ...",
         "whole-batch encoding is training-stage work; not run here"),
        ("head_training_real", "python3 train_heads.py ...",
         "training is main-control work; no torch in this session"),
        ("head_save_load_real", "tests/test_head_and_submission_synthetic.py",
         "3 head artifact tests skipped: torch not installed"),
        ("real_valid_test_prediction", "python3 predict_valid.py / predict_test.py ...",
         "no checkpoint, no heads, no features"),
    ):
        checks.append(_skip(name, cmd, reason))

    payload = {
        "session": "admet_deepseek_skill_coldstart_20261030 (preparation-only leaf)",
        "python": sys.version.split()[0],
        "cwd": HERE,
        "dependency_probe": deps,
        "blocked_by_missing_deps": sorted(blockers),
        "checks": checks,
        "summary": {
            "pass": sum(1 for c in checks if c["status"] == "PASS"),
            "fail": sum(1 for c in checks if c["status"] == "FAIL"),
            "skip": sum(1 for c in checks if c["status"] == "SKIP"),
        },
        "unverified_items": [
            "FrozenCheMeleonEncoder against real weights (feature_dim unconfirmed)",
            "head save/load + scaler round trip through torch (3 unittest skips)",
            "end-to-end encode -> train -> predict coverage on the 22 real tasks",
            "RDKit parse-failure policy on real SMILES (failures.json path)",
        ],
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0 if payload["summary"]["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())