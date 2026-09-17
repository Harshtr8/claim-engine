from datetime import datetime

from app.orchestrator.state import ClaimEngineState
from app.schemas.decision import (
    Citation,
    DecisionOutput,
    ValidationResult,
)


VALID_DECISIONS = {
    "ADMISSIBLE",
    "ADMISSIBLE_WITH_LIMITS",
    "PARTIALLY_ADMISSIBLE",
    "NOT_ADMISSIBLE",
    "NEEDS_REVIEW",
}


class DecisionAgent:

    name = "DecisionAgent"

    def run(
        self,
        state: ClaimEngineState,
    ) -> ClaimEngineState:

        start_time = datetime.now()

        claim = state["claim"]
        case_analysis = state.get(
            "case_analysis",
            {},
        )
        coverage = state.get(
            "coverage_analysis",
            {},
        )
        evidence = state.get(
            "policy_evidence",
            [],
        )

        findings = coverage.get(
            "findings",
            [],
        )

        limits = coverage.get(
            "applicable_limits",
            [],
        )

        missing_evidence = coverage.get(
            "missing_evidence",
            [],
        )

        deductions = coverage.get(
            "deductions",
            [],
        )

        decision = "NEEDS_REVIEW"

        confidence = 0.50

        if not evidence:

            decision = "NEEDS_REVIEW"
            confidence = 0.20

        elif missing_evidence:

            decision = "NEEDS_REVIEW"
            confidence = 0.40

        elif deductions:

            decision = "ADMISSIBLE_WITH_LIMITS"
            confidence = 0.75

        else:

            decision = "ADMISSIBLE"
            confidence = 0.70

        if decision not in VALID_DECISIONS:
            decision = "NEEDS_REVIEW"

        citations = []

        for item in evidence[:5]:

            citations.append(
                Citation(
                    claim=(
                        "Relevant policy evidence retrieved "
                        "for claim analysis."
                    ),
                    source=item["source"],
                    page=item["page"],
                    section=item["section"],
                    chunk_id=item["chunk_id"],
                )
            )

        validation = ValidationResult(
            status="PENDING",
            unsupported_claims=[],
        )

        payable_amount = None

        if claim.claimed_amount is not None:

            total_deductions = sum(
                item["deduction"]
                for item in deductions
            )

            payable_amount = max(
                0,
                claim.claimed_amount
                - total_deductions,
            )

        decision_output = DecisionOutput(
            case_id=claim.case_id,
            decision=decision,
            confidence=confidence,
            key_findings=findings,
            applicable_limits=limits,
            missing_evidence=missing_evidence,
            citations=citations,
            validation=validation,
            payable_amount=payable_amount,
            deductions=deductions,
        )

        elapsed_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        trace = state.get(
            "trace",
            [],
        )

        trace.append(
            {
                "agent": self.name,
                "action": (
                    "Generated structured preliminary "
                    "claim decision from coverage analysis."
                ),
                "retrieval_count": len(evidence),
                "validation_status": "PENDING",
                "elapsed_ms": elapsed_ms,
            }
        )

        state["decision"] = decision_output
        state["trace"] = trace

        return state