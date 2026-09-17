from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class ClaimCase(BaseModel):
    case_id: str = Field(..., description="Unique claim case ID")

    policy_start_date: date
    claim_date: date

    hospitalization_start_date: Optional[date] = None
    hospitalization_end_date: Optional[date] = None

    diagnosis: Optional[str] = None
    treatment: Optional[str] = None

    hospital_name: Optional[str] = None
    hospital_registration: Optional[str] = None

    is_inpatient: Optional[bool] = None
    treatment_duration_hours: Optional[float] = None

    pre_existing_disease: Optional[bool] = None
    pre_existing_details: Optional[str] = None

    prior_insurer: Optional[str] = None
    prior_coverage_years: Optional[float] = None
    prior_sum_insured: Optional[float] = None

    current_sum_insured: Optional[float] = None

    claimed_amount: Optional[float] = None

    room_expense: Optional[float] = None
    doctor_expense: Optional[float] = None
    medicine_diagnostic_expense: Optional[float] = None

    pre_hospitalization_expense: Optional[float] = None
    post_hospitalization_expense: Optional[float] = None
    ambulance_expense: Optional[float] = None

    additional_information: Optional[str] = None