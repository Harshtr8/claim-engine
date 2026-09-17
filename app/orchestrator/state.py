from typing import Any, TypedDict

from app.schemas.claim import ClaimCase
from app.schemas.decision import DecisionOutput


class ClaimEngineState(TypedDict, total=False):
    # Input
    claim: ClaimCase

    # Case analysis
    case_analysis: dict[str, Any]

    # Retrieved policy evidence
    policy_evidence: list[dict[str, Any]]

    # Coverage analysis
    coverage_analysis: dict[str, Any]

    # Decision
    decision: DecisionOutput

    # Validation
    validation: dict[str, Any]

    # Execution trace
    trace: list[dict[str, Any]]