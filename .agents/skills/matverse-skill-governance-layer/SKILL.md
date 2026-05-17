# MatVerse Skill Governance Layer

## Purpose

Use this skill when an agent skill, connector, workflow or external action must be evaluated before execution.

The skill enforces admissibility through intent clarity, connector declaration, data minimization, consent, human approval, CVaR-style risk, receipts, ledger and replay.

## Activation triggers

- User asks to audit, approve or execute a skill.
- A connector is about to access business, customer, legal, financial, biomedical, location or private data.
- A workflow includes sensitive action.
- A marketplace-style skill must be classified before installation or use.
- A request involves temporary private communication, customer contact, location, private images, payments, contracts or claims.

## Canonical flow

```text
Intent
→ Skill Manifest
→ Connector Policy
→ Ω-Gate
→ CVaR
→ Consent / Human Approval
→ Receipt
→ Ledger
→ Replay
→ Evidence Pack
```

## Fail-closed rules

Block when:

- consent is missing for sensitive data
- sensitive action lacks human approval
- connector is undeclared
- data access is undeclared
- sensitive action has no replay path
- precise location is requested without necessity
- private image, minor or unknown age context is present
- clinical, legal or financial claim lacks evidence
- request implies hidden purpose, evasion, deletion of legitimate traces or coded commercial language

## Output

Return:

- decision: PASS / HOLD / REPAIR / BLOCK / ESCALATE
- reasons
- hard blocks
- Ψ, Θ, CVaR, PoLE, Ω
- receipt hash
- replay payload hash
- ledger record
