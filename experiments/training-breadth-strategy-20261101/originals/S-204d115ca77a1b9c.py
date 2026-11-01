#!/usr/bin/env python3
"""Convenience wrapper: run admet_eval commands from any directory.

Examples (from the project root):
  python3 output/data-eval/run_admet_eval.py selftest
  python3 output/data-eval/run_admet_eval.py verify-inputs --report output/data-eval/reports/inputs_report.json
  python3 output/data-eval/run_admet_eval.py score --pred runs/preds.csv --labels <dir-or-csv>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admet_eval.__main__ import main

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
