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
    Load cases from:
      - a directory of JSON files
      - a JSON list
      - {"cases": [...]}
      - a single JSON object
    """

    if path.is_dir():

        cases = []

        for file_path in sorted(path.glob("*.json")):

            data = load_json(file_path)

            if isinstance(data, list):
                cases.extend(data)

            elif isinstance(data, dict):

                if isinstance(data.get("cases"), list):
                    cases.extend(data["cases"])

                else:
                    cases.append(data)

        return cases

    data = load_json(path)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        if isinstance(data.get("cases"), list):
            return data["cases"]

        return [data]

    raise ValueError(
        f"Unsupported case format: {path}"
    )


def load_expected(path: Path) -> dict[str, dict]:
    """
    Supports:

    {
        "PUB-001": {
            "expected_decision": "ADMISSIBLE"
        }
    }

    and:

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

            if case_id:
                output[case_id] = item

        return output

    raise ValueError(
        f"Unsupported expected-outcomes format: {path}"
    )


# ============================================================
# OBJECT HELPERS
# ============================================================

def get_field(obj: Any, field: str, default=None):
    """
    Safely retrieve a field from:
      - dict
      - Pydantic v2 model
      - Pydantic v1 model
      - normal Python object
    """

    if obj is None:
        return default

    if isinstance(obj, dict):
        return obj.get(field, default)

    return getattr(obj, field, default)


def to_jsonable(obj: Any):
    """
    Convert Pydantic objects / nested objects into
    JSON-serializable Python structures.
    """

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, list):
        return [
            to_jsonable(item)
            for item in obj
        ]

    if isinstance(obj, tuple):
        return [
            to_jsonable(item)
            for item in obj
        ]

    if isinstance(obj, dict):
        return {
            str(key): to_jsonable(value)
            for key, value in obj.items()
        }

    if hasattr(obj, "model_dump"):
        return to_jsonable(
            obj.model_dump()
        )

    if hasattr(obj, "dict"):
        return to_jsonable(
            obj.dict()
        )

    if hasattr(obj, "__dict__"):
        return to_jsonable(
            vars(obj)
        )

    return str(obj)


# ============================================================
# CITATION SERIALIZATION
# ============================================================

def serialize_citation(citation: Any) -> dict:

    if citation is None:
        return {}

    if isinstance(citation, dict):
        return {
            "claim": citation.get("claim", ""),
            "source": citation.get("source", ""),
            "page": citation.get("page"),
            "section": citation.get("section", ""),
            "chunk_id": citation.get("chunk_id", ""),
        }

    return {
        "claim": get_field(
            citation,
            "claim",
            "",
        ),
        "source": get_field(
            citation,
            "source",
            "",
        ),
        "page": get_field(
            citation,
            "page",
            None,
        ),
        "section": get_field(
            citation,
            "section",
            "",
        ),
        "chunk_id": get_field(
            citation,
            "chunk_id",
            "",
        ),
    }


# ============================================================
# TRACE SERIALIZATION
# ============================================================

def serialize_trace_step(step: Any) -> dict:

    if step is None:
        return {}

    if isinstance(step, dict):
        return dict(step)

    return {
        "agent": get_field(
            step,
            "agent",
            "",
        ),
        "action": get_field(
            step,
            "action",
            "",
        ),
        "retrieval_count": get_field(
            step,
            "retrieval_count",
            None,
        ),
        "validation_status": get_field(
            step,
            "validation_status",
            None,
        ),
        "elapsed_ms": get_field(
            step,
            "elapsed_ms",
            None,
        ),
    }


# ============================================================
# VALIDATION SERIALIZATION
# ============================================================

def serialize_validation(validation: Any) -> dict:

    if validation is None:
        return {}

    if isinstance(validation, dict):
        return dict(validation)

    return {
        "status": get_field(
            validation,
            "status",
            "",
        ),
        "unsupported_claims": get_field(
            validation,
            "unsupported_claims",
            [],
        ),
    }


# ============================================================
# DECISION NORMALIZATION
# ============================================================

def normalize_decision(decision: Any) -> str:
    """
    Convert DecisionOutput.decision into a plain string.

    Handles:
      - string
      - enum
      - Pydantic value
      - arbitrary objects
    """

    if decision is None:
        return ""

    if isinstance(decision, str):
        return decision

    # Enum-like objects
    value = getattr(
        decision,
        "value",
        None,
    )

    if value is not None:
        return str(value)

    return str(decision)


# ============================================================
# SINGLE CASE EVALUATION
# ============================================================

