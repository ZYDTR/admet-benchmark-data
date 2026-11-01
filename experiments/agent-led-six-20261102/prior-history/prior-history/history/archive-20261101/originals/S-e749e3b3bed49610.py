#!/usr/bin/env python3
"""Opt-in integration probe for an already reviewed local Python image."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

PROBE = r'''
import errno,json,os,pathlib,socket
checks={"non_root":os.getuid()!=0,"root_read_only":bool(os.statvfs('/').f_flag & os.ST_RDONLY)}
checks["network_interfaces"]=sorted(p.name for p in pathlib.Path('/sys/class/net').iterdir())
checks["only_loopback"]=checks["network_interfaces"]==["lo"]
checks["input_readable"]=pathlib.Path('/probe/input.txt').read_text()=="synthetic boundary fixture\n"
try:
    pathlib.Path('/probe/input.txt').write_text('must not write')
    checks["input_read_only"]=False
except OSError as exc:
    checks["input_read_only"]=exc.errno==errno.EROFS
checks["cache_starts_empty"]=not pathlib.Path('/tmp/cache').exists()
pathlib.Path('/tmp/cache').mkdir()
pathlib.Path('/tmp/cache/write-check').write_text('ok')
checks["scratch_writable"]=True
try:
    with socket.create_connection(('198.51.100.1',80),timeout=1):
        checks["external_connection_blocked"]=False
except OSError as exc:
    checks["external_connection_blocked"]=True
    checks["network_error"]=type(exc).__name__
required=['non_root','root_read_only','only_loopback','input_readable','input_read_only','cache_starts_empty','scratch_writable','external_connection_blocked']
checks['ok']=all(checks[k] for k in required)
print(json.dumps(checks))
raise SystemExit(0 if checks['ok'] else 1)
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="reviewed local sha256:<64 hex> image ID containing python3")
    args = parser.parse_args()
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", args.image):
        print(json.dumps({"ok": False, "error": "IMAGE_NOT_PINNED"}))
        return 2
    if shutil.which("docker") is None:
        print(json.dumps({"ok": False, "error": "DOCKER_UNAVAILABLE", "isolation_runtime_tested": False}))
        return 2
    name = "admet-boundary-" + uuid.uuid4().hex[:12]
    try:
        with tempfile.TemporaryDirectory(prefix="admet-boundary-") as temporary:
            directory = Path(temporary)
            directory.chmod(0o755)
            fixture = directory / "input.txt"
            fixture.write_text("synthetic boundary fixture\n")
            fixture.chmod(0o666)  # Writable DAC permissions ensure failure tests the RO mount.
            if "," in str(directory) or "\n" in str(directory):
                raise ValueError("Docker bind path cannot contain comma/newline")
            command = ["docker", "run", "--rm", "--name", name, "--pull", "never", "--network", "none", "--read-only",
                       "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--user", "65532:65532",
                       "--memory", "256m", "--cpus", "1", "--pids-limit", "32",
                       "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m,mode=1777",
                       "--mount", f"type=bind,src={directory},dst=/probe,readonly",
                       "--entrypoint", "python3", args.image, "-c", PROBE]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
            if result.returncode:
                print(json.dumps({"ok": False, "error": "BOUNDARY_PROBE_FAILED", "exit_code": result.returncode,
                                  "stdout": result.stdout[-8000:], "stderr": result.stderr[-8000:], "isolation_runtime_tested": False}))
                return 2
            checks = json.loads(result.stdout)
            print(json.dumps({"ok": checks.get("ok") is True, "image": args.image, "checks": checks,
                              "isolation_runtime_tested": checks.get("ok") is True,
                              "scope": "This probe only; not host-Agent permissions, image provenance or competition training."}, indent=2))
            return 0 if checks.get("ok") is True else 2
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc), "isolation_runtime_tested": False}))
        return 2
    finally:
        # A timeout can kill the client while leaving the container alive.
        try:
            subprocess.run(["docker", "rm", "--force", name], capture_output=True, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            pass


if __name__ == "__main__":
    raise SystemExit(main())
