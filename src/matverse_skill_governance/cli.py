from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import GovernanceEngine


def load_json(path: str) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def cmd_evaluate(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    request = load_json(args.request)
    engine = GovernanceEngine(manifest.get("gate_policy"))
    result = engine.evaluate(manifest, request)
    payload = result.to_dict()
    if args.ledger:
        payload["chain_hash"] = engine.append_ledger(result, args.ledger)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_replay(args: argparse.Namespace) -> int:
    manifest = load_json(args.manifest)
    request = load_json(args.request)
    engine = GovernanceEngine(manifest.get("gate_policy"))
    ok = engine.replay(manifest, request, args.expected_receipt_hash)
    print(json.dumps({"replay": ok}, indent=2))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="matverse-skill-governance")
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser("evaluate", help="Evaluate a skill execution request.")
    evaluate.add_argument("--manifest", required=True)
    evaluate.add_argument("--request", required=True)
    evaluate.add_argument("--ledger", required=False)
    evaluate.set_defaults(func=cmd_evaluate)

    replay = sub.add_parser("replay", help="Replay a request and verify receipt hash.")
    replay.add_argument("--manifest", required=True)
    replay.add_argument("--request", required=True)
    replay.add_argument("--expected-receipt-hash", required=True)
    replay.set_defaults(func=cmd_replay)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
