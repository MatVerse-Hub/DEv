from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any


class Decision(StrEnum):
    PASS = "PASS"
    HOLD = "HOLD"
    REPAIR = "REPAIR"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"


class GovernanceError(ValueError):
    """Raised when the governance input is malformed."""


DEFAULT_THRESHOLDS = {
    "min_psi": 0.85,
    "max_cvar": 0.05,
    "min_omega": 0.85,
    "replay_required": True,
}

SENSITIVE_DATA_TYPES = {
    "precise_location",
    "payment_data",
    "bank_data",
    "identity_document",
    "health_data",
    "biometric_data",
    "minor_data",
    "private_image",
    "legal_document",
    "contract",
}

SENSITIVE_ACTIONS = {
    "send_email",
    "request_signature",
    "approve_contract",
    "send_invoice",
    "initiate_payment",
    "change_payroll",
    "publish_claim",
    "share_location",
    "export_customer_data",
    "delete_records",
    "clinical_claim",
    "legal_claim",
    "financial_claim",
}

DEFAULT_BLOCK_PATTERNS = {
    "ephemeral_room_for_evasion": [
        "delete everything",
        "leave no trace",
        "avoid records",
        "sem rastros",
        "apagar tudo",
        "chat secreto para cobrança",
    ],
    "coded_commercial_language": [
        "sem falar dinheiro",
        "não mencione valor",
        "cobrar sem parecer cobrança",
        "indirect payment",
    ],
    "clinical_overclaim": [
        "diagnose",
        "treat disease",
        "guaranteed cure",
        "diagnóstico clínico",
        "cura garantida",
    ],
    "unsupported_legal_or_financial_claim": [
        "guaranteed legal outcome",
        "garantia jurídica",
        "lucro garantido",
        "guaranteed profit",
    ],
}


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(data: Any) -> str:
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _as_set(value: Any, field_name: str) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, list):
        raise GovernanceError(f"{field_name} must be a list")
    return {str(item) for item in value}


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


@dataclass(frozen=True)
class GovernanceResult:
    decision: Decision
    omega: float
    psi: float
    theta: float
    cvar: float
    pole: float
    reasons: list[str]
    hard_blocks: list[str]
    receipt_hash: str
    replay_payload_hash: str
    ledger_record: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "omega": self.omega,
            "psi": self.psi,
            "theta": self.theta,
            "cvar": self.cvar,
            "pole": self.pole,
            "reasons": self.reasons,
            "hard_blocks": self.hard_blocks,
            "receipt_hash": self.receipt_hash,
            "replay_payload_hash": self.replay_payload_hash,
            "ledger_record": self.ledger_record,
        }


