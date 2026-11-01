"""本机审计：只读冻结源、零训练；结果只写本审计目录。"""
import ast
import datetime
import hashlib
import json
import math
import random
import subprocess
import sys
from pathlib import Path

A = Path(__file__).resolve().parent
R = A.parents[1]
C = R / "cycles/monitor-mae-e2e-20261101"
original = C / "monitor/acceptance/frozen/output"
fixed = C / "preparation/host-science-v1"
result = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "training_updates": 0, "remote_operations": 0}

# 调用此前已审读的真实生产函数提取检查器，不导入模型/依赖、不写 checkpoint。
checker = C / "control/preparation-repair-20261101/check_checkpoint_semantics.py"
result["checkpoint"] = {}
for name, source, expected in [("original", original, 1), ("main_fixed", fixed, 0)]:
    p = subprocess.run([sys.executable, "-B", str(checker), str(source)],
                       capture_output=True, text=True, timeout=20)
    (A / (name + "-metadata.stdout")).write_text(p.stdout)
    (A / (name + "-metadata.stderr")).write_text(p.stderr)
    assert p.returncode == expected, (name, p.returncode)
    result["checkpoint"][name] = {"returncode": p.returncode,
        "expected_returncode": expected, "production_cases": json.loads(p.stdout)}

# 只提取标准库行合同/分组函数；不加载 numpy/torch 或训练入口。
tree = ast.parse((original / "training_science.py").read_text())
names = {"PreparationError", "check_rows_identity", "split_train_stop_groups",
         "canonical_json_bytes", "sha256_hex"}
nodes = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
nodes += [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
env = {"hashlib": hashlib, "json": json, "random": random, "math": math}
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
             "<original production row functions>", "exec"), env)
cases = {}
for label, rows in {
    "same_attributes_different_positions_two_groups": [
        {"Drug_ID": "dup", "Drug": "CC", "Y": "1"},
        {"Drug_ID": "dup", "Drug": "CC", "Y": "1"},
        {"Drug_ID": "other", "Drug": "CCC", "Y": "2"}],
    "unique_ids_single_group": [
        {"Drug_ID": "first", "Drug": "CC", "Y": "1"},
        {"Drug_ID": "second", "Drug": "CC", "Y": "2"}]
}.items():
    env["check_rows_identity"](rows, require_y=True, label="train")
    try:
        split = env["split_train_stop_groups"](rows, 43, .1)
        cases[label] = {"state": "accepted", "rows": len(rows), "split": split}
    except env["PreparationError"] as e:
        cases[label] = {"state": "rejected", "error": str(e)}
assert cases["same_attributes_different_positions_two_groups"]["state"] == "accepted"
assert cases["unique_ids_single_group"]["state"] == "rejected"
result["row_test_counterexample"] = cases
result["row_test_conclusion"] = "原测试证明单组不可划分，不证明重复(task,split,row_index)被拒；相同属性不同原始行必须保留。"

# 原始出包清单和当前字节相符；不修改冻结原件。
manifest = json.loads((original / "output-manifest.json").read_text())
checks = []
for item in manifest["files"]:
    p = original / item["path"]
    checks.append({"path": item["path"], "match":
                   hashlib.sha256(p.read_bytes()).hexdigest() == item["sha256"]})
assert all(x["match"] for x in checks)
result["frozen_output_manifest"] = checks
result["limits"] = ["metadata检查为生产函数加无写入serializer，不证明Tensor实际存取",
                    "当前只复核已冻结本机证据，无新训练/评分/网站或海南访问"]
(A / "recheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"checkpoint_original_rejected": True, "fixed_four_cases_pass": True,
                  "row_counterexample_confirmed": True, "output_hashes": len(checks),
                  "training_updates": 0}, ensure_ascii=False))