def evaluate_case(
    raw_case: dict,
    expected_entry: dict,
    engine: ClaimEngine,
    case_type: str,
) -> dict:

    case_id = str(
        raw_case.get(
            "case_id",
            "UNKNOWN",
        )
    )

    expected_decision = normalize_decision(
        expected_entry.get(
            "expected_decision",
            "",
        )
    )

    # --------------------------------------------------------
    # Adapt case
    # --------------------------------------------------------

    claim = adapt_public_case(
        raw_case
    )

    # --------------------------------------------------------
    # Run engine
    # --------------------------------------------------------

    output = engine.analyze(
        claim
    )

    # --------------------------------------------------------
    # Extract output fields
    # --------------------------------------------------------

    actual_decision = normalize_decision(
        get_field(
            output,
            "decision",
            "",
        )
    )

    confidence = get_field(
        output,
        "confidence",
        None,
    )

    payable_amount = get_field(
        output,
        "payable_amount",
        None,
    )

    key_findings = get_field(
        output,
        "key_findings",
        [],
    ) or []

    applicable_limits = get_field(
        output,
        "applicable_limits",
        [],
    ) or []

    missing_evidence = get_field(
        output,
        "missing_evidence",
        [],
    ) or []

    deductions = get_field(
        output,
        "deductions",
        [],
    ) or []

    citations_raw = get_field(
        output,
        "citations",
        [],
    ) or []

    trace_raw = get_field(
        output,
        "trace",
        [],
    ) or []

    validation_raw = get_field(
        output,
        "validation",
        None,
    )

    # --------------------------------------------------------
    # Serialize citations
    # --------------------------------------------------------

    citations = []

    for citation in citations_raw:

        serialized = serialize_citation(
            citation
        )

        if serialized:
            citations.append(
                serialized
            )

    # --------------------------------------------------------
    # Serialize trace
    # --------------------------------------------------------

    trace = []

    for step in trace_raw:

        serialized = serialize_trace_step(
            step
        )

        if serialized:
            trace.append(
                serialized
            )

    # --------------------------------------------------------
    # Serialize validation
    # --------------------------------------------------------

    validation = serialize_validation(
        validation_raw
    )

    # --------------------------------------------------------
    # Convert nested values
    # --------------------------------------------------------

    key_findings = to_jsonable(
        key_findings
    )

    applicable_limits = to_jsonable(
        applicable_limits
    )

    missing_evidence = to_jsonable(
        missing_evidence
    )

    deductions = to_jsonable(
        deductions
    )

    # --------------------------------------------------------
    # Correctness
    # --------------------------------------------------------

    correct = (
        actual_decision
        == expected_decision
    )

    # --------------------------------------------------------
    # Final case result
    # --------------------------------------------------------

    return {
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
        # Complete citation objects are persisted.
        "citation_count": len(citations),
        "citations": citations,

        # Trace contains operational information only.
        "trace": trace,

        "validation": validation,

        "missing_evidence_count": len(
            missing_evidence
        ),

        "deduction_count": len(
            deductions
        ),
    }


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

        case_id = str(
            raw_case.get(
                "case_id",
                "UNKNOWN",
            )
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

        # IMPORTANT:
        # actual/expected are now guaranteed strings.
        print(
            f"{case_id:<10} "
            f"Expected={result['expected']:<25} "
            f"Actual={result['actual']:<25} "
            f"[{status}]"
        )

        results.append(
            result
        )

    return results


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    results: list[dict],
) -> dict:

    total = len(
        results
    )

    correct = sum(
        1
        for result in results
        if result.get("correct") is True
    )

    abstentions = sum(
        1
        for result in results
        if result.get("actual")
        == "NEEDS_REVIEW"
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
    # Validate inputs
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
    # Load cases
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
        f"Loaded public cases : "
        f"{len(public_cases)}"
    )

    print(
        f"Loaded custom cases : "
        f"{len(custom_cases)}"
    )

    print()

    # --------------------------------------------------------
    # Initialize engine once
    # --------------------------------------------------------

    engine = ClaimEngine()

    # --------------------------------------------------------
    # PUBLIC
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
    # CUSTOM
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
    # Citation metrics
    # --------------------------------------------------------

    total_citations = sum(
        result.get(
            "citation_count",
            0,
        )
        for result in all_results
    )

    cases_with_citations = sum(
        1
        for result in all_results
        if result.get(
            "citation_count",
            0,
        ) > 0
    )

    # --------------------------------------------------------
    # SUMMARY
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

    print()
    print("=" * 80)
    print("CITATION SUMMARY")
    print("=" * 80)

    print(
        f"Total citations     : "
        f"{total_citations}"
    )

    print(
        f"Cases with citations: "
        f"{cases_with_citations}/"
        f"{len(all_results)}"
    )

    # --------------------------------------------------------
    # SAVE RESULTS
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

    # --------------------------------------------------------
    # Detailed output
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

    print()
    print(
        f"Results saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()