class GovernanceEngine:
    """Deterministic fail-closed governance engine for skill execution proposals."""

    def __init__(self, thresholds: dict[str, Any] | None = None) -> None:
        merged = dict(DEFAULT_THRESHOLDS)
        if thresholds:
            merged.update(thresholds)
        self.thresholds = merged

    def evaluate(self, manifest: dict[str, Any], request: dict[str, Any]) -> GovernanceResult:
        self._validate_manifest(manifest)
        self._validate_request(request)

        declared_connectors = _as_set(manifest.get("connectors"), "manifest.connectors")
        used_connectors = _as_set(request.get("connectors_used"), "request.connectors_used")
        declared_data = _as_set(manifest.get("data_access"), "manifest.data_access")
        requested_data = _as_set(request.get("data_access_requested"), "request.data_access_requested")
        manifest_sensitive_actions = _as_set(manifest.get("sensitive_actions"), "manifest.sensitive_actions")
        request_actions = _as_set(request.get("actions_requested"), "request.actions_requested")
        risk_classes = _as_set(manifest.get("risk_classes"), "manifest.risk_classes")

        text = " ".join(str(x).lower() for x in [request.get("intent", ""), request.get("purpose", ""), request.get("user_message", "")])
        reasons: list[str] = []
        hard_blocks: list[str] = []

        intent = str(request.get("intent", "")).strip()
        intent_clarity = 1.0 if len(intent) >= 12 else 0.2
        if intent_clarity < 0.85:
            reasons.append("unclear_intent")

        undeclared_connectors = sorted(used_connectors - declared_connectors)
        if undeclared_connectors:
            hard_blocks.append("undeclared_connector")
            reasons.append(f"undeclared_connectors:{','.join(undeclared_connectors)}")

        undeclared_data = sorted(requested_data - declared_data)
        if undeclared_data:
            hard_blocks.append("undeclared_data_access")
            reasons.append(f"undeclared_data_access:{','.join(undeclared_data)}")

        sensitive_data_used = bool(requested_data & SENSITIVE_DATA_TYPES)
        consent_required = sensitive_data_used or bool(risk_classes & {"privacy_risk", "health_risk", "customer_data_risk"})
        consent_valid = _as_bool(request.get("consent_valid"), default=False) if consent_required else True
        if consent_required and not consent_valid:
            hard_blocks.append("missing_consent_for_sensitive_data")
            reasons.append("consent_required_but_missing")

        sensitive_action_requested = bool(request_actions & (manifest_sensitive_actions | SENSITIVE_ACTIONS))
        human_approval_required = _as_bool(manifest.get("human_approval_required"), default=False) or sensitive_action_requested
        human_approval_valid = _as_bool(request.get("human_approval_valid"), default=False) if human_approval_required else True
        if human_approval_required and not human_approval_valid:
            hard_blocks.append("sensitive_action_without_human_approval")
            reasons.append("human_approval_required_but_missing")

        replay_possible = _as_bool(request.get("replay_possible"), default=False)
        if self.thresholds["replay_required"] and not replay_possible:
            if sensitive_action_requested:
                hard_blocks.append("no_replay_for_sensitive_action")
            reasons.append("replay_required_but_missing")

        if "precise_location" in requested_data and "location_required" not in request.get("justifications", {}):
            hard_blocks.append("precise_location_without_need")
            reasons.append("precise_location_requested_without_necessity")

        if "minor_data" in requested_data or request.get("age_context") in {"minor", "unknown"}:
            if sensitive_action_requested or "private_image" in requested_data:
                hard_blocks.append("minor_or_age_uncertain_sensitive_context")
                reasons.append("minor_or_unknown_age_sensitive_context")

        for block_name, patterns in DEFAULT_BLOCK_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                hard_blocks.append(block_name)
                reasons.append(f"blocked_pattern:{block_name}")

        if "clinical_claim" in request_actions and not request.get("clinical_validation"):
            hard_blocks.append("clinical_overclaim")
            reasons.append("clinical_claim_without_validation")

        if ("legal_claim" in request_actions or "financial_claim" in request_actions) and not request.get("claim_evidence"):
            hard_blocks.append("unsupported_legal_or_financial_claim")
            reasons.append("legal_or_financial_claim_without_evidence")

        connector_policy = 1.0 if not undeclared_connectors else 0.0
        data_policy = 1.0 if not undeclared_data else 0.0
        consent_integrity = 1.0 if consent_valid else 0.0
        approval_integrity = 1.0 if human_approval_valid else 0.0
        replayability = 1.0 if replay_possible else 0.0
        evidence_quality = max(0.0, min(1.0, float(request.get("evidence_quality", 0.0))))

        psi = round(sum([intent_clarity, connector_policy, data_policy, consent_integrity, approval_integrity, replayability, evidence_quality, 1.0]) / 8, 6)
        theta = round(0.30 * connector_policy + 0.25 * data_policy + 0.20 * replayability + 0.15 * approval_integrity + 0.10 * evidence_quality, 6)
        cvar = round(self._cvar_tail_risk(self._risk_events(sensitive_data_used, sensitive_action_requested, consent_valid, human_approval_valid, replay_possible, hard_blocks, request)), 6)
        pole = round(1.0 if not hard_blocks and not undeclared_connectors and not undeclared_data else 0.0, 6)
        omega = round(0.4 * psi + 0.3 * theta + 0.2 * (1 - cvar) + 0.1 * pole, 6)

        decision = self._decide(psi=psi, cvar=cvar, omega=omega, pole=pole, hard_blocks=hard_blocks, request=request)
        if decision != Decision.PASS and not reasons:
            reasons.append("thresholds_not_satisfied")

        replay_payload = {
            "engine": "matverse-skill-governance",
            "version": "0.1.0",
            "thresholds": self.thresholds,
            "manifest_hash": sha256_json(manifest),
            "request_hash": sha256_json(request),
            "decision_inputs": {"psi": psi, "theta": theta, "cvar": cvar, "pole": pole, "omega": omega, "hard_blocks": sorted(set(hard_blocks)), "reasons": reasons},
        }
        replay_payload_hash = sha256_json(replay_payload)
        receipt = {
            "skill_id": manifest["skill_id"],
            "domain": manifest["domain"],
            "decision": decision.value,
            "metrics": {"psi": psi, "theta": theta, "cvar": cvar, "pole": pole, "omega": omega},
            "hard_blocks": sorted(set(hard_blocks)),
            "reasons": reasons,
            "replay_payload_hash": replay_payload_hash,
        }
        receipt_hash = sha256_json(receipt)
        ledger_record = {
            "timestamp": utc_now_iso(),
            "record_type": "skill_governance_receipt",
            "receipt_hash": receipt_hash,
            "receipt": receipt,
            "manifest_hash": sha256_json(manifest),
            "request_hash": sha256_json(request),
            "replay_payload": replay_payload,
        }
        return GovernanceResult(decision, omega, psi, theta, cvar, pole, reasons, sorted(set(hard_blocks)), receipt_hash, replay_payload_hash, ledger_record)

    def append_ledger(self, result: GovernanceResult, ledger_path: str | Path) -> str:
        path = Path(ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        previous_hash = None
        if path.exists():
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if lines:
                previous_hash = json.loads(lines[-1])["chain_hash"]
        payload = dict(result.ledger_record)
        payload["previous_hash"] = previous_hash
        payload["chain_hash"] = hashlib.sha256((canonical_json(payload) + (previous_hash or "")).encode("utf-8")).hexdigest()
        with path.open("a", encoding="utf-8") as f:
            f.write(canonical_json(payload) + "\n")
        return payload["chain_hash"]

    def replay(self, manifest: dict[str, Any], request: dict[str, Any], expected_receipt_hash: str) -> bool:
        return self.evaluate(manifest, request).receipt_hash == expected_receipt_hash

    def _validate_manifest(self, manifest: dict[str, Any]) -> None:
        required = ["skill_id", "domain", "connectors", "data_access", "sensitive_actions", "risk_classes"]
        missing = [field for field in required if field not in manifest]
        if missing:
            raise GovernanceError(f"manifest missing required fields: {', '.join(missing)}")

    def _validate_request(self, request: dict[str, Any]) -> None:
        required = ["intent", "connectors_used", "data_access_requested", "actions_requested", "replay_possible"]
        missing = [field for field in required if field not in request]
        if missing:
            raise GovernanceError(f"request missing required fields: {', '.join(missing)}")

    def _risk_events(self, sensitive_data_used: bool, sensitive_action_requested: bool, consent_valid: bool, human_approval_valid: bool, replay_possible: bool, hard_blocks: list[str], request: dict[str, Any]) -> list[float]:
        risks = [0.01]
        if sensitive_data_used:
            risks.append(0.02)
        if sensitive_action_requested:
            risks.append(0.02)
        if not consent_valid:
            risks.append(0.50)
        if not human_approval_valid:
            risks.append(0.45)
        if not replay_possible:
            risks.append(0.25)
        if hard_blocks:
            risks.extend([0.90] * len(set(hard_blocks)))
        try:
            declared_risk_float = float(request.get("declared_risk", 0.0))
        except (TypeError, ValueError):
            declared_risk_float = 1.0
        if not math.isfinite(declared_risk_float):
            declared_risk_float = 1.0
        risks.append(max(0.0, min(1.0, declared_risk_float)))
        return risks

    def _cvar_tail_risk(self, risk_events: list[float], alpha: float = 0.95) -> float:
        if not risk_events:
            return 1.0
        ordered = sorted(max(0.0, min(1.0, float(x))) for x in risk_events)
        tail_start = max(0, int(math.floor(alpha * (len(ordered) - 1))))
        tail = ordered[tail_start:]
        return sum(tail) / len(tail)

    def _decide(self, *, psi: float, cvar: float, omega: float, pole: float, hard_blocks: list[str], request: dict[str, Any]) -> Decision:
        if hard_blocks:
            return Decision.BLOCK
        if any(not math.isfinite(x) for x in [psi, cvar, omega, pole]):
            return Decision.BLOCK
        if request.get("expert_review_required"):
            return Decision.ESCALATE
        if cvar > self.thresholds["max_cvar"]:
            return Decision.BLOCK
        if psi >= self.thresholds["min_psi"] and omega >= self.thresholds["min_omega"]:
            return Decision.PASS
        if psi < 0.55:
            return Decision.REPAIR
        return Decision.HOLD


def evaluate_skill_request(manifest: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    return GovernanceEngine(manifest.get("gate_policy")).evaluate(manifest, request).to_dict()
