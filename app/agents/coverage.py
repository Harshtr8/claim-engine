from __future__ import annotations

from datetime import date
from typing import Any

from app.retrieval.retriever import PolicyRetriever
from app.schemas.claim import ClaimCase


class CoverageAgent:
    """
    Deterministic policy coverage agent.

    Responsibilities:
    - Waiting periods
    - Pre-existing disease / portability
    - Hospitalization and day-care eligibility
    - Domiciliary treatment
    - Policy exclusions
    - Room / ICU / doctor / medicine / ambulance limits
    - Pre/post hospitalization windows
    - Structured deductions
    """

    def __init__(
        self,
        retriever: PolicyRetriever | None = None,
    ) -> None:
        self.retriever = retriever

    # =========================================================
    # STATE ENTRY POINT
    # =========================================================

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """
        Execute the agent using the shared engine state.
        """
        claim: ClaimCase = state["claim"]

        policy_evidence = state.get(
            "policy_evidence",
            [],
        )

        coverage_analysis = self.analyze(
            claim,
            policy_evidence,
        )

        state["coverage_analysis"] = coverage_analysis

        state.setdefault("trace", []).append(
            {
                "agent": "CoverageAgent",
                "action": (
                    "Evaluated waiting periods, exclusions, "
                    "facility eligibility, policy limits, "
                    "and expense admissibility."
                ),
                "retrieval_count": len(policy_evidence),
            }
        )

        return state

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _days_between(
        start: date,
        end: date,
    ) -> int:
        return max(
            (end - start).days,
            0,
        )

    @staticmethod
    def _coverage_months(
        claim: ClaimCase,
    ) -> float:
        """
        Prefer the dataset's explicit continuous coverage value.
        Otherwise calculate approximately.
        """

        if claim.dataset_continuous_coverage_months is not None:
            return float(
                claim.dataset_continuous_coverage_months
            )

        days = CoverageAgent._days_between(
            claim.policy_start_date,
            claim.claim_date,
        )

        return days / 30.4375

    @staticmethod
    def _hospitalization_days(
        claim: ClaimCase,
    ) -> float:
        """
        Calculate hospitalization duration.

        Room and ICU limits are PER DAY.

        Example:
        96 hours = 4 days
        Room limit = 1% SI × 4
        """

        if claim.treatment_duration_hours is not None:

            hours = float(
                claim.treatment_duration_hours
            )

            if hours > 0:
                return max(
                    hours / 24.0,
                    1.0,
                )

        if (
            claim.hospitalization_start_date
            is not None
            and claim.hospitalization_end_date
            is not None
        ):
            days = (
                claim.hospitalization_end_date
                - claim.hospitalization_start_date
            ).days

            return max(
                float(days),
                1.0,
            )

        return 1.0

    @staticmethod
    def _is_specified_disease(
        claim: ClaimCase,
    ) -> bool:

        diagnosis = (
            claim.diagnosis or ""
        ).strip().lower()

        specified_terms = [
            "asthma",
            "bronchitis",
            "chronic nephritis",
            "nephritic syndrome",
            "diarrhoea",
            "diarrhea",
            "dysentery",
            "gastro-enteritis",
            "gastroenteritis",
            "diabetes mellitus",
            "epilepsy",
            "hypertension",
            "influenza",
            "cough",
            "cold",
            "psychiatric",
            "psychosomatic",
            "pyrexia of unknown origin",
            "tonsillitis",
            "upper respiratory tract infection",
            "laryngitis",
            "pharyngitis",
            "arthritis",
            "gout",
            "rheumatism",
            "dental treatment",
            "dental surgery",
        ]

        return any(
            term in diagnosis
            for term in specified_terms
        )

    @staticmethod
    def _is_cosmetic_case(
        claim: ClaimCase,
    ) -> bool:

        text = " ".join(
            [
                claim.diagnosis or "",
                claim.treatment or "",
                claim.additional_information or "",
            ]
        ).lower()

        cosmetic_terms = [
            "cosmetic",
            "aesthetic",
            "beauty",
            "facial reconstruction",
            "liposuction",
            "rhinoplasty",
            "plastic surgery",
        ]

        return any(
            term in text
            for term in cosmetic_terms
        )

    @staticmethod
    def _add_deduction(
        deductions: list[dict[str, Any]],
        *,
        category: str,
        claimed: float,
        allowed: float,
        reason: str,
    ) -> None:

        claimed = float(claimed)

        allowed = max(
            float(allowed),
            0.0,
        )

        deduction = max(
            claimed - allowed,
            0.0,
        )

        if deduction > 0:

            deductions.append(
                {
                    "category": category,
                    "claimed": claimed,
                    "allowed": allowed,
                    "deduction": deduction,
                    "reason": reason,
                }
            )

    # =========================================================
    # ANALYSIS
    # =========================================================

    def analyze(
        self,
        claim: ClaimCase,
        policy_evidence: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:

        evidence = (
            policy_evidence or []
        )

        # -----------------------------------------------------
        # Basic calculations
        # -----------------------------------------------------

        coverage_days = self._days_between(
            claim.policy_start_date,
            claim.claim_date,
        )

        coverage_months = self._coverage_months(
            claim
        )

        hospitalization_days = (
            self._hospitalization_days(
                claim
            )
        )

        sum_insured = float(
            claim.current_sum_insured or 0
        )

        claimed_amount = float(
            claim.claimed_amount or 0
        )

        findings: list[str] = []

        missing_evidence: list[str] = []

        exclusions: list[str] = []

        waiting_failures: list[str] = []

        applicable_limits: list[str] = []

        deductions: list[dict[str, Any]] = []

        # =====================================================
        # GENERAL WAITING PERIOD
        # =====================================================

        general_waiting_exception = False

        if coverage_days < 30:

            prior_years = float(
                claim.prior_coverage_years or 0
            )

            if (
                prior_years >= 1
                and claim.prior_policy_records_received
                is True
            ):

                general_waiting_exception = True

                findings.append(
                    "The general 30-day waiting period is "
                    "satisfied through the qualifying prior "
                    "continuous individual health coverage "
                    "exception."
                )

            else:

                waiting_failures.append(
                    "Claim falls within the general 30-day "
                    "waiting period."
                )

        else:

            findings.append(
                "Claim occurs after the general 30-day "
                "waiting period."
            )

        # =====================================================
        # PRE-EXISTING DISEASE / PORTABILITY
        # =====================================================

        if claim.pre_existing_disease is True:

            pre_existing_waiting_months = 48.0

            prior_years = float(
                claim.prior_coverage_years or 0
            )

            prior_sum_insured = float(
                claim.prior_sum_insured or 0
            )

            current_sum_insured = float(
                claim.current_sum_insured or 0
            )

            qualifying_prior_coverage = (
                prior_years > 0
                and claim.prior_policy_records_received
                is True
                and claim.prior_policy_insurer_type
                in {
                    "indian_individual",
                    "individual",
                    "us",
                }
            )

            if qualifying_prior_coverage:

                reduced_waiting = max(
                    pre_existing_waiting_months
                    - (prior_years * 12.0),
                    0.0,
                )

                if (
                    current_sum_insured
                    > prior_sum_insured
                    and prior_sum_insured > 0
                ):

                    findings.append(
                        "Portability credit reduces the "
                        "pre-existing disease waiting period "
                        "to the extent of the previous Sum "
                        "Insured."
                    )

                pre_existing_waiting_months = (
                    reduced_waiting
                )

            if (
                coverage_months
                < pre_existing_waiting_months
            ):

                waiting_failures.append(
                    "Pre-existing disease remains within "
                    "the applicable waiting period."
                )

            else:

                findings.append(
                    "Pre-existing disease waiting period "
                    "has elapsed."
                )

        # =====================================================
        # SPECIFIED DISEASE
        # =====================================================

        is_specified_disease = (
            self._is_specified_disease(
                claim
            )
        )

        if is_specified_disease:

            prior_years = float(
                claim.prior_coverage_years or 0
            )

            specified_waiting_exception = (
                prior_years >= 1
                and claim.prior_policy_records_received
                is True
            )

            if coverage_months < 12:

                if not specified_waiting_exception:

                    waiting_failures.append(
                        "Specified disease is within the "
                        "one-year waiting period."
                    )

                else:

                    findings.append(
                        "The one-year specified-disease "
                        "waiting period is waived through "
                        "qualifying prior continuous coverage."
                    )

        # =====================================================
        # TREATMENT CLASSIFICATION
        # =====================================================

        is_domiciliary = bool(
            claim.domiciliary_treatment
        )

        is_day_care = (
            claim.is_inpatient is True
            and claim.treatment_duration_hours
            is not None
            and float(
                claim.treatment_duration_hours
            ) < 24
            and not is_domiciliary
        )

        # =====================================================
        # DOMICILIARY
        # =====================================================

        if is_domiciliary:

            if (
                claim.patient_cannot_be_moved
                is not True
                and claim.hospital_room_unavailable
                is not True
            ):

                if claim.evidence_context_present:

                    missing_evidence.append(
                        "Evidence is required to establish "
                        "the qualifying domiciliary treatment "
                        "condition."
                    )

            if (
                claim.medical_necessity_confirmed
                is False
            ):

                exclusions.append(
                    "Domiciliary treatment does not satisfy "
                    "the documented medical necessity "
                    "requirement."
                )

        # =====================================================
        # DAY CARE
        # =====================================================

        elif is_day_care:

            findings.append(
                "Treatment duration is below 24 hours and "
                "is evaluated under the policy's day-care "
                "provisions."
            )

        # =====================================================
        # INPATIENT
        # =====================================================

        elif claim.is_inpatient is True:

            duration_hours = float(
                claim.treatment_duration_hours or 0
            )

            if duration_hours >= 24:

                findings.append(
                    "Hospitalization meets the 24-hour "
                    "minimum duration requirement."
                )

            elif (
                claim.treatment_duration_hours
                is None
            ):

                missing_evidence.append(
                    "Hospitalization duration is required "
                    "to establish the 24-hour minimum."
                )

            else:

                exclusions.append(
                    "Hospitalization does not meet the "
                    "24-hour minimum duration requirement "
                    "and no applicable day-care exception "
                    "has been established."
                )

        # =====================================================
        # HOSPITAL EVIDENCE
        # =====================================================

        if claim.evidence_context_present:

            if claim.hospital_registered is None:

                missing_evidence.append(
                    "Hospital registration status is not "
                    "documented."
                )

            elif (
                claim.hospital_registered is False
            ):

                exclusions.append(
                    "Hospital registration requirement is "
                    "not satisfied."
                )

            if (
                claim.hospital_minimum_criteria_documented
                is None
            ):

                missing_evidence.append(
                    "Hospital minimum eligibility criteria "
                    "are not documented."
                )

            if (
                claim.medical_necessity_confirmed
                is None
            ):

                missing_evidence.append(
                    "Medical necessity is not documented."
                )

            elif (
                claim.medical_necessity_confirmed
                is False
            ):

                exclusions.append(
                    "Medical necessity for the treatment "
                    "has not been established."
                )

        # =====================================================
        # COSMETIC
        # =====================================================

        cosmetic_case = (
            self._is_cosmetic_case(
                claim
            )
        )

        if cosmetic_case:

            exclusions.append(
                "Cosmetic or aesthetic treatment is excluded "
                "unless it qualifies under the policy exception "
                "for plastic surgery relating to Injury or Disease."
            )

        # =====================================================
        # EXPERIMENTAL
        # =====================================================

        if claim.experimental is True:

            exclusions.append(
                "Unproven or experimental treatment is excluded "
                "under the policy."
            )

        # =====================================================
        # PRE / POST HOSPITALIZATION
        # =====================================================

        if claim.expense_timing_present:

            pre_days = (
                claim.pre_hospitalization_days_before
            )

            post_days = (
                claim.post_hospitalization_days_after_discharge
            )

            # -------------------------------------------------
            # Pre hospitalization
            # -------------------------------------------------

            if (
                claim.pre_hospitalization_expense
                and float(
                    claim.pre_hospitalization_expense
                ) > 0
            ):

                if pre_days is None:

                    missing_evidence.append(
                        "Pre-hospitalization timing is required "
                        "to validate the expense window."
                    )

                elif float(pre_days) <= 30:

                    findings.append(
                        "Pre-hospitalization expense falls within "
                        "the permitted 30-day window."
                    )

                else:

                    exclusions.append(
                        "Pre-hospitalization expense exceeds "
                        "the permitted 30-day window."
                    )

            # -------------------------------------------------
            # Post hospitalization
            # -------------------------------------------------

            if (
                claim.post_hospitalization_expense
                and float(
                    claim.post_hospitalization_expense
                ) > 0
            ):

                if post_days is None:

                    missing_evidence.append(
                        "Post-hospitalization timing is required "
                        "to validate the expense window."
                    )

                elif float(post_days) <= 60:

                    if (
                        claim.same_condition_confirmed
                        is True
                    ):

                        findings.append(
                            "Post-hospitalization expense falls "
                            "within the permitted 60-day window "
                            "and is confirmed for the same condition."
                        )

                    elif (
                        claim.same_condition_confirmed
                        is False
                    ):

                        exclusions.append(
                            "Post-hospitalization expense is not "
                            "confirmed for the same condition."
                        )

                    else:

                        missing_evidence.append(
                            "Same-condition confirmation is required "
                            "for post-hospitalization expenses."
                        )

                else:

                    exclusions.append(
                        "Post-hospitalization expense exceeds "
                        "the permitted 60-day window."
                    )

        # =====================================================
        # POLICY LIMITS
        # =====================================================

        if sum_insured > 0:

            # =================================================
            # ROOM
            # =================================================

            applicable_limits.append(
                "Room rent: 1% of Basic Sum Insured per day."
            )

            room_daily_limit = (
                0.01 * sum_insured
            )

            room_allowed = (
                room_daily_limit
                * hospitalization_days
            )

            if claim.room_expense is not None:

                self._add_deduction(
                    deductions,
                    category="room",
                    claimed=float(
                        claim.room_expense
                    ),
                    allowed=room_allowed,
                    reason=(
                        "Room expense exceeds the applicable "
                        "1% Basic Sum Insured per-day limit "
                        "multiplied by the hospitalization "
                        "duration."
                    ),
                )

            # =================================================
            # ICU
            # =================================================

            applicable_limits.append(
                "ICU: 2% of Basic Sum Insured per day."
            )

            icu_daily_limit = (
                0.02 * sum_insured
            )

            icu_allowed = (
                icu_daily_limit
                * hospitalization_days
            )

            if claim.icu_expense is not None:

                self._add_deduction(
                    deductions,
                    category="icu",
                    claimed=float(
                        claim.icu_expense
                    ),
                    allowed=icu_allowed,
                    reason=(
                        "ICU expense exceeds the applicable "
                        "2% Basic Sum Insured per-day limit "
                        "multiplied by the hospitalization "
                        "duration."
                    ),
                )

            # =================================================
            # DOCTOR
            # =================================================

            applicable_limits.append(
                "Medical practitioner/consultant/surgeon: "
                "25% of Sum Insured."
            )

            doctor_limit = (
                0.25 * sum_insured
            )

            if claim.doctor_expense is not None:

                self._add_deduction(
                    deductions,
                    category="doctor",
                    claimed=float(
                        claim.doctor_expense
                    ),
                    allowed=doctor_limit,
                    reason=(
                        "Medical practitioner, consultant, "
                        "or surgeon expenses exceed the "
                        "applicable 25% Sum Insured limit."
                    ),
                )

            # =================================================
            # MEDICINES / DIAGNOSTICS
            # =================================================

            applicable_limits.append(
                "Medicines/diagnostics and related expenses: "
                "40% of Sum Insured."
            )

            medicine_limit = (
                0.40 * sum_insured
            )

            if (
                claim.medicine_diagnostic_expense
                is not None
            ):

                self._add_deduction(
                    deductions,
                    category="medicines_diagnostics",
                    claimed=float(
                        claim.medicine_diagnostic_expense
                    ),
                    allowed=medicine_limit,
                    reason=(
                        "Medicines and diagnostic expenses "
                        "exceed the applicable 40% Sum "
                        "Insured limit."
                    ),
                )

            # =================================================
            # DOMICILIARY
            # =================================================

            if is_domiciliary:

                domiciliary_limit = (
                    0.20 * sum_insured
                )

                applicable_limits.append(
                    "Domiciliary treatment: "
                    "20% of Basic Sum Insured."
                )

                domiciliary_claim = (
                    float(
                        claim.doctor_expense or 0
                    )
                    + float(
                        claim.medicine_diagnostic_expense
                        or 0
                    )
                )

                self._add_deduction(
                    deductions,
                    category="domiciliary",
                    claimed=domiciliary_claim,
                    allowed=domiciliary_limit,
                    reason=(
                        "Domiciliary treatment expenses exceed "
                        "the applicable 20% Basic Sum Insured "
                        "aggregate sub-limit."
                    ),
                )

            # =================================================
            # AMBULANCE
            # =================================================

            applicable_limits.append(
                "Ambulance: 1% of Basic Sum Insured or "
                "₹1,000, whichever is less."
            )

            ambulance_limit = min(
                0.01 * sum_insured,
                1000.0,
            )

            if claim.ambulance_expense is not None:

                self._add_deduction(
                    deductions,
                    category="ambulance",
                    claimed=float(
                        claim.ambulance_expense
                    ),
                    allowed=ambulance_limit,
                    reason=(
                        "Ambulance expense exceeds the "
                        "applicable policy limit."
                    ),
                )

        # =====================================================
        # NO DEDUCTION FINDING
        # =====================================================

        if (
            not deductions
            and not exclusions
            and not waiting_failures
        ):

            findings.append(
                "No applicable policy sub-limit deduction "
                "was identified from the supplied claim facts."
            )

        # =====================================================
        # FINANCIAL CALCULATION
        # =====================================================

        total_deductions = sum(
            float(
                item.get(
                    "deduction",
                    0,
                )
                or 0
            )
            for item in deductions
            if isinstance(item, dict)
        )

        provisional_payable = max(
            claimed_amount
            - total_deductions,
            0.0,
        )

        # =====================================================
        # RETURN
        # =====================================================

        return {
            "coverage_days": coverage_days,

            "coverage_months": coverage_months,

            "general_waiting_exception":
                general_waiting_exception,

            "is_domiciliary":
                is_domiciliary,

            "is_day_care":
                is_day_care,

            "is_specified_disease":
                is_specified_disease,

            "cosmetic_case":
                cosmetic_case,

            "exclusions":
                exclusions,

            "waiting_failures":
                waiting_failures,

            "findings":
                findings,

            "missing_evidence":
                missing_evidence,

            "applicable_limits":
                applicable_limits,

            "deductions":
                deductions,

            "claimed_amount":
                claimed_amount,

            "total_deductions":
                total_deductions,

            "provisional_payable":
                provisional_payable,

            "evidence_count":
                len(evidence),

            "evidence_context_present":
                claim.evidence_context_present,

            "expense_timing_present":
                claim.expense_timing_present,

            "prior_policy_present":
                claim.prior_policy_present,
        }