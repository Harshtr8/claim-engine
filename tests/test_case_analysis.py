from datetime import date

from app.agents.case_analysis import CaseAnalysisAgent
from app.schemas.claim import ClaimCase


def test_case_analysis():

    claim = ClaimCase(
        case_id="TEST-001",
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2026, 3, 14),
        diagnosis="Acute appendicitis",
        treatment="Appendectomy",
        hospital_name="Test Hospital",
        is_inpatient=True,
        treatment_duration_hours=96,
        current_sum_insured=500000,
        claimed_amount=100000,
    )

    state = {
        "claim": claim,
        "trace": [],
    }

    agent = CaseAnalysisAgent()

    result = agent.run(state)

    assert "case_analysis" in result

    analysis = result["case_analysis"]

    assert analysis["case_id"] == "TEST-001"

    assert analysis["coverage_days"] == 437

    assert analysis["diagnosis"] == "Acute appendicitis"

    assert result["trace"][0]["agent"] == (
        "CaseAnalysisAgent"
    )