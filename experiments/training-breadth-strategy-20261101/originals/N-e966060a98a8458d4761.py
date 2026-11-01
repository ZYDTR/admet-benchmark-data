"""Generate the six batch configs from input/base_config.json + input/batch_request.json.

Preparation-only: writes output/configs/<run_id>.json and output/batch-manifest.json.
Imports the frozen production module (training_science.validate_config) to pre-validate each
in-memory object; acceptance additionally re-validates the WRITTEN JSON bytes from disk in a
separate process (see tests/test_batch_configs.py). No training, no parameter updates.
"""
from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]      # output/
TASK = OUT.parent                               # preparation/
sys.path.insert(0, str(OUT))
import training_science as science              # noqa: E402  (frozen production module, byte-copy of input/reference)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    base = json.loads((TASK / "input/base_config.json").read_text(encoding="utf-8"))
    request = json.loads((TASK / "input/batch_request.json").read_text(encoding="utf-8"))
    runs = request["runs"]
    assert len(runs) == 6, f"expected exactly six runs, got {len(runs)}"
    assert request["scientific_asset_id"] == "chemeleon"
    assert request["task"] == base["task"]

    seen_run_ids = set()
    entries = []
    for req_run in runs:
        cfg = copy.deepcopy(base)
        cfg["run_id"] = req_run["run_id"]
        cfg["monitor"] = req_run["monitor"]
        cfg["head_config"]["seed"] = req_run["model_seed"]
        if cfg["run_id"] in seen_run_ids:
            raise SystemExit(f"duplicate run_id in request: {cfg['run_id']}")
        seen_run_ids.add(cfg["run_id"])
        science.validate_config(cfg)  # pre-write sanity via production entry
        path = OUT / "configs" / f"{cfg['run_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
            f.write("\n")
        # only run_id / monitor / head_config.seed may differ from base.
        # (monitor may coincidentally equal the base value; equality is checked against the
        #  batch_request declaration below, not against base.)
        assert cfg["run_id"] != base["run_id"], cfg["run_id"]
        assert cfg["monitor"] == req_run["monitor"], (cfg["run_id"], cfg["monitor"])
        assert cfg["head_config"]["seed"] == req_run["model_seed"], cfg["run_id"]
        top_keys_changed = {k for k in set(cfg) | set(base) if cfg.get(k) != base.get(k)}
        assert top_keys_changed <= {"run_id", "monitor", "head_config"}, (cfg["run_id"], top_keys_changed)
        nested_diff = [k for k in ("hidden_dims", "dropout", "lr", "weight_decay", "batch_size",
                                   "epochs", "patience", "val_fraction_from_train", "optimizer", "seed")
                       if cfg["head_config"][k] != base["head_config"][k]]
        assert nested_diff == [] or (nested_diff == ["seed"] and base["head_config"]["seed"] != req_run["model_seed"]), \
            (cfg["run_id"], nested_diff)
        assert cfg["split_config"] == base["split_config"], cfg["run_id"]
        assert cfg["inputs"] == base["inputs"], cfg["run_id"]
        entries.append({
            "run_id": cfg["run_id"],
            "config_path": f"configs/{cfg['run_id']}.json",
            "config_sha256": sha(path),
            "monitor": cfg["monitor"],
            "head_seed": cfg["head_config"]["seed"],
            "split_seed": cfg["split_config"]["seed"],
            "declared_model_seed": req_run["model_seed"],
            "declared_split_seed": req_run["split_seed"],
        })

    manifest = {
        "cycle_id": request["cycle_id"],
        "request_id": "admet-contract-follow-preparation-20261101-001",
        "task": request["task"],
        "scientific_asset_id": request["scientific_asset_id"],
        "base_config": {"path": "input/base_config.json",
                        "sha256": sha(TASK / "input/base_config.json"),
                        "role": "template; old run_id must not appear in new configs"},
        "batch_request": {"path": "input/batch_request.json",
                          "sha256": sha(TASK / "input/batch_request.json")},
        "source_files": [
            {"path": name,
             "origin": f"input/reference/{name}",
             "output_copy_sha256": sha(OUT / name),
             "reference_sha256": sha(TASK / "input/reference" / name)}
            for name in ("training_science.py", "train_remote_v4.py", "encoder.py")
        ],
        "inputs_deployed_by_host": [
            {"role": i["role"], "path": i["path"], "sha256": i["sha256"], "rows": i["rows"]}
            for i in base["inputs"]
        ],
        "runs": entries,
        "notes": "six independent serial runs; host deploys data/ paths; split seed fixed 43",
    }
    mpath = OUT / "batch-manifest.json"
    with mpath.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print(json.dumps({"written": len(entries), "manifest": str(mpath)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
