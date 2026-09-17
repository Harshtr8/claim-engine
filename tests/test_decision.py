from datetime import date

from app.agents.case_analysis import CaseAnalysisAgent
from app.agents.policy_evidence import PolicyEvidenceAgent
from app.agents.coverage import CoverageAgent
from app.agents.decision import DecisionAgent
from app.schemas.claim import ClaimCase


def test_decision_agent():

    claim = ClaimCase(
        case_id="TEST-004",
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
        ambulance_expense=1200,
    )

    state = {
        "claim": claim,
        "trace": [],
    }

    state = CaseAnalysisAgent().run(state)

    state = PolicyEvidenceAgent().run(state)

    state = CoverageAgent().run(state)

    state = DecisionAgent().run(state)

    assert "decision" in state

    decision = state["decision"]

    assert decision.case_id == "TEST-004"

    assert decision.decision in {
        "ADMISSIBLE",
        "ADMISSIBLE_WITH_LIMITS",
        "PARTIALLY_ADMISSIBLE",
        "NOT_ADMISSIBLE",
        "NEEDS_REVIEW",
    }

    assert 0 <= decision.confidence <= 1

    assert len(decision.citations) > 0

    assert state["trace"][-1]["agent"] == (
        "DecisionAgent"
    )