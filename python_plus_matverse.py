"""Python+ prototype for MatVerse causal admissibility governance.

This module encodes the core formulas described in the CANÔNICO 3 FULL notes:
- Ω(x) = 0.4Ψ + 0.3Θ̂ + 0.2(1 − CVaR) + 0.1PoLE
- hard constraints: Ψ >= 0.85, CVaR <= 0.05, Ω >= 0.85
- execution law: Execution(x)=1 iff Validated ∧ Proved ∧ Recorded
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class CausalSignal:
    psi: float
    theta_hat: float
    cvar: float
    pole: float


@dataclass(frozen=True)
class ValidationResult:
    """Result produced by Ω-Gate validation.

    The omega score is returned with the admissibility decision so the receipt
    reflects the exact score that was validated. This avoids recomputing Ω in
    the runtime and keeps the gate as the single source of constitutional truth.
    """

    valid: bool
    omega: float
    reason: str


@dataclass(frozen=True)
class GovernanceDecision:
    event_id: str
    omega: float
    validated: bool
    proved: bool
    recorded: bool
    execution: bool
    reason: str
    receipt_hash: Optional[str] = None

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
    def validate(cls, signal: CausalSignal) -> ValidationResult:
        score = cls.omega(signal)
        if signal.psi < cls.min_psi:
            return ValidationResult(False, score, f"psi_below_threshold:{signal.psi:.4f}")
        if signal.cvar > cls.max_cvar:
            return ValidationResult(False, score, f"cvar_above_threshold:{signal.cvar:.4f}")
        if score < cls.min_omega:
            return ValidationResult(False, score, f"omega_below_threshold:{score:.4f}")
        return ValidationResult(True, score, "admissible")


class CausalLedger:
    """In-memory ledger supporting receipt append and deterministic replay."""

    def __init__(self) -> None:
        self._receipts: list[GovernanceDecision] = []

    def append(self, decision: GovernanceDecision) -> bool:
        """Append a decision receipt and report whether recording succeeded.

        Recording is intentionally independent from validation/proof. This keeps
        Execution(x)=Validated ∧ Proved ∧ Recorded meaningful: if storage fails
        or policy later rejects persistence, execution must remain false.
        """

        self._receipts.append(decision)
        return self._receipts[-1] is decision

    def replay(self) -> list[Dict[str, Any]]:
        return [r.receipt() for r in self._receipts]


class MatVerseRuntime:
    """Minimal runtime implementing event → Ω-Gate → decision → receipt → ledger → replay."""

    def __init__(self) -> None:
        self.ledger = CausalLedger()

    def process_event(self, event_id: str, signal: CausalSignal, proved: bool) -> GovernanceDecision:
        validation = OmegaGate.validate(signal)

        provisional = GovernanceDecision(
            event_id=event_id,
            omega=validation.omega,
            validated=validation.valid,
            proved=proved,
            recorded=False,
            execution=False,
            reason=validation.reason,
        )

        recorded = self.ledger.append(provisional) if validation.valid and proved else False
        execution = validation.valid and proved and recorded

        decision = GovernanceDecision(
            event_id=event_id,
            omega=validation.omega,
            validated=validation.valid,
            proved=proved,
            recorded=recorded,
            execution=execution,
            reason=validation.reason,
        )

        if recorded:
            self.ledger._receipts[-1] = decision

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
