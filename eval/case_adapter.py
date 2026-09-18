from __future__ import annotations

from typing import Any

from app.schemas.claim import ClaimCase


def adapt_public_case(raw: dict[str, Any]) -> ClaimCase:
    """
    Convert one supplied public_test_cases.json object into the
    internal flat ClaimCase schema.

    The original public case is never modified.
    """

    hospital = raw.get("hospital") or {}
    treatment = raw.get("treatment") or {}
    expenses = raw.get("expenses_inr") or {}
    evidence = raw.get("evidence_context") or {}
    timing = raw.get("expense_timing") or {}
    prior_policy = raw.get("prior_policy") or {}

    # Preserve whether these objects were actually supplied.
    evidence_context_present = "evidence_context" in raw
    expense_timing_present = "expense_timing" in raw
    prior_policy_present = "prior_policy" in raw

    documents = raw.get("documents") or []

    treatment_type = str(
        treatment.get("type") or ""
    ).strip().lower()

    # =========================================================
    # Prior coverage / portability
    # =========================================================

    prior_coverage_years = prior_policy.get(
        "continuous_years",
        raw.get("prior_insurer_continuous_years"),
    )

    prior_records_received = prior_policy.get(
        "database_and_claim_history_received"
    )

    previous_sum_insured = prior_policy.get(
        "previous_sum_insured_inr"
    )

    prior_insurer_type = prior_policy.get(
        "insurer_type"
    )

    # =========================================================
    # Expense timing
    # =========================================================

    pre_days = timing.get(
        "pre_hospitalization_days_before_admission"
    )

    post_days = timing.get(
        "post_hospitalization_days_after_discharge"
    )

    same_condition = timing.get(
        "same_condition_confirmed"
    )

    # =========================================================
    # Treatment classification
    # =========================================================

    is_inpatient = treatment_type == "inpatient"

    domiciliary = treatment_type == "domiciliary"

    # =========================================================
    # Claimed amount
    #
    # The public dataset gives component expenses rather than a
    # separate claimed_amount field, so calculate the aggregate.
    # =========================================================

    expense_keys = (
        "room",
        "icu",
        "doctor_fees",
        "medicines_diagnostics",
        "pre_hospitalization",
        "post_hospitalization",
        "ambulance",
    )

    claimed_amount = sum(
        float(expenses.get(key) or 0)
        for key in expense_keys
    )

    # =========================================================
    # Build internal ClaimCase
    # =========================================================

    return ClaimCase(
        case_id=raw["case_id"],

        policy_start_date=raw["policy_start_date"],

        claim_date=raw["claim_date"],

        diagnosis=treatment.get("diagnosis"),

        treatment=(
            treatment_type
            or treatment.get("procedure")
        ),

        domiciliary_treatment=domiciliary,

        experimental=treatment.get("experimental"),

        # -----------------------------------------------------
        # Hospital
        # -----------------------------------------------------

        hospital_name=hospital.get("name"),

        hospital_registration=None,

        hospital_registered=evidence.get(
            "hospital_registered"
        ),

        hospital_minimum_criteria_documented=evidence.get(
            "hospital_minimum_criteria_documented"
        ),

        is_inpatient=is_inpatient,

        treatment_duration_hours=treatment.get(
            "admission_hours"
        ),

        hospital_room_unavailable=treatment.get(
            "hospital_room_unavailable"
        ),

        patient_cannot_be_moved=treatment.get(
            "patient_cannot_be_moved"
        ),

        medical_necessity_confirmed=evidence.get(
            "medical_necessity_confirmed"
        ),

        # -----------------------------------------------------
        # Pre-existing disease
        # -----------------------------------------------------

        pre_existing_disease=treatment.get(
            "pre_existing"
        ),

        pre_existing_details=(
            treatment.get("diagnosis")
            if treatment.get("pre_existing") is True
            else None
        ),

        # -----------------------------------------------------
        # Prior policy / portability
        # -----------------------------------------------------

        prior_insurer=None,

        prior_policy_insurer_type=prior_insurer_type,

        prior_coverage_years=prior_coverage_years,

        prior_policy_records_received=prior_records_received,

        prior_sum_insured=previous_sum_insured,

        current_sum_insured=raw.get(
            "sum_insured_inr"
        ),

        # -----------------------------------------------------
        # Expenses
        # -----------------------------------------------------

        claimed_amount=claimed_amount,

        room_expense=expenses.get("room"),

        icu_expense=expenses.get("icu"),

        doctor_expense=expenses.get(
            "doctor_fees"
        ),

        medicine_diagnostic_expense=expenses.get(
            "medicines_diagnostics"
        ),

        pre_hospitalization_expense=expenses.get(
            "pre_hospitalization"
        ),

        post_hospitalization_expense=expenses.get(
            "post_hospitalization"
        ),

        ambulance_expense=expenses.get(
            "ambulance"
        ),

        # -----------------------------------------------------
        # Pre / Post hospitalization
        # -----------------------------------------------------

        pre_hospitalization_days_before=pre_days,

        post_hospitalization_days_after_discharge=post_days,

        same_condition_confirmed=same_condition,

        # -----------------------------------------------------
        # Evidence metadata
        # -----------------------------------------------------

        documents=documents,

        evidence_context_present=evidence_context_present,

        expense_timing_present=expense_timing_present,

        prior_policy_present=prior_policy_present,

        dataset_continuous_coverage_months=raw.get(
            "continuous_coverage_months"
        ),

        # -----------------------------------------------------
        # Additional source information
        # -----------------------------------------------------

        additional_information=_build_additional_information(
            raw
        ),
    )


def _build_additional_information(
    raw: dict[str, Any],
) -> str:
    """
    Preserve useful source-case metadata that is not represented
    by dedicated ClaimCase fields.
    """

    documents = raw.get("documents") or []

    task = raw.get("task") or ""

    hospital = raw.get("hospital") or {}

    parts: list[str] = []

    if documents:
        parts.append(
            "Documents supplied: "
            + ", ".join(
                str(x)
                for x in documents
            )
        )

    if hospital.get("network_provider") is not None:
        parts.append(
            "Network provider: "
            + str(
                hospital["network_provider"]
            )
        )

    if raw.get("continuous_coverage_months") is not None:
        parts.append(
            "Dataset continuous coverage months: "
            + str(
                raw["continuous_coverage_months"]
            )
        )

    if task:
        parts.append(
            "Evaluation task: "
            + str(task)
        )

    return " | ".join(parts)