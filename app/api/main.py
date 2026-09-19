from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.orchestrator.graph import ClaimEngine
from app.schemas.claim import ClaimCase
from app.schemas.decision import DecisionOutput


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="Policy-Aware Insurance Claim Decision Engine",
    description=(
        "Multi-agent RAG system for insurance claim analysis, "
        "policy-grounded decisions, citations, deductions, "
        "and evidence-aware abstention."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ENGINE
# ============================================================

engine: ClaimEngine | None = None


def get_engine() -> ClaimEngine:
    """
    Lazily initialize the claim engine.

    Lazy initialization prevents expensive embedding,
    reranker, FAISS and BM25 loading during module import.
    """

    global engine

    if engine is None:
        engine = ClaimEngine()

    return engine


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health() -> dict[str, Any]:
    """
    Basic service health endpoint.
    """

    return {
        "status": "ok",
        "service": "policy-aware-claim-engine",
        "version": "1.0.0",
    }


# ============================================================
# ANALYZE CLAIM
# ============================================================

@app.post(
    "/analyze",
    response_model=DecisionOutput,
)
def analyze_claim(claim: ClaimCase) -> DecisionOutput:
    """
    Analyze an insurance claim using the multi-agent
    policy-aware RAG pipeline.
    """

    started = time.perf_counter()

    try:
        claim_engine = get_engine()

        result = claim_engine.analyze(claim)

        # ClaimEngine normally returns the final DecisionOutput.
        # If it returns a state dictionary, extract the decision.
        if isinstance(result, DecisionOutput):
            decision = result

        elif isinstance(result, dict):
            decision = result.get("decision")

            if isinstance(decision, DecisionOutput):
                pass

            elif isinstance(decision, dict):
                try:
                    decision = DecisionOutput.model_validate(
                        decision
                    )
                except AttributeError:
                    decision = DecisionOutput.parse_obj(
                        decision
                    )

            else:
                raise TypeError(
                    "ClaimEngine returned a state without "
                    "a valid DecisionOutput."
                )

        else:
            decision = getattr(
                result,
                "decision",
                None,
            )

            if isinstance(decision, dict):
                try:
                    decision = DecisionOutput.model_validate(
                        decision
                    )
                except AttributeError:
                    decision = DecisionOutput.parse_obj(
                        decision
                    )

        if not isinstance(decision, DecisionOutput):
            raise TypeError(
                "Unable to extract DecisionOutput "
                "from ClaimEngine result."
            )

        elapsed_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        # Do not modify the decision itself.
        # Add API timing only to logs.
        print(
            f"[API] case={claim.case_id} "
            f"decision={decision.decision} "
            f"elapsed_ms={elapsed_ms}"
        )

        return decision

    except HTTPException:
        raise

    except Exception as exc:
        print(
            f"[API ERROR] case={claim.case_id} "
            f"error={type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Claim analysis failed",
                "type": type(exc).__name__,
                "message": str(exc),
            },
        ) from exc


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "Policy-Aware Insurance Claim Decision Engine",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "analyze": "POST /analyze",
            "docs": "GET /docs",
        },
    }