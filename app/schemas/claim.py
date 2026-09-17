from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ClaimCase(BaseModel):
    case_id: str = Field(...)

    policy_start_date: date = Field(...)
    claim_date: date = Field(...)

    hospitalization_start_date: Optional[date] = None
    hospitalization_end_date: Optional[date] = None

    diagnosis: Optional[str] = None
    treatment: Optional[str] = None
    domiciliary_treatment: Optional[bool] = None

    hospital_name: Optional[str] = None
    hospital_registration: Optional[str] = None

    is_inpatient: Optional[bool] = None
    treatment_duration_hours: Optional[float] = Field(
        default=None,
        ge=0
    )

    pre_existing_disease: Optional[bool] = None
    pre_existing_details: Optional[str] = None

    prior_insurer: Optional[str] = None
    prior_coverage_years: Optional[float] = Field(
        default=None,
        ge=0
    )
    prior_sum_insured: Optional[float] = Field(
        default=None,
        ge=0
    )
    current_sum_insured: Optional[float] = Field(
        default=None,
        ge=0
    )

    claimed_amount: Optional[float] = Field(
        default=None,
        ge=0
    )

    room_expense: Optional[float] = Field(
        default=None,
        ge=0
    )
    doctor_expense: Optional[float] = Field(
        default=None,
        ge=0
    )
    medicine_diagnostic_expense: Optional[float] = Field(
        default=None,
        ge=0
    )

    pre_hospitalization_expense: Optional[float] = Field(
        default=None,
        ge=0
    )
    post_hospitalization_expense: Optional[float] = Field(
        default=None,
        ge=0
    )
    ambulance_expense: Optional[float] = Field(
        default=None,
        ge=0
    )

    additional_information: Optional[str] = None