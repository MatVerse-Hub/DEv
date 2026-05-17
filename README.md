# MatVerse Skill Governance Layer

ACOA Skill Governance Layer for governing vertical agent skills before execution.

## Core thesis

Agent marketplaces sell capability.

MatVerse sells admissible capability.

This repository implements a deterministic governance layer for agent skills, connectors, sensitive actions, consent, human approval, CVaR-style risk control, receipts, ledger records and replayable evidence.

## Canonical flow

```text
Intent
→ Skill Manifest
→ Connector Policy
→ MNB Compilation
→ Ω-Gate
→ CVaR / Risk
→ Consent / Human Approval
→ Execution Proposal
→ Receipt
→ Ledger
→ Replay
→ Evidence Pack
```

## Decisions

- `PASS`: action admissible.
- `HOLD`: insufficient evidence or weak confidence.
- `REPAIR`: manifest/request must be corrected.
- `BLOCK`: constitutional violation or unacceptable risk.
- `ESCALATE`: human expert review required.

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest -q

matverse-skill-governance evaluate \
  --manifest examples/manifest_business_gate.json \
  --request examples/request_pass.json
```

## Product position

This is not another agent. It is a governance layer for skills, workflows, connectors and vertical agent marketplaces.
