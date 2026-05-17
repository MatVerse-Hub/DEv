install:
	python -m pip install -U pip
	pip install -e ".[dev]"

test:
	pytest -q

pass:
	matverse-skill-governance evaluate --manifest examples/manifest_business_gate.json --request examples/request_pass.json

block:
	matverse-skill-governance evaluate --manifest examples/manifest_business_gate.json --request examples/request_block.json

ledger-pass:
	matverse-skill-governance evaluate --manifest examples/manifest_business_gate.json --request examples/request_pass.json --ledger ledger.jsonl
