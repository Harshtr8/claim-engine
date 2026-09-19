from __future__ import annotations

from datetime import date
from typing import Any

from app.schemas.claim import ClaimCase


class CoverageAgent:
    """
    Evaluates structured claim facts against retrieved policy evidence.

    Important evidence semantics:
        True  = evidence confirms the condition
        False = evidence explicitly indicates failure
        None  = evidence is missing / not documented

    None must never be silently converted into False.
    """

    def __init__(self) -> None:
        pass

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _hospitalization_days(claim: ClaimCase) -> float:
        if claim.treatment_duration_hours is not None:
            if claim.treatment_duration_hours > 0:
                return max(
                    1.0,
                    claim.treatment_duration_hours / 24.0,
                )

        if (
            claim.hospitalization_start_date
            and claim.hospitalization_end_date
        ):
            delta = (
                claim.hospitalization_end_date
                - claim.hospitalization_start_date
            ).days

            return max(1.0, float(delta))

        return 1.0

    @staticmethod
    def _months_between(
        start: date,
        end: date,
    ) -> float:
        return max(
            0.0,
            (
                end.year - start.year
            ) * 12
            + (
                end.month - start.month
            )
            + (
                end.day - start.day
            ) / 30.44,
        )

    @staticmethod
    def _is_missing(value: Any) -> bool:
        return value is None

    # =========================================================
    # MAIN ANALYSIS
    # =========================================================

    def analyze(
        self,
        claim: ClaimCase,
        policy_evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:

        policy_evidence = policy_evidence or []

        findings: list[str] = []
        missing_evidence: list[str] = []
        waiting_failures: list[str] = []
        exclusions: list[str] = []
        deductions: list[dict[str, Any]] = []
        applicable_limits: list[str] = []

        coverage_days = self._hospitalization_days(claim)

        coverage_months = self._months_between(
            claim.policy_start_date,
            claim.claim_date,
        )

        # =====================================================
        # GENERAL WAITING PERIOD
        # =====================================================

        general_waiting_satisfied = coverage_days >= 30

        if coverage_months * 30.44 < 30:

            prior_exception = (
                claim.prior_policy_present
                and claim.prior_coverage_years is not None
                and claim.prior_coverage_years >= 1
                and claim.prior_policy_records_received is True
            )

            if not prior_exception:

                waiting_failures.append(
                    "General 30-day waiting period has not been completed."
                )

        else:

            findings.append(
                "Claim occurs after the general 30-day waiting period."
            )

        # =====================================================
        # PRE-EXISTING DISEASE
        # =====================================================

        if claim.pre_existing_disease is True:

            prior_coverage_years = (
                claim.prior_coverage_years or 0
            )

            continuous_months = (
                claim.dataset_continuous_coverage_months
                or 0
            )

            qualifying_prior_months = max(
                prior_coverage_years * 12,
                continuous_months,
            )

            effective_waiting_months = max(
                0.0,
                48.0 - qualifying_prior_months,
            )

            if coverage_months < effective_waiting_months:

                waiting_failures.append(
                    "Pre-existing disease remains within "
                    "the applicable waiting period."
                )

            else:

                findings.append(
                    "Pre-existing disease waiting period "
                    "has been satisfied."
                )

        # =====================================================
        # SPECIFIED DISEASE / TREATMENT WAITING
        # =====================================================

        diagnosis_text = (
            claim.diagnosis or ""
        ).lower()

        specified_keywords = [
            "cataract",
            "hernia",
            "gallbladder",
            "gall bladder",
            "joint replacement",
            "hysterectomy",
            "sinus",
            "piles",
            "fissure",
            "fistula",
            "prostate",
        ]

        is_specified_disease = any(
            keyword in diagnosis_text
            for keyword in specified_keywords
        )

        if is_specified_disease:

            prior_exception = (
                claim.prior_policy_present
                and (
                    claim.prior_coverage_years or 0
                ) >= 1
                and claim.prior_policy_records_received is True
            )

            if (
                coverage_months < 12
                and not prior_exception
            ):

                waiting_failures.append(
                    "Specified disease remains within "
                    "the applicable one-year waiting period."
                )

        # =====================================================
        # HOSPITALIZATION DURATION
        # =====================================================

        if claim.is_inpatient is True:

            if claim.treatment_duration_hours is None:

                missing_evidence.append(
                    "Hospitalization duration is not documented."
                )

            elif claim.treatment_duration_hours < 24:

                exclusions.append(
                    "Hospitalization does not meet the "
                    "24-hour minimum requirement."
                )

            else:

                findings.append(
                    "Hospitalization meets the "
                    "24-hour minimum duration requirement."
                )

        # =====================================================
        # CRITICAL EVIDENCE CHECK
        # =====================================================
        #
        # This is the fix for CUS-004.
        #
        # None = missing evidence.
        # False = explicitly failed.
        #
        # We DO NOT turn None into False.
        # =====================================================

        if claim.is_inpatient is True:

            if claim.hospital_registered is None:

                missing_evidence.append(
                    "Hospital registration status is not documented."
                )

            elif claim.hospital_registered is False:

                exclusions.append(
                    "Hospital registration requirement "
                    "is not satisfied."
                )

            if (
                claim.hospital_minimum_criteria_documented
                is None
            ):

                missing_evidence.append(
                    "Hospital minimum eligibility criteria "
                    "are not documented."
                )

            elif (
                claim.hospital_minimum_criteria_documented
                is False
            ):

                exclusions.append(
                    "Hospital minimum eligibility criteria "
                    "are not satisfied."
                )

            if claim.medical_necessity_confirmed is None:

                missing_evidence.append(
                    "Medical necessity is not documented."
                )

            elif claim.medical_necessity_confirmed is False:

                exclusions.append(
                    "Medical necessity for the treatment "
                    "has not been established."
                )

        # =====================================================
        # DOMICILIARY TREATMENT
        # =====================================================

        if claim.domiciliary_treatment is True:

            if (
                claim.patient_cannot_be_moved is None
                and claim.hospital_room_unavailable is None
            ):

                missing_evidence.append(
                    "Domiciliary treatment eligibility "
                    "evidence is not documented."
                )

            elif not (
                claim.patient_cannot_be_moved is True
                or claim.hospital_room_unavailable is True
            ):

                exclusions.append(
                    "Domiciliary treatment conditions "
                    "are not satisfied."
                )

        # =====================================================
        # EXPERIMENTAL / UNPROVEN TREATMENT
        # =====================================================

        if claim.experimental is True:

            exclusions.append(
                "Unproven or experimental treatment "
                "is excluded under the policy."
            )

        # =====================================================
        # COSMETIC / AESTHETIC
        # =====================================================

        treatment_text = (
            f"{claim.treatment or ''} "
            f"{claim.diagnosis or ''}"
        ).lower()

        cosmetic_keywords = [
            "cosmetic",
            "aesthetic",
            "plastic surgery",
        ]

        is_cosmetic = any(
            keyword in treatment_text
            for keyword in cosmetic_keywords
        )

        if is_cosmetic:

            exclusions.append(
                "Cosmetic or aesthetic treatment "
                "is excluded unless covered under "
                "the applicable injury/disease exception."
            )

        # =====================================================
        # POLICY LIMITS
        # =====================================================

        basic_si = (
            claim.current_sum_insured
            or 0
        )

        if basic_si > 0:

            # -------------------------------------------------
            # ROOM
            # -------------------------------------------------

            applicable_limits.append(
                "Room rent: 1% of Basic Sum Insured per day."
            )

            if claim.room_expense is not None:

                room_limit = (
                    basic_si * 0.01 * coverage_days
                )

                if claim.room_expense > room_limit:

                    deduction = (
                        claim.room_expense
                        - room_limit
                    )

                    deductions.append(
                        {
                            "category": "room",
                            "claimed": claim.room_expense,
                            "allowed": room_limit,
                            "deduction": deduction,
                            "reason": (
                                "Room expense exceeds the applicable "
                                "1% Basic Sum Insured per-day limit "
                                "multiplied by the hospitalization duration."
                            ),
                        }
                    )

            # -------------------------------------------------
            # ICU
            # -------------------------------------------------

            applicable_limits.append(
                "ICU: 2% of Basic Sum Insured per day."
            )

            if claim.icu_expense is not None:

                icu_limit = (
                    basic_si * 0.02 * coverage_days
                )

                if claim.icu_expense > icu_limit:

                    deduction = (
                        claim.icu_expense
                        - icu_limit
                    )

                    deductions.append(
                        {
                            "category": "icu",
                            "claimed": claim.icu_expense,
                            "allowed": icu_limit,
                            "deduction": deduction,
                            "reason": (
                                "ICU expense exceeds the applicable "
                                "2% Basic Sum Insured per-day limit "
                                "multiplied by the hospitalization duration."
                            ),
                        }
                    )

            # -------------------------------------------------
            # DOCTOR
            # -------------------------------------------------

            applicable_limits.append(
                "Medical practitioner/consultant/surgeon: "
                "25% of Sum Insured."
            )

            if claim.doctor_expense is not None:

                doctor_limit = (
                    basic_si * 0.25
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
                                "Medical practitioner, consultant, "
                                "or surgeon expenses exceed the "
                                "applicable 25% Sum Insured limit."
                            ),
                        }
                    )

            # -------------------------------------------------
            # MEDICINES / DIAGNOSTICS
            # -------------------------------------------------

            applicable_limits.append(
                "Medicines/diagnostics and related expenses: "
                "40% of Sum Insured."
            )

            if claim.medicine_diagnostic_expense is not None:

                medicine_limit = (
                    basic_si * 0.40
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
                            "claimed": (
                                claim.medicine_diagnostic_expense
                            ),
                            "allowed": medicine_limit,
                            "deduction": deduction,
                            "reason": (
                                "Medicines and diagnostic expenses "
                                "exceed the applicable 40% "
                                "Sum Insured limit."
                            ),
                        }
                    )

            # -------------------------------------------------
            # AMBULANCE
            # -------------------------------------------------

            applicable_limits.append(
                "Ambulance: 1% of Basic Sum Insured "
                "or ₹1,000, whichever is less."
            )

            if claim.ambulance_expense is not None:

                ambulance_limit = min(
                    basic_si * 0.01,
                    1000.0,
                )

                if (
                    claim.ambulance_expense
                    > ambulance_limit
                ):

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
                                "Ambulance expense exceeds "
                                "the applicable policy limit."
                            ),
                        }
                    )

            # -------------------------------------------------
            # DOMICILIARY
            # -------------------------------------------------

            if claim.domiciliary_treatment is True:

                domiciliary_limit = (
                    basic_si * 0.20
                )

                if (
                    claim.claimed_amount is not None
                    and claim.claimed_amount
                    > domiciliary_limit
                ):

                    deduction = (
                        claim.claimed_amount
                        - domiciliary_limit
                    )

                    deductions.append(
                        {
                            "category": "domiciliary",
                            "claimed": claim.claimed_amount,
                            "allowed": domiciliary_limit,
                            "deduction": deduction,
                            "reason": (
                                "Domiciliary treatment exceeds "
                                "the applicable 20% Basic "
                                "Sum Insured limit."
                            ),
                        }
                    )

        # =====================================================
        # PRE-HOSPITALIZATION
        # =====================================================

        if (
            claim.pre_hospitalization_expense is not None
            and claim.pre_hospitalization_expense > 0
        ):

            if claim.expense_timing_present:

                if claim.pre_hospitalization_days_before is None:

                    missing_evidence.append(
                        "Pre-hospitalization expense timing "
                        "is not documented."
                    )

                elif (
                    claim.pre_hospitalization_days_before
                    > 30
                ):

                    deductions.append(
                        {
                            "category": "pre_hospitalization",
                            "claimed": (
                                claim.pre_hospitalization_expense
                            ),
                            "allowed": 0,
                            "deduction": (
                                claim.pre_hospitalization_expense
                            ),
                            "reason": (
                                "Pre-hospitalization expense falls "
                                "outside the maximum 30-day period."
                            ),
                        }
                    )

        # =====================================================
        # POST-HOSPITALIZATION
        # =====================================================

        if (
            claim.post_hospitalization_expense is not None
            and claim.post_hospitalization_expense > 0
        ):

            if claim.expense_timing_present:

                if (
                    claim.post_hospitalization_days_after_discharge
                    is None
                ):

                    missing_evidence.append(
                        "Post-hospitalization expense timing "
                        "is not documented."
                    )

                elif (
                    claim.post_hospitalization_days_after_discharge
                    > 60
                ):

                    deductions.append(
                        {
                            "category": "post_hospitalization",
                            "claimed": (
                                claim.post_hospitalization_expense
                            ),
                            "allowed": 0,
                            "deduction": (
                                claim.post_hospitalization_expense
                            ),
                            "reason": (
                                "Post-hospitalization expense falls "
                                "outside the maximum 60-day period."
                            ),
                        }
                    )

                elif (
                    claim.same_condition_confirmed is None
                ):

                    missing_evidence.append(
                        "Evidence that post-hospitalization "
                        "expenses relate to the same condition "
                        "is not documented."
                    )

                elif (
                    claim.same_condition_confirmed is False
                ):

                    deductions.append(
                        {
                            "category": "post_hospitalization",
                            "claimed": (
                                claim.post_hospitalization_expense
                            ),
                            "allowed": 0,
                            "deduction": (
                                claim.post_hospitalization_expense
                            ),
                            "reason": (
                                "Post-hospitalization expenses "
                                "are not confirmed to relate "
                                "to the same condition."
                            ),
                        }
                    )

        # =====================================================
        # PROVISIONAL PAYABLE
        # =====================================================

        claimed_amount = (
            claim.claimed_amount
            or 0.0
        )

        total_deductions = sum(
            float(
                item.get(
                    "deduction",
                    0,
                )
            )
            for item in deductions
        )

        provisional_payable = max(
            0.0,
            claimed_amount - total_deductions,
        )

        # =====================================================
        # DEDUP MISSING EVIDENCE
        # =====================================================

        missing_evidence = list(
            dict.fromkeys(
                missing_evidence
            )
        )

        # =====================================================
        # DEDUP EXCLUSIONS
        # =====================================================

        exclusions = list(
            dict.fromkeys(
                exclusions
            )
        )

        # =====================================================
        # DEDUP WAITING FAILURES
        # =====================================================

        waiting_failures = list(
            dict.fromkeys(
                waiting_failures
            )
        )

        # =====================================================
        # FINAL FINDINGS
        # =====================================================

        findings.extend(
            exclusions
        )

        findings.extend(
            waiting_failures
        )

        # =====================================================
        # RESULT
        # =====================================================

        return {
            "coverage_days": coverage_days,
            "coverage_months": coverage_months,

            "findings": findings,

            "missing_evidence": (
                missing_evidence
            ),

            "waiting_failures": (
                waiting_failures
            ),

            "exclusions": (
                exclusions
            ),

            "applicable_limits": (
                applicable_limits
            ),

            "deductions": (
                deductions
            ),

            "provisional_payable": (
                provisional_payable
            ),

            "evidence_count": len(
                policy_evidence
            ),
        }

    # =========================================================
    # LANGGRAPH RUN
    # =========================================================

    def run(
        self,
        state: dict[str, Any],
    ) -> dict[str, Any]:

        import time

        started = time.perf_counter()

        claim = state["claim"]

        policy_evidence = state.get(
            "policy_evidence",
            [],
        )

        result = self.analyze(
            claim,
            policy_evidence,
        )

        elapsed_ms = (
            time.perf_counter()
            - started
        ) * 1000

        state["coverage_analysis"] = result

        trace = state.setdefault(
            "trace",
            [],
        )

        trace.append(
            {
                "agent": "CoverageAgent",
                "action": (
                    "Evaluated waiting periods, exclusions, "
                    "facility eligibility, policy limits, "
                    "and expense admissibility."
                ),
                "retrieval_count": len(
                    policy_evidence
                ),
                "validation_status": None,
                "elapsed_ms": elapsed_ms,
            }
        )

        return state