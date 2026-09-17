from typing import Any, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    claim: str
    source: str
    page: int
    section: str
    chunk_id: str


class ValidationResult(BaseModel):
    status: str
    unsupported_claims: list[str] = Field(default_factory=list)


class TraceStep(BaseModel):
    agent: str
    action: str
    retrieval_count: Optional[int] = None
    validation_status: Optional[str] = None
    elapsed_ms: Optional[float] = None


class DecisionOutput(BaseModel):
    case_id: str

    decision: str

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    key_findings: list[str] = Field(
        default_factory=list
    )

    applicable_limits: list[str] = Field(
        default_factory=list
    )

    missing_evidence: list[str] = Field(
        default_factory=list
    )

    citations: list[Citation] = Field(
        default_factory=list
    )

    validation: ValidationResult

    trace: list[TraceStep] = Field(
        default_factory=list
    )

    payable_amount: Optional[float] = None

    deductions: list[dict[str, Any]] = Field(
        default_factory=list
    )