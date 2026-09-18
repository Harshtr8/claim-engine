from pathlib import Path
import json
from typing import Any

from app.orchestrator.graph import ClaimEngine
from eval.case_adapter import adapt_public_case


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PUBLIC_CASES = ROOT / "data" / "public_cases"
CUSTOM_CASES = ROOT / "data" / "custom_cases" / "custom_test_cases.json"

PUBLIC_EXPECTED = ROOT / "eval" / "expected_outcomes.json"
CUSTOM_EXPECTED = ROOT / "eval" / "custom_expected_outcomes.json"

OUTPUT_FILE = ROOT / "eval" / "results.json"


# ============================================================
# JSON HELPERS
# ============================================================

def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_cases(path: Path) -> list[dict]:
    """
    Load cases from either:

    1. A JSON list
    2. A JSON object containing a cases list
    3. A directory containing JSON files
    """

    if path.is_dir():

        cases = []

        files = sorted(path.glob("*.json"))

        for file_path in files:
            data = load_json(file_path)

            if isinstance(data, list):
                cases.extend(data)

            elif isinstance(data, dict):

                if "cases" in data and isinstance(data["cases"], list):
                    cases.extend(data["cases"])

                else:
                    cases.append(data)

        return cases

    data = load_json(path)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        if "cases" in data and isinstance(data["cases"], list):
            return data["cases"]

        return [data]

    raise ValueError(f"Unsupported case format: {path}")


def load_expected(path: Path) -> dict[str, dict]:
    """
    Supports:

    {
        "PUB-001": {
            "expected_decision": "ADMISSIBLE"
        }
    }

    or:

    [
        {
            "case_id": "PUB-001",
            "expected_decision": "ADMISSIBLE"
        }
    ]
    """

    data = load_json(path)

    if isinstance(data, dict):
        return data

    if isinstance(data, list):

        output = {}

        for item in data:

            case_id = item.get("case_id")

            if not case_id:
                continue

            output[case_id] = item

        return output

    raise ValueError(f"Unsupported expected-outcomes format: {path}")


# ============================================================
# SERIALIZATION HELPERS
# ============================================================

def serialize_citation(citation: Any) -> dict:
    """
    Convert a Pydantic Citation object or dictionary
    into a JSON-safe dictionary.
    """

    if citation is None:
        return {}

    # Pydantic v2
    if hasattr(citation, "model_dump"):
        return citation.model_dump()

    # Pydantic v1
    if hasattr(citation, "dict"):
        return citation.dict()

    if isinstance(citation, dict):
        return dict(citation)

    return {
        "claim": getattr(citation, "claim", ""),
        "source": getattr(citation, "source", ""),
        "page": getattr(citation, "page", None),
        "section": getattr(citation, "section", ""),
        "chunk_id": getattr(citation, "chunk_id", ""),
    }


def serialize_trace_step(step: Any) -> dict:
    """
    Convert trace objects into JSON-safe dictionaries.
    """

    if step is None:
        return {}

    if hasattr(step, "model_dump"):
        return step.model_dump()

    if hasattr(step, "dict"):
        return step.dict()

    if isinstance(step, dict):
        return dict(step)

    return {
        "agent": getattr(step, "agent", ""),
        "action": getattr(step, "action", ""),
        "retrieval_count": getattr(step, "retrieval_count", None),
        "validation_status": getattr(step, "validation_status", None),
        "elapsed_ms": getattr(step, "elapsed_ms", None),
    }


def serialize_validation(validation: Any) -> dict:
    """
    Convert validation result into JSON-safe dictionary.
    """

    if validation is None:
        return {}

    if hasattr(validation, "model_dump"):
        return validation.model_dump()

    if hasattr(validation, "dict"):
        return validation.dict()

    if isinstance(validation, dict):
        return dict(validation)

    return {
        "status": getattr(validation, "status", ""),
        "unsupported_claims": getattr(
            validation,
            "unsupported_claims",
            [],
        ),
    }


def get_output_field(output: Any, field: str, default=None):
    """
    Safely read a field from either a Pydantic object or dict.
    """

    if output is None:
        return default

    if isinstance(output, dict):
        return output.get(field, default)

    return getattr(output, field, default)


# ============================================================
# SINGLE CASE EVALUATION
# ============================================================

