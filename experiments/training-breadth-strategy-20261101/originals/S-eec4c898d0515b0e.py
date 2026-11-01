#!/usr/bin/env python3
"""Read-only check of whether a delivered callback has an actionable disposition."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def stamp(value):
    value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return value


def check(event_path, decision_path, now, notify_after=300):
    event_path, decision_path = Path(event_path), Path(decision_path)
    raw = event_path.read_bytes()
    event = json.loads(raw)
    sent = stamp(event["sent_at"])
    age = (now - sent).total_seconds()
    if age < 0 or notify_after <= 0:
        raise ValueError("invalid observation time or notification interval")
    result = {"event_id": event["event_id"], "elapsed_seconds": age,
              "actionably_consumed": False, "automatically_sends": False}
    if not decision_path.exists():
        return dict(result, state="needs_controller_action" if age >= notify_after else "awaiting_decision")
    decision = json.loads(decision_path.read_text())
    if decision.get("event_id") != event["event_id"]:
        raise ValueError("decision event mismatch")
    if decision.get("event_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("decision does not bind exact callback")
    kind = decision.get("decision")
    if kind in (None, "received", "review_pending"):
        return dict(result, state="needs_controller_action" if age >= notify_after else "awaiting_decision")
    if kind not in ("action_dispatched", "waiting_dependency", "needs_user", "closed"):
        raise ValueError("unsupported disposition")
    if not decision.get("next_owner") or not decision.get("next_action"):
        raise ValueError("missing accountable owner/action")
    if kind == "action_dispatched" and not decision.get("next_thread_id"):
        raise ValueError("dispatch lacks target thread")
    if kind == "waiting_dependency" and not (decision.get("dependency_id") and decision.get("wake_mechanism")):
        raise ValueError("dependency wait lacks actual dependency/wakeup")
    if kind == "needs_user" and not decision.get("user_question_reference"):
        raise ValueError("user wait lacks actual question")
    if kind == "closed" and not decision.get("closure_outcome"):
        raise ValueError("closure lacks explicit scope outcome")
    if not decision.get("evidence"):
        raise ValueError("disposition lacks evidence")
    for item in decision["evidence"]:
        path = Path(item["path"])
        if not path.is_absolute():
            path = decision_path.parent / path
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("disposition evidence checksum mismatch")
    return dict(result, state=kind, actionably_consumed=True,
                limitation="Evidence identity checked; controller must assess whether it actually supports the disposition.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", required=True)
    parser.add_argument("--decision", required=True)
    parser.add_argument("--now")
    parser.add_argument("--notify-after-seconds", type=int, default=300)
    args = parser.parse_args()
    try:
        now = stamp(args.now) if args.now else datetime.now(timezone.utc)
        result = check(args.event, args.decision, now, args.notify_after_seconds)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(json.dumps({"state": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["actionably_consumed"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
