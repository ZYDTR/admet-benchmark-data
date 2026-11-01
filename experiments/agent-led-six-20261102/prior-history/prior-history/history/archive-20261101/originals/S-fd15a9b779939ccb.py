"""Read only remote sessions; freeze once both original runs are terminal."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("api_helper", ROOT.parent / "admet_frozen_baseline_20261030/dispatch.py")
api_helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_helper)
api_helper.DIRECTORY = "<PRIVATE_RUNTIME_PATH>"


def main():
    if (ROOT / "originals/manifest.json").exists():
        print(json.dumps({"phase": "already_frozen"}))
        return
    statuses = api_helper.api("/session/status")
    rows, records = [], {}
    for role in ("model", "data-eval"):
        sid = json.loads((ROOT / f"dispatch-{role}.json").read_text())["session_id"]
        messages = api_helper.api(f"/session/{sid}/message")
        last = messages[-1]["info"]
        status = statuses.get(sid, {"type": "idle"})
        terminal = status["type"] == "idle" and last["role"] == "assistant" and bool(
            last.get("time", {}).get("completed") and
            (last.get("error") or last.get("finish") not in (None, "tool-calls", "unknown"))
        )
        rows.append({"role": role, "session_id": sid, "status": status,
                     "terminal": terminal, "last": {k: last.get(k) for k in ("id", "time", "finish", "error")}})
        records[role] = (sid, messages)
    report = {"observed_at": datetime.now(timezone.utc).isoformat(), "rows": rows}
    (ROOT / "last-poll.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    if not all(row["terminal"] for row in rows):
        print(json.dumps(report, ensure_ascii=False))
        return
    target = ROOT / "originals"
    target.mkdir(exist_ok=False)
    for role, (sid, messages) in records.items():
        folder = target / role
        folder.mkdir()
        for name, value in (("messages", messages), ("session", api_helper.api(f"/session/{sid}")),
                            ("children", api_helper.api(f"/session/{sid}/children"))):
            (folder / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    remote_root = "<PRIVATE_RUNTIME_PATH>"
    archive = target / "outputs.tar.gz"
    with archive.open("wb") as file:
        subprocess.run(["ssh", "-o", "BatchMode=yes", "<PREPARATION_HOST_ALIAS>",
                        f"<LOCAL_PRIVATE_PATH> exec mini-opencode tar -C {remote_root} -czf - model/output data-eval/output"],
                       stdout=file, stderr=subprocess.PIPE, check=True)
    with tarfile.open(archive) as tar:
        tar.extractall(target, filter="data")
    package = json.loads((ROOT / "package-receipt.json").read_text())
    expected = {role["role"]: role["manifest"] for role in package["roles"]}
    script = "import pathlib,json,hashlib\nroot=pathlib.Path(" + repr(remote_root) + ")\nexpected=" + repr(expected) + "\n"
    script += "bad=[]\nfor role,files in expected.items():\n for name,sha in files.items():\n  p=root/role/name\n  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:bad.append(str(p))\nprint(json.dumps({'checked':sum(map(len,expected.values())),'mismatches':bad}))\n"
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "<PREPARATION_HOST_ALIAS>",
                             "<LOCAL_PRIVATE_PATH> exec -i mini-opencode python3 -"],
                            input=script, text=True, capture_output=True, check=True)
    (target / "input-verification.json").write_text(result.stdout)
    manifest = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in target.rglob("*") if p.is_file()}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    for p in target.rglob("*"):
        if p.is_file():
            p.chmod(0o444)
    print(json.dumps({"phase": "frozen", "files": len(manifest), "input_check": json.loads(result.stdout)}))


if __name__ == "__main__":
    main()
