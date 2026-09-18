from typing import Optional


def calculate_percentage_limit(
    sum_insured: Optional[float],
    percentage: float,
) -> Optional[float]:
    if sum_insured is None:
        return None

    return sum_insured * percentage


def calculate_room_limit(
    basic_sum_insured: Optional[float],
) -> Optional[float]:
    return calculate_percentage_limit(
        basic_sum_insured,
        0.01,
    )


def calculate_icu_limit(
    basic_sum_insured: Optional[float],
) -> Optional[float]:
    return calculate_percentage_limit(
        basic_sum_insured,
        0.02,
    )


def calculate_doctor_limit(
    sum_insured: Optional[float],
) -> Optional[float]:
    return calculate_percentage_limit(
        sum_insured,
        0.25,
    )


def calculate_medicine_diagnostic_limit(
    sum_insured: Optional[float],
) -> Optional[float]:
    return calculate_percentage_limit(
        sum_insured,
        0.40,
    )


def calculate_domiciliary_limit(
    basic_sum_insured: Optional[float],
) -> Optional[float]:
    return calculate_percentage_limit(
        basic_sum_insured,
        0.20,
    )


def calculate_ambulance_limit(
    basic_sum_insured: Optional[float],
) -> Optional[float]:
    if basic_sum_insured is None:
        return None

    return min(
        basic_sum_insured * 0.01,
        1000,
    )


def calculate_pre_existing_waiting_months(
    prior_coverage_years: float = 0,
) -> float:
    """
    Policy:
    Pre-existing diseases are excluded until 48 months
    of continuous coverage have elapsed.

    Portability reduces the waiting period by the
    completed preceding years of qualifying coverage.
    """
    base_waiting_months = 48.0

    reduction_months = max(
        0.0,
        prior_coverage_years * 12.0,
    )

    return max(
        0.0,
        base_waiting_months - reduction_months,
    )


def calculate_pre_existing_waiting_by_sum_insured(
    prior_coverage_years: float,
    previous_sum_insured: Optional[float],
    current_sum_insured: Optional[float],
) -> dict:
    waiting_months = calculate_pre_existing_waiting_months(
        prior_coverage_years
    )

    increased_sum_insured = (
        previous_sum_insured is not None
        and current_sum_insured is not None
        and current_sum_insured > previous_sum_insured
    )

    return {
        "waiting_months": waiting_months,
        "reduced_waiting_applies_to_previous_si": increased_sum_insured,
        "previous_sum_insured": previous_sum_insured,
        "current_sum_insured": current_sum_insured,
    }


def is_general_waiting_period_complete(
    coverage_days: Optional[int],
) -> Optional[bool]:
    """
    Policy general waiting period = 30 days.
    """
    if coverage_days is None:
        return None

    return coverage_days >= 30


def is_specified_disease_waiting_complete(
    coverage_months: Optional[float],
    prior_coverage_years: float = 0,
    prior_records_received: bool = False,
) -> Optional[bool]:
    """
    Specified diseases have a 1-year waiting period.

    The policy states that this waiting period does not
    apply when the insured had at least one completed
    continuous year under the qualifying prior coverage,
    subject to receipt of database/claim history.
    """
    if coverage_months is None:
        return None

    if (
        prior_coverage_years >= 1
        and prior_records_received
    ):
        return True

    return coverage_months >= 12


def is_pre_existing_waiting_complete(
    coverage_months: Optional[float],
    waiting_months: float,
) -> Optional[bool]:
    if coverage_months is None:
        return None

    return coverage_months >= waiting_months


def is_valid_pre_hospitalization_window(
    days_before: Optional[float],
) -> Optional[bool]:
    if days_before is None:
        return None

    return 0 <= days_before <= 30


def is_valid_post_hospitalization_window(
    days_after: Optional[float],
) -> Optional[bool]:
    if days_after is None:
        return None

    return 0 <= days_after <= 60


def is_day_care_candidate(
    treatment_type: Optional[str],
    admission_hours: Optional[float],
) -> bool:
    if treatment_type:
        normalized = treatment_type.lower().strip()

        if normalized == "day_care":
            return True

    if admission_hours is not None and admission_hours < 24:
        return True

    return False


def is_inpatient_candidate(
    treatment_type: Optional[str],
    admission_hours: Optional[float],
) -> bool:
    if treatment_type:
        normalized = treatment_type.lower().strip()

        if normalized == "inpatient":
            return True

    if admission_hours is not None and admission_hours >= 24:
        return True

    return False


def calculate_deduction(
    claimed_amount: Optional[float],
    applicable_limit: Optional[float],
) -> Optional[float]:
    if claimed_amount is None:
        return None

    if applicable_limit is None:
        return None

    if claimed_amount <= applicable_limit:
        return 0.0

    return claimed_amount - applicable_limit