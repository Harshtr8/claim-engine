from datetime import date

from app.agents.case_analysis import CaseAnalysisAgent
from app.agents.policy_evidence import PolicyEvidenceAgent
from app.agents.coverage import CoverageAgent
from app.agents.decision import DecisionAgent
from app.agents.validation import ValidationAgent
from app.schemas.claim import ClaimCase


def test_validation_agent():

    claim = ClaimCase(
        case_id="TEST-005",
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
    )

    state = {
        "claim": claim,
        "trace": [],
    }

    state = CaseAnalysisAgent().run(state)

    state = PolicyEvidenceAgent().run(state)

    state = CoverageAgent().run(state)

    state = DecisionAgent().run(state)

    state = ValidationAgent().run(state)

    assert "validation" in state

    assert state["validation"]["status"] in {
        "VALID",
        "VALID_ABSTENTION",
        "INVALID",
    }

    assert state["decision"].validation.status in {
        "VALID",
        "VALID_ABSTENTION",
        "INVALID",
    }

    assert state["trace"][-1]["agent"] == (
        "ValidationAgent"
    )