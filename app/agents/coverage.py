from datetime import datetime

from app.orchestrator.state import ClaimEngineState
from app.agents.policy_rules import (
    calculate_room_limit,
    calculate_icu_limit,
    calculate_doctor_limit,
    calculate_medicine_diagnostic_limit,
    calculate_domiciliary_limit,
    calculate_ambulance_limit,
)


class CoverageAgent:

    name = "CoverageAgent"

    def run(
        self,
        state: ClaimEngineState,
    ) -> ClaimEngineState:

        start_time = datetime.now()

        claim = state["claim"]
        evidence = state.get("policy_evidence", [])

        findings = []
        limits = []
        missing_evidence = []
        deductions = []

        coverage_days = (
            claim.claim_date - claim.policy_start_date
        ).days

        findings.append(
            f"Current policy coverage duration is "
            f"{coverage_days} days."
        )

        if claim.is_inpatient is True:
            findings.append(
                "Claim indicates inpatient treatment."
            )

        elif claim.is_inpatient is False:
            findings.append(
                "Claim does not indicate inpatient treatment."
            )

        else:
            missing_evidence.append(
                "Inpatient status is not established."
            )

        if claim.treatment_duration_hours is not None:

            if claim.treatment_duration_hours < 24:
                findings.append(
                    "Treatment duration is less than 24 hours."
                )
            else:
                findings.append(
                    "Treatment duration is at least 24 hours."
                )

        if claim.pre_existing_disease is True:

            findings.append(
                "Claim identifies a pre-existing disease."
            )

            if claim.prior_coverage_years is not None:

                findings.append(
                    "Previous continuous coverage information "
                    "is available."
                )

            else:

                missing_evidence.append(
                    "Previous continuous coverage information "
                    "is missing for portability analysis."
                )

        elif claim.pre_existing_disease is None:

            missing_evidence.append(
                "Pre-existing disease status is not established."
            )

        if not claim.hospital_name:

            missing_evidence.append(
                "Hospital information is missing."
            )

        if not claim.hospital_registration:

            missing_evidence.append(
                "Hospital registration evidence is missing."
            )

        basic_si = claim.current_sum_insured

        room_limit = calculate_room_limit(basic_si)

        if (
            room_limit is not None
            and claim.room_expense is not None
        ):

            limits.append(
                f"Room expense limit: ₹{room_limit:.2f}"
            )

            if claim.room_expense > room_limit:

                deduction = (
                    claim.room_expense - room_limit
                )

                deductions.append(
                    {
                        "category": "room_expense",
                        "claimed": claim.room_expense,
                        "allowed": room_limit,
                        "deduction": deduction,
                    }
                )

        doctor_limit = calculate_doctor_limit(basic_si)

        if (
            doctor_limit is not None
            and claim.doctor_expense is not None
        ):

            limits.append(
                f"Doctor expense limit: ₹{doctor_limit:.2f}"
            )

            if claim.doctor_expense > doctor_limit:

                deduction = (
                    claim.doctor_expense - doctor_limit
                )

                deductions.append(
                    {
                        "category": "doctor_expense",
                        "claimed": claim.doctor_expense,
                        "allowed": doctor_limit,
                        "deduction": deduction,
                    }
                )

        medicine_limit = (
            calculate_medicine_diagnostic_limit(
                basic_si
            )
        )

        if (
            medicine_limit is not None
            and claim.medicine_diagnostic_expense is not None
        ):

            limits.append(
                "Medicine/diagnostic expense limit: "
                f"₹{medicine_limit:.2f}"
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
                        "category": (
                            "medicine_diagnostic_expense"
                        ),
                        "claimed": (
                            claim.medicine_diagnostic_expense
                        ),
                        "allowed": medicine_limit,
                        "deduction": deduction,
                    }
                )

        if claim.domiciliary_treatment is True:

            domiciliary_limit = (
                calculate_domiciliary_limit(
                    basic_si
                )
            )

            if domiciliary_limit is not None:

                limits.append(
                    "Domiciliary hospitalization limit: "
                    f"₹{domiciliary_limit:.2f}"
                )

        ambulance_limit = (
            calculate_ambulance_limit(
                basic_si
            )
        )

        if (
            ambulance_limit is not None
            and claim.ambulance_expense is not None
        ):

            limits.append(
                f"Ambulance expense limit: ₹{ambulance_limit:.2f}"
            )

            if claim.ambulance_expense > ambulance_limit:

                deduction = (
                    claim.ambulance_expense
                    - ambulance_limit
                )

                deductions.append(
                    {
                        "category": "ambulance_expense",
                        "claimed": claim.ambulance_expense,
                        "allowed": ambulance_limit,
                        "deduction": deduction,
                    }
                )

        if (
            claim.pre_hospitalization_expense
            is not None
        ):

            limits.append(
                "Pre-hospitalization expenses must satisfy "
                "the policy time-window and admissibility conditions."
            )

        if (
            claim.post_hospitalization_expense
            is not None
        ):

            limits.append(
                "Post-hospitalization expenses must satisfy "
                "the policy time-window and admissibility conditions."
            )

        coverage_analysis = {
            "coverage_days": coverage_days,
            "findings": findings,
            "applicable_limits": limits,
            "missing_evidence": missing_evidence,
            "deductions": deductions,
            "evidence_count": len(evidence),
        }

        elapsed_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        trace = state.get("trace", [])

        trace.append(
            {
                "agent": self.name,
                "action": (
                    "Applied policy conditions and "
                    "deterministic expense limits."
                ),
                "retrieval_count": len(evidence),
                "validation_status": "NOT_VALIDATED",
                "elapsed_ms": elapsed_ms,
            }
        )

        state["coverage_analysis"] = coverage_analysis
        state["trace"] = trace

        return state