def evaluate_case(
    raw_case: dict,
    expected_entry: dict,
    engine: ClaimEngine,
    case_type: str,
) -> dict:

    case_id = raw_case.get("case_id", "UNKNOWN")

    expected_decision = expected_entry.get(
        "expected_decision"
    )

    # --------------------------------------------------------
    # Adapt raw case into ClaimCase
    # --------------------------------------------------------

    claim = adapt_public_case(raw_case)

    # --------------------------------------------------------
    # Run claim engine
    # --------------------------------------------------------

    output = engine.analyze(claim)

    # --------------------------------------------------------
    # Read decision
    # --------------------------------------------------------

    actual_decision = get_output_field(
        output,
        "decision",
        "",
    )

    confidence = get_output_field(
        output,
        "confidence",
        None,
    )

    payable_amount = get_output_field(
        output,
        "payable_amount",
        None,
    )

    key_findings = get_output_field(
        output,
        "key_findings",
        [],
    )

    applicable_limits = get_output_field(
        output,
        "applicable_limits",
        [],
    )

    missing_evidence = get_output_field(
        output,
        "missing_evidence",
        [],
    )

    deductions = get_output_field(
        output,
        "deductions",
        [],
    )

    citations_raw = get_output_field(
        output,
        "citations",
        [],
    )

    trace_raw = get_output_field(
        output,
        "trace",
        [],
    )

    validation_raw = get_output_field(
        output,
        "validation",
        None,
    )

    # --------------------------------------------------------
    # Serialize citations
    # --------------------------------------------------------

    citations = [
        serialize_citation(citation)
        for citation in (citations_raw or [])
    ]

    # Remove empty citation objects if any
    citations = [
        citation
        for citation in citations
        if citation
    ]

    # --------------------------------------------------------
    # Serialize trace
    # --------------------------------------------------------

    trace = [
        serialize_trace_step(step)
        for step in (trace_raw or [])
    ]

    trace = [
        step
        for step in trace
        if step
    ]

    # --------------------------------------------------------
    # Serialize validation
    # --------------------------------------------------------

    validation = serialize_validation(validation_raw)

    # --------------------------------------------------------
    # Correctness
    # --------------------------------------------------------

    correct = actual_decision == expected_decision

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    result = {
        "case_id": case_id,
        "case_type": case_type,

        "expected": expected_decision,
        "actual": actual_decision,
        "correct": correct,

        "confidence": confidence,
        "payable_amount": payable_amount,

        "key_findings": key_findings,
        "applicable_limits": applicable_limits,
        "missing_evidence": missing_evidence,
        "deductions": deductions,

        # IMPORTANT:
        # Store the complete citation objects.
        "citation_count": len(citations),
        "citations": citations,

        # Store complete trace without hidden chain-of-thought.
        "trace": trace,

        # Store validation result.
        "validation": validation,

        "missing_evidence_count": len(
            missing_evidence or []
        ),

        "deduction_count": len(
            deductions or []
        ),
    }

    return result


# ============================================================
# BATCH EVALUATION
# ============================================================

