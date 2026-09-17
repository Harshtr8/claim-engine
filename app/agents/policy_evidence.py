from datetime import datetime
from typing import Any

from app.orchestrator.state import ClaimEngineState
from app.retrieval.retriever import PolicyRetriever


class PolicyEvidenceAgent:

    name = "PolicyEvidenceAgent"

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        reranker_model: str = "BAAI/bge-reranker-base",
    ):
        self.retriever = PolicyRetriever(
            embedding_model=embedding_model,
            reranker_model=reranker_model,
        )

    def _build_queries(
        self,
        state: ClaimEngineState,
    ) -> list[str]:

        claim = state["claim"]
        analysis = state.get("case_analysis", {})

        queries = []

        # General coverage query
        if claim.diagnosis or claim.treatment:
            queries.append(
                f"""
                Is {claim.treatment or ''}
                for {claim.diagnosis or ''}
                covered under the policy?
                """
            )

        # Pre-existing disease
        if (
            claim.pre_existing_disease is not None
            or claim.pre_existing_details
        ):
            queries.append(
                """
                What are the policy rules for
                pre-existing diseases and their
                waiting period?
                """
            )

        # Portability
        if claim.prior_coverage_years is not None:
            queries.append(
                """
                What does the policy say about
                portability and credit for previous
                continuous coverage?
                """
            )

        # Hospitalization / day-care
        if (
            claim.is_inpatient is not None
            or claim.treatment_duration_hours is not None
        ):
            queries.append(
                """
                What are the policy definitions and
                requirements for hospitalization and
                day-care treatment?
                """
            )

        # Limits
        if (
            claim.room_expense is not None
            or claim.doctor_expense is not None
            or claim.medicine_diagnostic_expense is not None
            or claim.domiciliary_treatment is not None
        ):
            queries.append(
                """
                What policy limits apply to room,
                doctor, medicines, diagnostics and
                related hospitalization expenses?
                """
            )

        # Pre/post hospitalization
        if (
            claim.pre_hospitalization_expense is not None
            or claim.post_hospitalization_expense is not None
        ):
            queries.append(
                """
                What are the policy rules and time
                limits for pre-hospitalization and
                post-hospitalization expenses?
                """
            )

        # Fallback
        if not queries:
            queries.append(
                f"""
                What policy provisions are relevant
                to this insurance claim?

                Diagnosis: {claim.diagnosis}
                Treatment: {claim.treatment}
                Additional information:
                {claim.additional_information}
                """
            )

        return queries

    def run(
        self,
        state: ClaimEngineState,
    ) -> ClaimEngineState:

        start_time = datetime.now()

        queries = self._build_queries(state)

        all_results: dict[str, dict[str, Any]] = {}

        for query in queries:

            results = self.retriever.retrieve(
                query,
                dense_k=10,
                sparse_k=10,
                fusion_k=15,
                final_k=5,
            )

            for result in results:

                chunk_id = result["chunk_id"]

                if chunk_id not in all_results:
                    all_results[chunk_id] = result

                else:
                    # Keep the stronger reranker score
                    existing = all_results[chunk_id]

                    if (
                        result["reranker_score"]
                        > existing["reranker_score"]
                    ):
                        all_results[chunk_id] = result

        evidence = sorted(
            all_results.values(),
            key=lambda x: x["reranker_score"],
            reverse=True,
        )

        # Keep the strongest evidence
        evidence = evidence[:10]

        elapsed_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        trace = state.get("trace", [])

        trace.append(
            {
                "agent": self.name,
                "action": (
                    f"Generated {len(queries)} policy queries, "
                    f"combined dense and sparse retrieval, "
                    f"fused results and reranked evidence."
                ),
                "retrieval_count": len(evidence),
                "validation_status": "NOT_VALIDATED",
                "elapsed_ms": elapsed_ms,
            }
        )

        state["policy_evidence"] = evidence
        state["trace"] = trace

        return state