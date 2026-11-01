"""Download only the official submission template; never modify raw data."""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
URL = "http://www.aiinnovation.com.cn/file/down/" + urllib.parse.quote(
    "小分子药物预测技术创新赛-结果提交模板.csv"
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path,
                        default=PACKAGE / "reference/submission_template.csv")
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"Refusing to overwrite existing template: {args.output}")
    content = urllib.request.urlopen(URL, timeout=45).read()
    if not content.decode("utf-8-sig").startswith("task,sample_idx,drug_id,smiles,y_pred,metric"):
        raise SystemExit("Unexpected template schema; download not saved")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(content)
    metadata = {"source_url": URL, "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                "sha256": hashlib.sha256(content).hexdigest(), "bytes": len(content)}
    args.output.with_suffix(".source.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == "__main__":
    main()
