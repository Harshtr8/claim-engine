from __future__ import annotations

from typing import Any

from app.orchestrator.state import ClaimEngineState
from app.schemas.claim import ClaimCase


class CoverageAgent:
    """
    Specialized coverage-analysis agent.

    Responsibilities:
    - Evaluate waiting periods.
    - Evaluate pre-existing disease rules.
    - Evaluate hospitalization/day-care/domiciliary eligibility.
    - Evaluate policy exclusions.
    - Apply policy sub-limits.
    - Validate pre/post-hospitalization expenses when timing
      evidence is explicitly available.
    - Calculate deductions and provisional payable amount.

    The agent does not invent policy rules. It uses the supplied
    policy evidence retrieved earlier in the graph.
    """

    GENERAL_WAITING_DAYS = 30
    PRE_HOSPITALIZATION_MAX_DAYS = 30
    POST_HOSPITALIZATION_MAX_DAYS = 60

    def run(self, state: ClaimEngineState) -> ClaimEngineState:
        claim: ClaimCase = state["claim"]

        findings: list[str] = []
        missing_evidence: list[str] = []
        exclusions: list[str] = []
        waiting_failures: list[str] = []
        deductions: list[dict[str, Any]] = []

        # =========================================================
        # 1. Evidence count
        # =========================================================

        evidence_count = len(
            state.get("policy_evidence", [])
        )

        # =========================================================
        # 2. Applicable policy limits
        # =========================================================

        applicable_limits: list[str] = [
            "Room rent: 1% of Basic Sum Insured per day.",
            "ICU: 2% of Basic Sum Insured per day.",
            "Medical practitioner/consultant/surgeon: 25% of Sum Insured.",
            "Medicines/diagnostics and related expenses: 40% of Sum Insured.",
            "Ambulance: 1% of Basic Sum Insured or ₹1,000, whichever is less.",
        ]

        if claim.domiciliary_treatment is True:
            applicable_limits.append(
                "Domiciliary treatment: 20% of Basic Sum Insured."
            )

        # =========================================================
        # 3. Coverage duration
        # =========================================================

        coverage_days = (
            claim.claim_date - claim.policy_start_date
        ).days

        coverage_months = (
            claim.dataset_continuous_coverage_months
            if claim.dataset_continuous_coverage_months is not None
            else coverage_days / 30.4375
        )

        # =========================================================
        # 4. General waiting period
        # =========================================================

        general_waiting_exception = (
            claim.prior_coverage_years is not None
            and claim.prior_coverage_years >= 1
            and claim.prior_policy_records_received is True
        )

        if (
            coverage_days < self.GENERAL_WAITING_DAYS
            and not general_waiting_exception
        ):
            waiting_failures.append(
                "Claim falls within the initial 30-day waiting period."
            )

        elif coverage_days < self.GENERAL_WAITING_DAYS:
            findings.append(
                "Initial waiting-period exception is supported by "
                "qualifying prior continuous coverage and prior-policy records."
            )

        # =========================================================
        # 5. Pre-existing disease waiting period
        # =========================================================

        if claim.pre_existing_disease is True:
            required_months = 48.0

            qualifying_portability = (
                claim.prior_coverage_years is not None
                and claim.prior_coverage_years > 0
                and claim.prior_policy_records_received is True
                and claim.prior_policy_insurer_type is not None
                and "individual"
                in claim.prior_policy_insurer_type.lower()
                and "health"
                in claim.prior_policy_insurer_type.lower()
            )

            if qualifying_portability:
                prior_months = (
                    claim.prior_coverage_years * 12.0
                )

                if prior_months >= required_months:
                    required_months = 0.0
                else:
                    required_months = max(
                        0.0,
                        required_months - prior_months,
                    )

                findings.append(
                    "Prior qualifying individual health coverage is "
                    "available for portability-based waiting-period assessment."
                )

                if (
                    claim.current_sum_insured is not None
                    and claim.prior_sum_insured is not None
                    and claim.current_sum_insured
                    > claim.prior_sum_insured
                ):
                    findings.append(
                        "Current sum insured exceeds prior sum insured; "
                        "reduced waiting-period treatment applies only "
                        "to the prior sum-insured extent."
                    )

            if coverage_months < required_months:
                waiting_failures.append(
                    "Pre-existing disease waiting period has not been completed."
                )
            else:
                findings.append(
                    "Applicable pre-existing disease waiting period "
                    "has been completed."
                )

        # =========================================================
        # 6. Treatment type
        # =========================================================

        is_domiciliary = (
            claim.domiciliary_treatment is True
        )

        is_day_care = (
            claim.treatment_duration_hours is not None
            and claim.treatment_duration_hours < 24
            and not is_domiciliary
        )

        if is_domiciliary:

            room_unavailable = (
                claim.hospital_room_unavailable is True
            )

            cannot_move = (
                claim.patient_cannot_be_moved is True
            )

            if not room_unavailable and not cannot_move:
                missing_evidence.append(
                    "Domiciliary-treatment eligibility is not supported "
                    "by evidence that hospital accommodation was unavailable "
                    "or the patient could not be moved."
                )
            else:
                findings.append(
                    "Domiciliary-treatment condition is supported by "
                    "the available case evidence."
                )

        elif is_day_care:

            findings.append(
                "Treatment duration is below 24 hours and is evaluated "
                "under the policy's day-care treatment provisions."
            )

        else:

            if claim.is_inpatient is True:

                if claim.treatment_duration_hours is not None:

                    if claim.treatment_duration_hours >= 24:
                        findings.append(
                            "Hospitalization meets the 24-hour minimum "
                            "duration requirement."
                        )
                    else:
                        exclusions.append(
                            "Hospitalization does not meet the 24-hour "
                            "minimum duration requirement."
                        )

                else:
                    missing_evidence.append(
                        "Hospitalization duration is not documented."
                    )

        # =========================================================
        # 7. Hospital / Day-care facility eligibility
        # =========================================================

        if not is_domiciliary:

            if claim.hospital_registered is False:
                exclusions.append(
                    "Hospital/facility is explicitly documented "
                    "as not registered."
                )

            elif claim.hospital_minimum_criteria_documented is False:
                missing_evidence.append(
                    "Hospital/facility minimum eligibility criteria "
                    "are not adequately documented."
                )

            elif claim.evidence_context_present:

                if (
                    claim.hospital_registered is None
                    and claim.hospital_minimum_criteria_documented is None
                ):
                    missing_evidence.append(
                        "Hospital registration and minimum eligibility "
                        "criteria cannot be verified from the supplied evidence."
                    )

        # =========================================================
        # 8. Medical necessity
        # =========================================================

        if claim.medical_necessity_confirmed is False:
            exclusions.append(
                "Medical necessity is explicitly not confirmed."
            )

        elif claim.medical_necessity_confirmed is True:
            findings.append(
                "Medical necessity is confirmed by the supplied evidence."
            )

        # =========================================================
        # 9. Diagnosis / treatment text
        # =========================================================

        diagnosis_text = (
            claim.diagnosis or ""
        ).lower()

        treatment_text = (
            claim.treatment or ""
        ).lower()

        # =========================================================
        # 10. Specified disease waiting period
        # =========================================================

        specified_disease_terms = [
            "cataract",
            "hernia",
            "hydrocele",
            "benign prostatic",
            "piles",
            "fissure",
            "fistula",
            "sinus",
            "joint replacement",
            "arthritis",
            "gout",
        ]

        is_specified_disease = any(
            term in diagnosis_text
            or term in treatment_text
            for term in specified_disease_terms
        )

        if is_specified_disease:

            specified_waiting_exception = (
                claim.prior_coverage_years is not None
                and claim.prior_coverage_years >= 1
                and claim.prior_policy_records_received is True
                and claim.prior_policy_insurer_type is not None
                and "individual"
                in claim.prior_policy_insurer_type.lower()
                and "health"
                in claim.prior_policy_insurer_type.lower()
            )

            if (
                coverage_months < 12
                and not specified_waiting_exception
            ):
                waiting_failures.append(
                    "Specified-disease waiting period has not been completed."
                )

            elif specified_waiting_exception:
                findings.append(
                    "Specified-disease waiting-period exception is "
                    "supported by qualifying prior coverage and records."
                )

        # =========================================================
        # 11. Cosmetic / aesthetic exclusion
        # =========================================================

        cosmetic_terms = [
            "cosmetic",
            "aesthetic",
            "beautification",
            "plastic surgery",
        ]

        cosmetic_case = any(
            term in diagnosis_text
            or term in treatment_text
            for term in cosmetic_terms
        )

        if cosmetic_case:

            injury_or_disease_exception = any(
                term in diagnosis_text
                for term in [
                    "injury",
                    "disease",
                    "accident",
                    "trauma",
                ]
            )

            if not injury_or_disease_exception:
                exclusions.append(
                    "Cosmetic/aesthetic treatment is excluded "
                    "under the policy."
                )
            else:
                findings.append(
                    "Plastic surgery is associated with an injury/disease "
                    "context and is evaluated under the policy exception."
                )

        # =========================================================
        # 12. Experimental / unproven treatment exclusion
        # =========================================================

        if claim.experimental is True:
            exclusions.append(
                "Treatment is explicitly identified as experimental/unproven."
            )

        # =========================================================
        # 13. Domiciliary limit
        # =========================================================

        if (
            is_domiciliary
            and claim.current_sum_insured is not None
        ):

            domiciliary_limit = (
                0.20 * claim.current_sum_insured
            )

            domiciliary_claimed = (
                (claim.doctor_expense or 0.0)
                + (claim.medicine_diagnostic_expense or 0.0)
            )

            if domiciliary_claimed > domiciliary_limit:

                deduction = (
                    domiciliary_claimed
                    - domiciliary_limit
                )

                deductions.append(
                    {
                        "category": "domiciliary_limit",
                        "claimed": domiciliary_claimed,
                        "allowed": domiciliary_limit,
                        "deduction": deduction,
                        "reason": (
                            "Domiciliary-treatment expenses exceed "
                            "the 20% Basic Sum Insured limit."
                        ),
                    }
                )

        # =========================================================
        # 14. Room rent limit
        # =========================================================

        if (
            claim.room_expense is not None
            and claim.current_sum_insured is not None
            and claim.is_inpatient is True
        ):

            room_limit_per_day = (
                0.01 * claim.current_sum_insured
            )

            if (
                claim.hospitalization_start_date is not None
                and claim.hospitalization_end_date is not None
            ):

                hospitalization_days = (
                    claim.hospitalization_end_date
                    - claim.hospitalization_start_date
                ).days

                if hospitalization_days > 0:
                    allowed_room = (
                        room_limit_per_day
                        * hospitalization_days
                    )
                else:
                    allowed_room = room_limit_per_day

            else:
                allowed_room = room_limit_per_day

            if claim.room_expense > allowed_room:

                deduction = (
                    claim.room_expense
                    - allowed_room
                )

                deductions.append(
                    {
                        "category": "room",
                        "claimed": claim.room_expense,
                        "allowed": allowed_room,
                        "deduction": deduction,
                        "reason": (
                            "Room expense exceeds the applicable "
                            "1% Basic Sum Insured per-day limit."
                        ),
                    }
                )

        # =========================================================
        # 15. ICU limit
        # =========================================================

        if (
            claim.icu_expense is not None
            and claim.current_sum_insured is not None
            and claim.icu_expense > 0
        ):

            icu_limit_per_day = (
                0.02 * claim.current_sum_insured
            )

            if (
                claim.hospitalization_start_date is not None
                and claim.hospitalization_end_date is not None
            ):

                hospitalization_days = (
                    claim.hospitalization_end_date
                    - claim.hospitalization_start_date
                ).days

                if hospitalization_days > 0:
                    allowed_icu = (
                        icu_limit_per_day
                        * hospitalization_days
                    )
                else:
                    allowed_icu = icu_limit_per_day

            else:
                allowed_icu = icu_limit_per_day

            if claim.icu_expense > allowed_icu:

                deduction = (
                    claim.icu_expense
                    - allowed_icu
                )

                deductions.append(
                    {
                        "category": "icu",
                        "claimed": claim.icu_expense,
                        "allowed": allowed_icu,
                        "deduction": deduction,
                        "reason": (
                            "ICU expense exceeds the applicable "
                            "2% Basic Sum Insured per-day limit."
                        ),
                    }
                )

        # =========================================================
        # 16. Doctor / consultant / surgeon limit
        # =========================================================

        if (
            claim.doctor_expense is not None
            and claim.current_sum_insured is not None
        ):

            doctor_limit = (
                0.25 * claim.current_sum_insured
            )

            if claim.doctor_expense > doctor_limit:

                deduction = (
                    claim.doctor_expense
                    - doctor_limit
                )

                deductions.append(
                    {
                        "category": "doctor",
                        "claimed": claim.doctor_expense,
                        "allowed": doctor_limit,
                        "deduction": deduction,
                        "reason": (
                            "Medical practitioner/consultant/surgeon "
                            "expense exceeds the applicable 25% "
                            "Sum Insured limit."
                        ),
                    }
                )

        # =========================================================
        # 17. Medicines / diagnostics limit
        # =========================================================

        if (
            claim.medicine_diagnostic_expense is not None
            and claim.current_sum_insured is not None
        ):

            medicine_limit = (
                0.40 * claim.current_sum_insured
            )

            if (
                claim.medicine_diagnostic_expense
                > medicine_limit
            ):

                deduction = (
                    claim.medicine_diagnostic_expense
                    - medicine_limit
                )

                deductions.append(
                    {
                        "category": "medicines_diagnostics",
                        "claimed": claim.medicine_diagnostic_expense,
                        "allowed": medicine_limit,
                        "deduction": deduction,
                        "reason": (
                            "Medicines/diagnostics and related expenses "
                            "exceed the applicable 40% Sum Insured limit."
                        ),
                    }
                )

        # =========================================================
        # 18. Ambulance limit
        # =========================================================

        if (
            claim.ambulance_expense is not None
            and claim.current_sum_insured is not None
        ):

            ambulance_limit = min(
                0.01 * claim.current_sum_insured,
                1000.0,
            )

            if claim.ambulance_expense > ambulance_limit:

                deduction = (
                    claim.ambulance_expense
                    - ambulance_limit
                )

                deductions.append(
                    {
                        "category": "ambulance",
                        "claimed": claim.ambulance_expense,
                        "allowed": ambulance_limit,
                        "deduction": deduction,
                        "reason": (
                            "Ambulance expense exceeds the policy limit "
                            "of 1% Basic Sum Insured or ₹1,000, "
                            "whichever is less."
                        ),
                    }
                )

        # =========================================================
        # 19. Pre-hospitalization expenses
        #
        # Timing is validated only when explicit timing evidence
        # is present in the supplied case.
        # =========================================================

        if (
            claim.pre_hospitalization_expense is not None
            and claim.pre_hospitalization_expense > 0
            and claim.expense_timing_present
        ):

            if claim.pre_hospitalization_days_before is None:

                missing_evidence.append(
                    "Pre-hospitalization expense timing is not documented."
                )

            elif (
                claim.pre_hospitalization_days_before
                > self.PRE_HOSPITALIZATION_MAX_DAYS
            ):

                deductions.append(
                    {
                        "category": "pre_hospitalization",
                        "claimed": claim.pre_hospitalization_expense,
                        "allowed": 0.0,
                        "deduction": claim.pre_hospitalization_expense,
                        "reason": (
                            "Pre-hospitalization expense falls outside "
                            "the permitted 30-day window."
                        ),
                    }
                )

            else:

                findings.append(
                    "Pre-hospitalization expense falls within "
                    "the permitted 30-day window."
                )

        # =========================================================
        # 20. Post-hospitalization expenses
        # =========================================================

        if (
            claim.post_hospitalization_expense is not None
            and claim.post_hospitalization_expense > 0
            and claim.expense_timing_present
        ):

            if claim.post_hospitalization_days_after_discharge is None:

                missing_evidence.append(
                    "Post-hospitalization expense timing is not documented."
                )

            elif (
                claim.post_hospitalization_days_after_discharge
                > self.POST_HOSPITALIZATION_MAX_DAYS
            ):

                deductions.append(
                    {
                        "category": "post_hospitalization",
                        "claimed": claim.post_hospitalization_expense,
                        "allowed": 0.0,
                        "deduction": claim.post_hospitalization_expense,
                        "reason": (
                            "Post-hospitalization expense falls outside "
                            "the permitted 60-day window."
                        ),
                    }
                )

            elif claim.same_condition_confirmed is False:

                deductions.append(
                    {
                        "category": "post_hospitalization",
                        "claimed": claim.post_hospitalization_expense,
                        "allowed": 0.0,
                        "deduction": claim.post_hospitalization_expense,
                        "reason": (
                            "Post-hospitalization expense is not confirmed "
                            "to relate to the same condition."
                        ),
                    }
                )

            elif claim.same_condition_confirmed is None:

                missing_evidence.append(
                    "Same-condition confirmation is missing for "
                    "post-hospitalization expenses."
                )

            else:

                findings.append(
                    "Post-hospitalization expense falls within "
                    "the permitted 60-day window and is confirmed "
                    "for the same condition."
                )

        # =========================================================
        # 21. Claimed amount
        # =========================================================

        claimed_amount = claim.claimed_amount

        if claimed_amount is None:

            claimed_amount = sum(
                value or 0.0
                for value in [
                    claim.room_expense,
                    claim.icu_expense,
                    claim.doctor_expense,
                    claim.medicine_diagnostic_expense,
                    claim.pre_hospitalization_expense,
                    claim.post_hospitalization_expense,
                    claim.ambulance_expense,
                ]
            )

        # =========================================================
        # 22. Total deductions
        # =========================================================

        total_deductions = sum(
            float(item.get("deduction", 0.0))
            for item in deductions
        )

        provisional_payable = max(
            0.0,
            claimed_amount - total_deductions,
        )

        # =========================================================
        # 23. Structured coverage analysis
        # =========================================================

        coverage_analysis = {
            "coverage_days": coverage_days,
            "coverage_months": coverage_months,

            "general_waiting_exception": (
                general_waiting_exception
            ),

            "is_domiciliary": is_domiciliary,
            "is_day_care": is_day_care,
            "is_specified_disease": is_specified_disease,
            "cosmetic_case": cosmetic_case,

            "exclusions": exclusions,
            "waiting_failures": waiting_failures,

            "findings": findings,
            "missing_evidence": missing_evidence,

            "applicable_limits": applicable_limits,

            "deductions": deductions,

            "claimed_amount": claimed_amount,
            "total_deductions": total_deductions,
            "provisional_payable": provisional_payable,

            "evidence_count": evidence_count,

            "evidence_context_present": (
                claim.evidence_context_present
            ),

            "expense_timing_present": (
                claim.expense_timing_present
            ),

            "prior_policy_present": (
                claim.prior_policy_present
            ),
        }

        # =========================================================
        # 24. Trace
        # =========================================================

        trace = list(
            state.get("trace", [])
        )

        trace.append(
            {
                "agent": "CoverageAgent",
                "action": (
                    "Evaluated waiting periods, exclusions, "
                    "facility eligibility, policy limits, "
                    "and expense admissibility."
                ),
                "retrieval_count": evidence_count,
            }
        )

        # =========================================================
        # 25. Update state
        # =========================================================

        state["coverage_analysis"] = coverage_analysis
        state["trace"] = trace

        return state