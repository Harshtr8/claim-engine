from datetime import date

from app.agents.case_analysis import CaseAnalysisAgent
from app.agents.policy_evidence import PolicyEvidenceAgent
from app.agents.coverage import CoverageAgent
from app.schemas.claim import ClaimCase


def test_coverage_agent():

    claim = ClaimCase(
        case_id="TEST-003",
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2026, 3, 14),
        diagnosis="Acute appendicitis",
        treatment="Appendectomy",
        hospital_name="Test Hospital",
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

    state = {
        "claim": claim,
        "trace": [],
    }

    state = CaseAnalysisAgent().run(state)

    state = PolicyEvidenceAgent().run(state)

    state = CoverageAgent().run(state)

    assert "coverage_analysis" in state

    analysis = state["coverage_analysis"]

    assert analysis["coverage_days"] == 437

    assert analysis["evidence_count"] > 0

    assert len(analysis["findings"]) > 0

    assert len(analysis["applicable_limits"]) > 0

    assert state["trace"][2]["agent"] == "CoverageAgent"