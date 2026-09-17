from datetime import date, datetime

from app.orchestrator.state import ClaimEngineState


class CaseAnalysisAgent:

    name = "CaseAnalysisAgent"

    def run(self, state: ClaimEngineState) -> ClaimEngineState:

        start_time = datetime.now()

        claim = state["claim"]

        analysis = {
            "case_id": claim.case_id,
            "policy_start_date": str(
                claim.policy_start_date
            ),
            "claim_date": str(
                claim.claim_date
            ),
            "coverage_days": (
                claim.claim_date
                - claim.policy_start_date
            ).days,
            "diagnosis": claim.diagnosis,
            "treatment": claim.treatment,
            "is_inpatient": claim.is_inpatient,
            "treatment_duration_hours": (
                claim.treatment_duration_hours
            ),
            "pre_existing_disease": (
                claim.pre_existing_disease
            ),
            "prior_coverage_years": (
                claim.prior_coverage_years
            ),
            "prior_sum_insured": (
                claim.prior_sum_insured
            ),
            "current_sum_insured": (
                claim.current_sum_insured
            ),
            "claimed_amount": (
                claim.claimed_amount
            ),
        }

        missing_evidence = []

        if claim.is_inpatient is None:
            missing_evidence.append(
                "Whether the treatment was inpatient."
            )

        if not claim.diagnosis:
            missing_evidence.append(
                "Diagnosis information."
            )

        if not claim.treatment:
            missing_evidence.append(
                "Treatment information."
            )

        if not claim.hospital_name:
            missing_evidence.append(
                "Hospital information."
            )

        analysis["missing_evidence"] = missing_evidence

        elapsed_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        trace = state.get("trace", [])

        trace.append(
            {
                "agent": self.name,
                "action": (
                    "Parsed claim attributes, "
                    "calculated coverage duration, "
                    "and identified missing evidence."
                ),
                "retrieval_count": 0,
                "validation_status": "NOT_VALIDATED",
                "elapsed_ms": elapsed_ms,
            }
        )

        state["case_analysis"] = analysis
        state["trace"] = trace

        return state