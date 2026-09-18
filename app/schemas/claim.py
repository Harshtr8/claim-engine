from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ClaimCase(BaseModel):
    """
    Normalized internal representation of an insurance claim case.

    The schema intentionally keeps claim facts separate from policy
    evidence and reasoning so that downstream agents can operate
    deterministically on structured data.
    """

    # =========================================================
    # Case / Policy Dates
    # =========================================================

    case_id: str

    policy_start_date: date

    claim_date: date

    hospitalization_start_date: Optional[date] = None

    hospitalization_end_date: Optional[date] = None

    # =========================================================
    # Diagnosis / Treatment
    # =========================================================

    diagnosis: Optional[str] = None

    treatment: Optional[str] = None

    domiciliary_treatment: Optional[bool] = None

    experimental: Optional[bool] = None

    # =========================================================
    # Hospital Information
    # =========================================================

    hospital_name: Optional[str] = None

    hospital_registration: Optional[str] = None

    hospital_registered: Optional[bool] = None

    hospital_minimum_criteria_documented: Optional[bool] = None

    is_inpatient: Optional[bool] = None

    treatment_duration_hours: Optional[float] = Field(
        default=None,
        ge=0,
    )

    hospital_room_unavailable: Optional[bool] = None

    patient_cannot_be_moved: Optional[bool] = None

    medical_necessity_confirmed: Optional[bool] = None

    # =========================================================
    # Medical / Waiting Period Information
    # =========================================================

    pre_existing_disease: Optional[bool] = None

    pre_existing_details: Optional[str] = None

    # =========================================================
    # Prior Policy / Portability
    # =========================================================

    prior_insurer: Optional[str] = None

    prior_policy_insurer_type: Optional[str] = None

    prior_coverage_years: Optional[float] = Field(
        default=None,
        ge=0,
    )

    prior_policy_records_received: Optional[bool] = None

    prior_sum_insured: Optional[float] = Field(
        default=None,
        ge=0,
    )

    current_sum_insured: Optional[float] = Field(
        default=None,
        ge=0,
    )

    # =========================================================
    # Claim / Expense Information
    # =========================================================

    claimed_amount: Optional[float] = Field(
        default=None,
        ge=0,
    )

    room_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    icu_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    doctor_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    medicine_diagnostic_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    pre_hospitalization_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    post_hospitalization_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    ambulance_expense: Optional[float] = Field(
        default=None,
        ge=0,
    )

    # =========================================================
    # Pre / Post Hospitalization Evidence
    # =========================================================

    pre_hospitalization_days_before: Optional[float] = Field(
        default=None,
        ge=0,
    )

    post_hospitalization_days_after_discharge: Optional[float] = Field(
        default=None,
        ge=0,
    )

    same_condition_confirmed: Optional[bool] = None

    # =========================================================
    # Evidence Metadata
    # =========================================================

    documents: list[str] = Field(
        default_factory=list,
    )

    evidence_context_present: bool = False

    expense_timing_present: bool = False

    prior_policy_present: bool = False

    dataset_continuous_coverage_months: Optional[float] = Field(
        default=None,
        ge=0,
    )

    # =========================================================
    # Additional Source Information
    # =========================================================

    additional_information: Optional[str] = None