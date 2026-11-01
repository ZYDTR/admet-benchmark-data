"""Offline gateway invariants. Never proves scientific truth or actual reading."""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import urlparse
import zipfile

FILES = ("analysis.md", "review.json", "issues.json", "next_batch_guide.md",
         "next_experiments.json", "search_space.json")
LAYERS = ("root", "context", "history", "current_batch", "related_originals")
KINDS = ("applicable_rule_and_source", "historical_refutation_chain",
         "current_configuration_or_direct_numeric_check")
RECEIPT_FIELDS = ("entry_id", "layer", "uri", "source_version", "read_mode",
                  "evidence_locator", "observed_fact", "limitation")
REVIEW_FIELDS = ("schema_version", "request_id", "round_id", "manifest_sha256",
                 "status", "read_receipt", "read_checks", "findings",
                 "missing_evidence", "not_assessed", "comparison_groups", "stop_reasons")
ITEMS = {
    "issues.json": ("issues", "issue_id", "issue_id status severity category statement affected_run_ids evidence_refs hypothesis counterevidence impact proposed_resolution verification_criterion related_proposal_ids".split()),
    "next_experiments.json": ("experiments", "proposal_id", "proposal_id priority hypothesis control_run_or_config task asset_versions change_only hold_fixed split_id seeds metric direction minimum_effect_or_decision_rule success_criterion falsification_criterion compute_budget dependencies within_current_scope".split()),
    "search_space.json": ("directions", "direction_id", "direction_id linked_issues rationale evidence_refs counterevidence candidate_models_or_modules parameters combination_constraints search_method configuration_count_or_counting_rule seeds estimated_run_count cost_assumptions readiness priority scope_status".split()),
}


class ContractError(ValueError):
    pass


