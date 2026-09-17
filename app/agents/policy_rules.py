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