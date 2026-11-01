"""CLI entry point: python3 -m admet_eval <command> [options]."""
from __future__ import annotations

import argparse
import sys

from . import check_predictions
from . import export_submission
from . import score
from . import selftest
from . import validate_submission
from . import verify_inputs
from .common import SPLITS


def build_parser():
    parser = argparse.ArgumentParser(
        prog='admet_eval',
        description='Data verification, per-task scoring and submission export for the frozen ADMET baseline (task B). '
                    'Pure Python standard library. Run from the project root or pass --data-root.',
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('verify-inputs', help='verify registered inputs and the official template (read-only)')
    p.add_argument('--data-root', default=None, help='project root containing data/ (default: auto-detect)')
    p.add_argument('--template', default=None, help='template CSV path (default: <data-root>/data/official/submission_template.csv)')
    p.add_argument('--schema', default=None, help='reference task_schema.json for cross-check (default: auto-detect; "none" disables)')
    p.add_argument('--report', default=None, help='write a JSON report to this path')
    p.add_argument('--verbose', action='store_true', help='also print passing checks')

    p = sub.add_parser('check-predictions', help='contract and coverage checks for a prediction file')
    p.add_argument('--pred', required=True, help='prediction CSV with columns task,split,row_index,y_pred')
    p.add_argument('--data-root', default=None)
    p.add_argument('--report', default=None)

    p = sub.add_parser('score', help='per-task scoring of one split against explicitly provided labels')
    p.add_argument('--pred', required=True)
    p.add_argument('--split', default='valid', choices=list(SPLITS))
    p.add_argument('--labels', required=True,
                   help='labels directory (per-task official-format CSVs) or single long-format CSV (task,row_index,y_true)')
    p.add_argument('--data-root', default=None)
    p.add_argument('--template', default=None)
    p.add_argument('--report', default=None)
    p.add_argument('--report-csv', default=None)

    p = sub.add_parser('export', help='fill y_pred into the official template (byte-preserving)')
    p.add_argument('--pred', required=True)
    p.add_argument('--template', default=None)
    p.add_argument('--output', required=True)
    p.add_argument('--data-root', default=None)
    p.add_argument('--report', default=None)
    p.add_argument('--check-range', action='store_true',
                   help='additionally require classification y_pred within [0,1]')
    p.add_argument('--allow-unregistered-template', action='store_true',
                   help='permit a template whose sha256 is not the registered official one')
    p.add_argument('--overwrite', action='store_true', help='replace an existing output file')

    p = sub.add_parser('validate-submission', help='verify a candidate CSV preserves the template except y_pred')
    p.add_argument('--submission', required=True)
    p.add_argument('--template', default=None)
    p.add_argument('--report', default=None)
    p.add_argument('--allow-unregistered-template', action='store_true')

    p = sub.add_parser('selftest', help='synthetic fixed-value checks of metrics, CSV splicing and validators')
    p.add_argument('--report', default=None)

    return parser


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    runners = {
        'verify-inputs': verify_inputs.run,
        'check-predictions': check_predictions.run,
        'score': score.run,
        'export': export_submission.run,
        'validate-submission': validate_submission.run,
        'selftest': selftest.run,
    }
    return runners[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
