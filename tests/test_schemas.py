from datetime import date

from app.schemas.claim import ClaimCase
from app.schemas.decision import (
    Citation,
    DecisionOutput,
    ValidationResult,
)


def test_claim_schema():

    claim = ClaimCase(
        case_id="TEST-001",
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2026, 3, 14),
        diagnosis="Acute appendicitis",
        treatment="Appendectomy",
        is_inpatient=True,
        treatment_duration_hours=96,
        current_sum_insured=500000,
        claimed_amount=100000,
    )

    assert claim.case_id == "TEST-001"
    assert claim.is_inpatient is True


def test_decision_schema():

    output = DecisionOutput(
        case_id="TEST-001",
        decision="ADMISSIBLE",
        confidence=0.90,
        key_findings=[
            "Hospitalization evidence is available."
        ],
        applicable_limits=[],
        missing_evidence=[],
        citations=[
            Citation(
                claim="Test policy claim",
                source="policy.pdf",
                page=8,
                section="Test section",
                chunk_id="policy_p8_chunk_01",
            )
        ],
        validation=ValidationResult(
            status="VALID",
            unsupported_claims=[],
        ),
    )

    assert output.decision == "ADMISSIBLE"
    assert output.confidence == 0.90