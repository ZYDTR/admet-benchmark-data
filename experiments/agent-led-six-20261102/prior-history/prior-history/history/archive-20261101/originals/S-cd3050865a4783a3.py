#!/usr/bin/env python3
"""Read-only checks; performs no training, remote access or installation."""
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parents[1]
sys.path.insert(0, str(PROJECT / 'src'))
from plan_checks import check

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: python3 -B scripts/check_plan.py PLAN.json')
    plan = json.loads(Path(sys.argv[1]).read_text())
    result = check(plan, WORKSPACE / 'adhoc_jobs/admet_frozen_baseline_20261030',
                   PROJECT / 'policy.json', WORKSPACE / 'rules/skills/hainan-compute-access/SKILL.md')
    print(json.dumps(result, ensure_ascii=False, indent=2))
