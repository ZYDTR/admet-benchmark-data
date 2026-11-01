"""Write ``assets.lock.json`` for the downloaded CheMeleon checkpoint.

Run by MAIN CONTROL after downloading the weights (this prep session did not
download them):

    python3 make_asset_lock.py --weights /abs/path/chemeleon_mp.pt \
        --out assets.lock.json

Refuses to write unless size == 34,859,448 and MD5 ==
``6a80b54fdb7de37ef0374d302f01e8ce`` (publisher values pinned in ``assets.py``);
the SHA256 is recorded from the file so the feature cache is bound to the exact
bytes that produced it.  ``--code-commit`` must equal the pinned commit.
"""

import argparse
import json
import os
import sys

from assets import (
    CHEMELEON_CODE_COMMIT,
    CHEMELEON_DOWNLOAD_URL,
    CHEMELEON_LICENSE,
    CHEMELEON_ZENODO_DOI,
    verify_weights_file,
)
from errors import InputContractError


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--code-commit", default=CHEMELEON_CODE_COMMIT)
    ap.add_argument("--feature-dim", type=int, default=None,
                    help="observed encoder output width; record it once measured")
    args = ap.parse_args(argv)

    try:
        info = verify_weights_file(args.weights)
    except InputContractError as exc:
        print(f"[asset-lock] refused: {exc}", file=sys.stderr)
        return 1
    if args.code_commit != CHEMELEON_CODE_COMMIT:
        print(f"[asset-lock] refused: code commit {args.code_commit} != pinned "
              f"{CHEMELEON_CODE_COMMIT}", file=sys.stderr)
        return 1

    lock = {
        "weights_file": "chemeleon_mp.pt",
        "weights_size": info["size"],
        "weights_md5": info["md5"],
        "weights_sha256": info["sha256"],
        "code_commit": args.code_commit,
        "zenodo_doi": CHEMELEON_ZENODO_DOI,
        "download_url": CHEMELEON_DOWNLOAD_URL,
        "license": CHEMELEON_LICENSE,
    }
    if args.feature_dim is not None:
        lock["feature_dim"] = args.feature_dim

    out = os.path.abspath(args.out)
    tmp = out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(lock, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, out)
    print(json.dumps(lock, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())