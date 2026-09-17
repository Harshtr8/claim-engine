from datetime import date

from app.agents.case_analysis import CaseAnalysisAgent
from app.agents.policy_evidence import PolicyEvidenceAgent
from app.schemas.claim import ClaimCase


def test_policy_evidence():

    claim = ClaimCase(
        case_id="TEST-002",
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

    case_agent = CaseAnalysisAgent()
    state = case_agent.run(state)

    evidence_agent = PolicyEvidenceAgent()
    state = evidence_agent.run(state)

    assert "policy_evidence" in state

    evidence = state["policy_evidence"]

    assert len(evidence) > 0

    for item in evidence:
        assert "chunk_id" in item
        assert "page" in item
        assert "text" in item
        assert "source" in item
        assert "reranker_score" in item

    assert state["trace"][1]["agent"] == "PolicyEvidenceAgent"

    print("\n========== POLICY EVIDENCE ==========\n")

    for i, item in enumerate(evidence, start=1):
        print(f"Result #{i}")
        print("Chunk:", item["chunk_id"])
        print("Page:", item["page"])
        print("Section:", item["section"])
        print("Score:", item["reranker_score"])
        print("Text:", item["text"][:700])
        print("-------------------------------------")