def evaluate_cases(
    cases: list[dict],
    expected: dict[str, dict],
    engine: ClaimEngine,
    case_type: str,
) -> list[dict]:

    results = []

    for raw_case in cases:

        case_id = raw_case.get(
            "case_id",
            "UNKNOWN",
        )

        if case_id not in expected:
            print(
                f"{case_id:<10} "
                f"Expected outcome missing "
                f"[SKIP]"
            )
            continue

        result = evaluate_case(
            raw_case=raw_case,
            expected_entry=expected[case_id],
            engine=engine,
            case_type=case_type,
        )

        status = (
            "PASS"
            if result["correct"]
            else "FAIL"
        )

        print(
            f"{case_id:<10} "
            f"Expected={result['expected']:<25} "
            f"Actual={result['actual']:<25} "
            f"[{status}]"
        )

        results.append(result)

    return results


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(results: list[dict]) -> dict:

    total = len(results)

    correct = sum(
        1
        for result in results
        if result.get("correct") is True
    )

    abstentions = sum(
        1
        for result in results
        if result.get("actual") == "NEEDS_REVIEW"
    )

    accuracy = (
        correct / total
        if total
        else 0.0
    )

    return {
        "total": total,
        "correct": correct,
        "accuracy": round(
            accuracy,
            4,
        ),
        "abstentions": abstentions,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("CLAIM ENGINE EVALUATION")
    print("=" * 80)
    print()

    # --------------------------------------------------------
    # Validate input files
    # --------------------------------------------------------

    required_paths = [
        PUBLIC_CASES,
        CUSTOM_CASES,
        PUBLIC_EXPECTED,
        CUSTOM_EXPECTED,
    ]

    for path in required_paths:

        if not path.exists():
            raise FileNotFoundError(
                f"Required evaluation input missing: {path}"
            )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    public_cases = load_cases(
        PUBLIC_CASES
    )

    custom_cases = load_cases(
        CUSTOM_CASES
    )

    public_expected = load_expected(
        PUBLIC_EXPECTED
    )

    custom_expected = load_expected(
        CUSTOM_EXPECTED
    )

    print(
        f"Loaded public cases : {len(public_cases)}"
    )

    print(
        f"Loaded custom cases : {len(custom_cases)}"
    )

    print()

    # --------------------------------------------------------
    # Initialize engine ONCE
    #
    # This avoids repeatedly loading:
    # - embedding model
    # - BM25 index
    # - reranker
    # --------------------------------------------------------

    engine = ClaimEngine()

    # --------------------------------------------------------
    # Public cases
    # --------------------------------------------------------

    print("=" * 80)
    print("PUBLIC CASE EVALUATION")
    print("=" * 80)

    public_results = evaluate_cases(
        cases=public_cases,
        expected=public_expected,
        engine=engine,
        case_type="Public",
    )

    # --------------------------------------------------------
    # Custom cases
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("CUSTOM CASE EVALUATION")
    print("=" * 80)

    custom_results = evaluate_cases(
        cases=custom_cases,
        expected=custom_expected,
        engine=engine,
        case_type="Custom",
    )

    # --------------------------------------------------------
    # Combine
    # --------------------------------------------------------

    all_results = (
        public_results
        + custom_results
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    public_metrics = calculate_metrics(
        public_results
    )

    custom_metrics = calculate_metrics(
        custom_results
    )

    overall_metrics = calculate_metrics(
        all_results
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)

    print(
        f"Public cases       : "
        f"{public_metrics['total']}"
    )

    print(
        f"Public correct     : "
        f"{public_metrics['correct']}"
    )

    print(
        f"Public accuracy    : "
        f"{public_metrics['accuracy']:.2%}"
    )

    print(
        f"Custom cases       : "
        f"{custom_metrics['total']}"
    )

    print(
        f"Custom correct     : "
        f"{custom_metrics['correct']}"
    )

    print(
        f"Custom accuracy    : "
        f"{custom_metrics['accuracy']:.2%}"
    )

    print(
        f"Total cases        : "
        f"{overall_metrics['total']}"
    )

    print(
        f"Correct decisions  : "
        f"{overall_metrics['correct']}"
    )

    print(
        f"Overall accuracy   : "
        f"{overall_metrics['accuracy']:.2%}"
    )

    print(
        f"Abstentions        : "
        f"{overall_metrics['abstentions']}"
    )

    # --------------------------------------------------------
    # Citation statistics
    # --------------------------------------------------------

    total_citations = sum(
        result.get("citation_count", 0)
        for result in all_results
    )

    cases_with_citations = sum(
        1
        for result in all_results
        if result.get("citation_count", 0) > 0
    )

    print()
    print("=" * 80)
    print("CITATION SUMMARY")
    print("=" * 80)

    print(
        f"Total citations    : "
        f"{total_citations}"
    )

    print(
        f"Cases with citations: "
        f"{cases_with_citations}/{len(all_results)}"
    )

    # --------------------------------------------------------
    # Detailed results
    # --------------------------------------------------------

    print()
    print("Detailed Results:")

    print(
        json.dumps(
            all_results,
            indent=2,
            ensure_ascii=False,
        )
    )

    # --------------------------------------------------------
    # Final JSON
    # --------------------------------------------------------

    output = {
        "public": {
            **public_metrics,
            "cases": public_results,
        },

        "custom": {
            **custom_metrics,
            "cases": custom_results,
        },

        "overall": {
            **overall_metrics,
            "total_citations": total_citations,
            "cases_with_citations": cases_with_citations,
        },

        "results": all_results,
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print(
        f"Results saved to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()