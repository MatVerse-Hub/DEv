from matverse_skill_governance.engine import Decision, GovernanceEngine


def manifest():
    return {
        "skill_id": "business_gate",
        "domain": "small_business_operations",
        "connectors": ["gmail", "google_drive", "stripe", "quickbooks"],
        "data_access": ["metadata", "invoice", "payment_data"],
        "sensitive_actions": ["send_invoice"],
        "human_approval_required": True,
        "retention_policy": "hash_receipt_only_by_default",
        "risk_classes": ["privacy_risk", "financial_commitment_risk"],
        "gate_policy": {
            "min_psi": 0.85,
            "max_cvar": 0.05,
            "min_omega": 0.85,
            "replay_required": True,
        },
    }


def passing_request():
    return {
        "intent": "Compile approved monthly invoice events and prepare a replayable month-close evidence pack.",
        "connectors_used": ["gmail", "google_drive", "stripe", "quickbooks"],
        "data_access_requested": ["metadata", "invoice", "payment_data"],
        "actions_requested": ["send_invoice"],
        "consent_valid": True,
        "human_approval_valid": True,
        "replay_possible": True,
        "evidence_quality": 0.98,
        "declared_risk": 0.01,
        "claim_evidence": True,
        "justifications": {"payment_data": "Required for reconciliation."},
    }


def test_pass_request():
    engine = GovernanceEngine(manifest()["gate_policy"])
    result = engine.evaluate(manifest(), passing_request())
    assert result.decision == Decision.PASS
    assert result.omega >= 0.85
    assert result.cvar <= 0.05
    assert result.receipt_hash


def test_block_missing_approval_and_consent():
    req = passing_request()
    req["consent_valid"] = False
    req["human_approval_valid"] = False
    result = GovernanceEngine(manifest()["gate_policy"]).evaluate(manifest(), req)
    assert result.decision == Decision.BLOCK
    assert "missing_consent_for_sensitive_data" in result.hard_blocks
    assert "sensitive_action_without_human_approval" in result.hard_blocks


def test_block_undeclared_connector():
    req = passing_request()
    req["connectors_used"] = ["gmail", "unknown_chat"]
    result = GovernanceEngine(manifest()["gate_policy"]).evaluate(manifest(), req)
    assert result.decision == Decision.BLOCK
    assert "undeclared_connector" in result.hard_blocks


def test_replay_receipt_hash():
    engine = GovernanceEngine(manifest()["gate_policy"])
    result = engine.evaluate(manifest(), passing_request())
    assert engine.replay(manifest(), passing_request(), result.receipt_hash) is True
