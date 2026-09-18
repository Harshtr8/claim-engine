from datetime import datetime

from app.orchestrator.state import ClaimEngineState


class ValidationAgent:

    name = "ValidationAgent"

    def run(
        self,
        state: ClaimEngineState,
    ) -> ClaimEngineState:

        start_time = datetime.now()

        decision = state.get("decision")
        evidence = state.get("policy_evidence", [])

        unsupported_claims = []

        if decision is None:
            unsupported_claims.append(
                "No decision was generated."
            )

        if not evidence:
            unsupported_claims.append(
                "No policy evidence was retrieved."
            )

        if decision is not None:

            if not decision.citations:
                unsupported_claims.append(
                    "Decision contains no policy citations."
                )

            evidence_ids = {
                item["chunk_id"]
                for item in evidence
            }

            for citation in decision.citations:

                if citation.chunk_id not in evidence_ids:
                    unsupported_claims.append(
                        f"Citation references unknown chunk "
                        f"{citation.chunk_id}."
                    )

            if decision.decision == "NEEDS_REVIEW":

                validation_status = "VALID_ABSTENTION"

            elif unsupported_claims:

                validation_status = "INVALID"

            else:

                validation_status = "VALID"

            decision.validation.status = validation_status
            decision.validation.unsupported_claims = (
                unsupported_claims
            )

            state["decision"] = decision

        else:

            validation_status = "INVALID"

        elapsed_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        trace = state.get("trace", [])

        trace.append(
            {
                "agent": self.name,
                "action": (
                    "Validated decision structure, "
                    "policy citation references and "
                    "abstention status."
                ),
                "retrieval_count": len(evidence),
                "validation_status": validation_status,
                "elapsed_ms": elapsed_ms,
            }
        )

        state["validation"] = {
            "status": validation_status,
            "unsupported_claims": unsupported_claims,
        }

        state["trace"] = trace

        return state