def require(ok, code):
    if not ok:
        raise ContractError(code)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate_json_key:" + key)
            result[key] = value
        return result
    def constant(value):
        raise ContractError("nonfinite_json:" + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def safe_relative(name):
    require(isinstance(name, str) and bool(name), "empty_path")
    p = PurePosixPath(name)
    require(not p.is_absolute() and ".." not in p.parts and "\\" not in name
            and ":" not in name and not any(ord(c) < 32 for c in name), "unsafe_path:" + name)
    require(name == p.as_posix() and name not in (".", ""), "noncanonical_path:" + name)
    return p


def safe_file(root, name):
    p = safe_relative(name)
    root = Path(root)
    require(root.is_dir() and not root.is_symlink(), "unsafe_root")
    item = root
    for part in p.parts:
        item = item / part
        require(not item.is_symlink(), "symlink_path:" + name)
    require(item.is_file(), "missing_file:" + name)
    require(item.resolve().is_relative_to(root.resolve()), "outside_root:" + name)
    return item


def inspect_zip(path, max_members=2000, max_bytes=200_000_000):
    with zipfile.ZipFile(path) as z:
        infos = z.infolist()
        require(len(infos) <= max_members, "zip_member_budget")
        require(sum(x.file_size for x in infos) <= max_bytes, "zip_byte_budget")
        names = set()
        for info in infos:
            name = info.filename.rstrip("/") if info.is_dir() else info.filename
            safe_relative(name)
            require(name not in names, "duplicate_zip_member:" + name)
            names.add(name)
            require(not stat.S_ISLNK((info.external_attr >> 16) & 0xffff), "zip_symlink:" + name)
            require(not (info.flag_bits & 1), "encrypted_zip:" + name)
        bad = z.testzip()
        require(bad is None, "zip_crc:" + str(bad))
    return {"state": "verified", "members": len(infos),
            "bytes": Path(path).stat().st_size, "sha256": digest(Path(path).read_bytes()),
            "crc": "PASS", "source_code_executed": False}


def pinned(uri, commit, repository):
    if not isinstance(uri, str):
        return False
    u = urlparse(uri)
    owner_repo = urlparse(repository).path.strip("/").split("/")
    parts = u.path.strip("/").split("/")
    if u.scheme != "https" or len(owner_repo) != 2:
        return False
    if u.hostname == "raw.githubusercontent.com":
        return len(parts) >= 4 and parts[:2] == owner_repo and parts[2] == commit
    if u.hostname == "github.com":
        return (len(parts) >= 5 and parts[:2] == owner_repo
                and parts[2] in ("blob", "tree") and parts[3] == commit)
    return False


def validate_plan(plan):
    commit = plan.get("source_commit", "")
    require(bool(re.fullmatch(r"[0-9a-f]{40}", commit)), "unsealed_commit")
    entries = plan.get("entries", [])
    require(isinstance(entries, list) and entries, "missing_read_plan")
    ids = set()
    layers = set()
    for item in entries:
        require(all(k in item for k in ("entry_id", "layer", "uri", "source_version", "required_read_mode")),
                "read_plan_fields")
        require(item["entry_id"] not in ids, "duplicate_plan_entry")
        ids.add(item["entry_id"])
        require(item["layer"] in LAYERS, "unknown_plan_layer")
        layers.add(item["layer"])
        require(item["source_version"] == commit, "mixed_source_version")
        require(item["required_read_mode"] == "original", "mandatory_plan_not_original")
        require(pinned(item["uri"], commit, plan["repository"]), "mutable_or_wrong_repository_uri")
    require(set(LAYERS).issubset(layers), "missing_required_layer:" + ",".join(set(LAYERS) - layers))


def check_read_contract(review, plan):
    validate_plan(plan)
    receipts = review.get("read_receipt")
    require(isinstance(receipts, list), "read_receipt_not_array")
    by_id = {}
    for item in receipts:
        require(isinstance(item, dict) and all(k in item for k in RECEIPT_FIELDS), "read_receipt_fields")
        require(item["entry_id"] not in by_id, "duplicate_receipt_entry")
        require(item["read_mode"] in ("original", "summary", "hash_only", "unread"), "unknown_read_mode")
        require(bool(item["evidence_locator"]) and bool(item["observed_fact"]), "empty_read_evidence")
        by_id[item["entry_id"]] = item
    for item in plan["entries"]:
        require(item["entry_id"] in by_id, "missing_mandatory_entry:" + item["entry_id"])
        actual = by_id[item["entry_id"]]
        for key in ("layer", "uri", "source_version"):
            require(actual[key] == item[key], "receipt_plan_mismatch:" + item["entry_id"] + ":" + key)
        require(actual["read_mode"] == "original", "mandatory_not_original:" + item["entry_id"])
    checks = review.get("read_checks")
    require(isinstance(checks, list) and len(checks) >= 3, "missing_independent_checks")
    ids = set()
    for item in checks:
        require(all(k in item for k in ("check_id", "kind", "answer", "input_locator", "method", "evidence_refs")),
                "read_check_fields")
        require(item["check_id"] not in ids, "duplicate_read_check")
        ids.add(item["check_id"])
        require(bool(item["method"]) and bool(item["input_locator"]) and bool(item["evidence_refs"]),
                "empty_read_check_method")
    require(set(KINDS).issubset({x["kind"] for x in checks}), "missing_independent_check_kind")
    return {"state": "structure_passed", "mandatory_entries": len(plan["entries"]),
            "actual_original_read_proven": False}


def exact(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def compare_oracle(review, plan, expected, oracle):
    require(oracle is not None, "independent_oracle_pending")
    for key in ("request_id", "round_id", "manifest_sha256"):
        require(oracle.get(key) == expected[key], "oracle_identity:" + key)
    require(oracle.get("source_commit") == plan["source_commit"], "oracle_source_version")
    rows = {x["check_id"]: x for x in review["read_checks"]}
    specs = oracle.get("checks", [])
    require(len(specs) == 3 and {x["kind"] for x in specs} == set(KINDS), "oracle_three_kinds")
    results = []
    for spec in specs:
        require(spec["check_id"] in rows, "oracle_check_missing")
        actual = rows[spec["check_id"]]
        require(actual["kind"] == spec["kind"], "oracle_check_kind")
        if spec["comparison"] == "exact_json":
            passed = exact(actual["answer"], spec["expected"])
        elif spec["comparison"] == "decimal":
            require(not isinstance(actual["answer"], bool), "boolean_numeric_answer")
            a, b, tol = map(lambda v: Decimal(str(v)),
                            (actual["answer"], spec["expected"], spec["absolute_tolerance"]))
            require(a.is_finite() and b.is_finite() and tol.is_finite() and tol >= 0, "invalid_numeric_oracle")
            passed = abs(a - b) <= tol
        else:
            raise ContractError("unsupported_oracle_comparison")
        require(passed, "independent_value_mismatch:" + spec["check_id"])
        results.append({"check_id": spec["check_id"], "value_match": True})
    return {"state": "configured_values_match", "results": results,
            "controller_evidence_judgment_still_required": True}


def validate_dispatch_gate(gate):
    """Checks declared preconditions only; does not create a Chat or authorize itself."""
    require(gate.get("creation_mode") == "create_new_once_after_packet_acceptance",
            "not_registered_product_chat_mode")
    require(gate.get("maximum_analysis_requests") == 1, "not_single_creation_slot")
    require(gate.get("scope") == "analysis_product_chat_only", "executor_creation_not_allowed")
    require(gate.get("creation_key") == gate.get("cycle_id", "") + ":" + gate.get("request_id", ""),
            "creation_key_not_bound")
    require(gate.get("request_id") != gate.get("old_request_id"), "old_request_cannot_be_recreated")
    require(gate.get("new_request_send_state") == "not_sent", "new_send_unknown_or_already_sent")
    require(gate.get("send_attempts_started") == 0, "creation_slot_already_claimed")
    require(gate.get("actual_chat_id") is None, "existing_target_requires_reconciliation")
    require(gate.get("controller_packet_accepted") is True, "packet_not_accepted")
    require(bool(gate.get("controller_acceptance_evidence")), "packet_acceptance_evidence_missing")
    require(gate.get("pro_observed") is True and gate.get("empty_history_observed") is True,
            "actual_pro_or_blank_history_not_verified")
    prompt = gate.get("frozen_prompt", "")
    require(bool(prompt.strip()) and "{{" not in prompt and "}}" not in prompt, "unresolved_or_placeholder_prompt")
    require(gate.get("prompt_sha256") == digest(prompt.encode("utf-8")), "frozen_prompt_hash_mismatch")
    # An accepted old artifact delivery with an unknown generation terminal is not
    # an unknown send of this distinct new request. Never cancels or resends the old one.
    return {"state": "declared_preconditions_passed", "creates_chat": False,
            "requires_actual_UI_and_controller_evidence": True,
            "old_terminal_state_preserved": gate.get("old_terminal_state", "unknown")}


def check_bundle(root, expected, plan, oracle=None):
    errors = []
    result = {"artifact_state": "unverified", "scientific_status": None,
              "chat_terminal_state": "unknown", "read_contract_state": "unverified",
              "independent_check_state": "pending", "fresh_chat_read_verified": False,
              "scientific_acceptance": "controller_pending", "errors": errors}
    try:
        manifest = strict_json(safe_file(root, "delivery-manifest.json").read_bytes())
        for key in ("request_id", "round_id", "manifest_sha256"):
            require(manifest.get(key) == expected[key], "delivery_identity:" + key)
        require(manifest.get("scientific_status") in ("complete", "needs_evidence", "inconclusive"),
                "delivery_scientific_status")
        rows = manifest.get("files", [])
        require(isinstance(rows, list) and len(rows) == len(FILES), "six_manifest_members")
        names, parsed, checked = set(), {}, []
        for row in rows:
            require(all(k in row for k in ("path", "bytes", "sha256")), "delivery_file_fields")
            f = safe_file(root, row["path"])
            name = f.name
            require(name in FILES and name not in names, "duplicate_or_unexpected_artifact:" + name)
            names.add(name)
            require(type(row["bytes"]) is int and row["bytes"] > 0, "invalid_file_length")
            require(bool(re.fullmatch(r"[0-9a-f]{64}", row["sha256"])), "invalid_file_digest")
            raw = f.read_bytes()
            require(len(raw) == row["bytes"] and digest(raw) == row["sha256"], "artifact_hash_or_size:" + name)
            text = raw.decode("utf-8")
            require(bool(text.strip()), "empty_artifact:" + name)
            require(re.search(r"(?m)^\s*(?:\.\.\.|…|TODO|此处省略|其余同上)\s*$", text) is None,
                    "standalone_placeholder:" + name)
            if name.endswith(".json"):
                parsed[name] = strict_json(raw)
                for key in ("request_id", "round_id", "manifest_sha256"):
                    require(parsed[name].get(key) == expected[key], "artifact_identity:" + name + ":" + key)
            checked.append({"path": row["path"], "bytes": len(raw), "sha256": digest(raw)})
        require(names == set(FILES), "missing_artifact")
        review = parsed["review.json"]
        require(all(k in review for k in REVIEW_FIELDS), "review_required_fields")
        require(review["status"] == manifest["scientific_status"], "scientific_status_mismatch")
        guide = safe_file(root, next(x["path"] for x in rows
                                    if PurePosixPath(x["path"]).name == "next_batch_guide.md")).read_text()
        for field in "work_item_id issue_ids goal model_and_asset_versions input_contract output_contract implementation_scope frozen_components preparation_steps dependencies acceptance_checks priority budget blocked_fallback".split():
            require(field in guide, "guide_field_label:" + field)
        for name, (container, id_key, fields) in ITEMS.items():
            items = parsed[name].get(container)
            require(isinstance(items, list), "artifact_item_array:" + name)
            seen = set()
            for item in items:
                require(isinstance(item, dict) and all(k in item for k in fields), "artifact_item_fields:" + name)
                require(item[id_key] not in seen, "duplicate_item_id:" + name)
                seen.add(item[id_key])
        result.update(artifact_state="verified", scientific_status=review["status"], files=checked)
        result["read_contract"] = check_read_contract(review, plan)
        result["read_contract_state"] = "structure_passed"
        if oracle is not None:
            result["independent_checks"] = compare_oracle(review, plan, expected, oracle)
            result["independent_check_state"] = "configured_values_match"
    except (ContractError, ValueError, KeyError, TypeError, OSError, UnicodeError, InvalidOperation) as exc:
        errors.append(str(exc))
    result["status"] = ("eligible_for_controller_review" if not errors
                        and result["independent_check_state"] == "configured_values_match"
                        else "structure_only_pending_oracle" if not errors else "rejected")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--read-plan", type=Path, required=True)
    parser.add_argument("--oracle", type=Path)
    args = parser.parse_args()
    result = check_bundle(args.bundle, strict_json(args.expected.read_bytes()),
                          strict_json(args.read_plan.read_bytes()),
                          strict_json(args.oracle.read_bytes()) if args.oracle else None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
