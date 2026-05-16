"""Python+ prototype for MatVerse causal admissibility governance.

This module encodes the core formulas described in the CANÔNICO 3 FULL notes:
- Ω(x) = 0.4Ψ + 0.3Θ̂ + 0.2(1 − CVaR) + 0.1PoLE
- hard constraints: Ψ >= 0.85, CVaR <= 0.05, Ω >= 0.85
- execution law: Execution(x)=1 iff Validated ∧ Proved ∧ Recorded
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass(frozen=True)
class CausalSignal:
    psi: float
    theta_hat: float
    cvar: float
    pole: float


@dataclass(frozen=True)
class GovernanceDecision:
    event_id: str
    omega: float
    validated: bool
    proved: bool
    recorded: bool
    execution: bool
    reason: str

    def receipt(self) -> Dict[str, Any]:
        return asdict(self)


class OmegaGate:
    """Fail-closed admissibility gate for causal execution."""

    min_psi = 0.85
    max_cvar = 0.05
    min_omega = 0.85

    @classmethod
    def omega(cls, signal: CausalSignal) -> float:
        return (
            0.4 * signal.psi
            + 0.3 * signal.theta_hat
            + 0.2 * (1.0 - signal.cvar)
            + 0.1 * signal.pole
        )

    @classmethod
    def validate(cls, signal: CausalSignal) -> tuple[bool, str]:
        score = cls.omega(signal)
        if signal.psi < cls.min_psi:
            return False, f"psi_below_threshold:{signal.psi:.4f}"
        if signal.cvar > cls.max_cvar:
            return False, f"cvar_above_threshold:{signal.cvar:.4f}"
        if score < cls.min_omega:
            return False, f"omega_below_threshold:{score:.4f}"
        return True, "admissible"


class CausalLedger:
    """In-memory ledger supporting receipt append and deterministic replay."""

    def __init__(self) -> None:
        self._receipts: list[GovernanceDecision] = []

    def append(self, decision: GovernanceDecision) -> None:
        self._receipts.append(decision)

    def replay(self) -> list[Dict[str, Any]]:
        return [r.receipt() for r in self._receipts]


class MatVerseRuntime:
    """Minimal runtime implementing event → Ω-Gate → decision → receipt → ledger → replay."""

    def __init__(self) -> None:
        self.ledger = CausalLedger()

    def process_event(self, event_id: str, signal: CausalSignal, proved: bool) -> GovernanceDecision:
        validated, reason = OmegaGate.validate(signal)
        omega_score = OmegaGate.omega(signal)
        recorded = validated and proved
        execution = validated and proved and recorded

        decision = GovernanceDecision(
            event_id=event_id,
            omega=omega_score,
            validated=validated,
            proved=proved,
            recorded=recorded,
            execution=execution,
            reason=reason,
        )
        self.ledger.append(decision)
        return decision


def _demo() -> None:
    runtime = MatVerseRuntime()

    accepted = runtime.process_event(
        "evt-001",
        CausalSignal(psi=0.93, theta_hat=0.90, cvar=0.03, pole=0.90),
        proved=True,
    )
    rejected = runtime.process_event(
        "evt-002",
        CausalSignal(psi=0.81, theta_hat=0.95, cvar=0.02, pole=0.92),
        proved=True,
    )

    print("accepted:", accepted.receipt())
    print("rejected:", rejected.receipt())
    print("replay:", runtime.ledger.replay())


if __name__ == "__main__":
    _demo()
