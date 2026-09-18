from datetime import date

from app.orchestrator.graph import ClaimEngine
from app.schemas.claim import ClaimCase


def test_end_to_end():

    claim = ClaimCase(
        case_id="E2E-001",
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2026, 3, 14),
        diagnosis="Acute appendicitis",
        treatment="Appendectomy",
        hospital_name="Test Hospital",
        hospital_registration="REG-123",
        is_inpatient=True,
        treatment_duration_hours=96,
        current_sum_insured=500000,
        claimed_amount=100000,
        room_expense=30000,
        doctor_expense=30000,
        medicine_diagnostic_expense=90000,
        pre_hospitalization_expense=5000,
        post_hospitalization_expense=7000,
        ambulance_expense=1200,
    )

    engine = ClaimEngine()

    result = engine.analyze(claim)

    assert "decision" in result

    decision = result["decision"]

    assert decision.case_id == "E2E-001"

    assert decision.decision in {
        "ADMISSIBLE",
        "ADMISSIBLE_WITH_LIMITS",
        "PARTIALLY_ADMISSIBLE",
        "NOT_ADMISSIBLE",
        "NEEDS_REVIEW",
    }

    assert 0 <= decision.confidence <= 1

    assert len(decision.citations) > 0

    assert len(result["trace"]) == 5

    assert result["trace"][0]["agent"] == (
        "CaseAnalysisAgent"
    )

    assert result["trace"][1]["agent"] == (
        "PolicyEvidenceAgent"
    )

    assert result["trace"][2]["agent"] == (
        "CoverageAgent"
    )

    assert result["trace"][3]["agent"] == (
        "DecisionAgent"
    )

    assert result["trace"][4]["agent"] == (
        "ValidationAgent"
    )