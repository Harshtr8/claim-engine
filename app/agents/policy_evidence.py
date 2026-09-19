from datetime import datetime
from typing import Any

from app.orchestrator.state import ClaimEngineState
from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import PolicyReranker


class PolicyEvidenceAgent:

    name = "PolicyEvidenceAgent"

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
        reranker_model: str = "BAAI/bge-reranker-base",
    ):
        # Load retrieval components once.
        self.dense = DenseRetriever(
            embedding_model=embedding_model
        )

        self.sparse = SparseRetriever()

        self.reranker = PolicyReranker(
            model_name=reranker_model
        )

    def _build_queries(
        self,
        state: ClaimEngineState,
    ) -> list[str]:

        claim = state["claim"]

        queries = []

        # ---------------------------------------------------------
        # General coverage
        # ---------------------------------------------------------
        if claim.diagnosis or claim.treatment:
            queries.append(
                f"""
                Is {claim.treatment or ''}
                for {claim.diagnosis or ''}
                covered under the policy?
                """
            )

        # ---------------------------------------------------------
        # Pre-existing disease
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Portability
        # ---------------------------------------------------------
        if claim.prior_coverage_years is not None:
            queries.append(
                """
                What does the policy say about
                portability and credit for previous
                continuous coverage?
                """
            )

        # ---------------------------------------------------------
        # Hospitalization / day-care
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Limits
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Pre/post hospitalization
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Fallback
        # ---------------------------------------------------------
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

        # ---------------------------------------------------------
        # Stage 1:
        # Dense + sparse retrieval for every query.
        #
        # IMPORTANT:
        # We do NOT rerank here.
        # ---------------------------------------------------------
        candidate_map: dict[str, dict[str, Any]] = {}

        for query in queries:

            dense_results = self.dense.search(
                query,
                top_k=10,
            )

            sparse_results = self.sparse.search(
                query,
                top_k=10,
            )

            fused_results = reciprocal_rank_fusion(
                dense_results,
                sparse_results,
                top_k=15,
            )

            # -----------------------------------------------------
            # Merge candidates across all queries.
            # -----------------------------------------------------
            for result in fused_results:

                chunk_id = result["chunk_id"]

                if chunk_id not in candidate_map:

                    candidate_map[chunk_id] = {
                        **result,
                        "query_matches": [query],
                    }

                else:

                    existing = candidate_map[chunk_id]

                    existing.setdefault(
                        "query_matches",
                        [],
                    )

                    if query not in existing["query_matches"]:
                        existing["query_matches"].append(query)

                    # Keep the strongest RRF score.
                    if (
                        result.get("rrf_score", 0.0)
                        > existing.get("rrf_score", 0.0)
                    ):

                        existing["rrf_score"] = (
                            result.get("rrf_score", 0.0)
                        )

                    # Preserve stronger dense score when available.
                    if (
                        result.get("dense_score", float("-inf"))
                        > existing.get(
                            "dense_score",
                            float("-inf"),
                        )
                    ):

                        existing["dense_score"] = (
                            result.get("dense_score")
                        )

        # ---------------------------------------------------------
        # Stage 2:
        # Single reranking pass over the merged candidates.
        # ---------------------------------------------------------

        candidates = list(
            candidate_map.values()
        )

        # The reranker needs one query.
        #
        # Combine the policy questions into one contextual
        # reranking query so that the reranker evaluates each
        # chunk against the complete claim-policy context.
        rerank_query = "\n".join(
            queries
        )

        reranked = self.reranker.rerank(
            rerank_query,
            candidates,
            top_k=10,
        )

        # ---------------------------------------------------------
        # Remove temporary query metadata from final evidence.
        # ---------------------------------------------------------

        evidence = []

        for result in reranked:

            item = result.copy()

            item.pop(
                "query_matches",
                None,
            )

            evidence.append(item)

        # ---------------------------------------------------------
        # Trace
        # ---------------------------------------------------------

        elapsed_ms = (
            datetime.now() - start_time
        ).total_seconds() * 1000

        trace = state.get(
            "trace",
            [],
        )

        trace.append(
            {
                "agent": self.name,
                "action": (
                    f"Generated {len(queries)} policy queries, "
                    f"combined dense and sparse retrieval, "
                    f"fused {len(candidate_map)} unique candidates, "
                    f"and performed one reranking pass."
                ),
                "retrieval_count": len(evidence),
                "validation_status": "NOT_VALIDATED",
                "elapsed_ms": elapsed_ms,
            }
        )

        state["policy_evidence"] = evidence
        state["trace"] = trace

        return state