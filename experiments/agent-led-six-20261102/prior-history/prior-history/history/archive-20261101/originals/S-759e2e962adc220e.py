#!/usr/bin/env python3
"""Run from a checkout without installing any packages."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from admet_harness.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
