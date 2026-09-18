from __future__ import annotations

import json
from pathlib import Path

from app.orchestrator.graph import ClaimEngine
from eval.case_adapter import adapt_public_case


ROOT = Path(__file__).resolve().parents[1]

PUBLIC_CASES = (
    ROOT
    / "data"
    / "public_cases"
    / "public_test_cases.json"
)

EXPECTED = (
    ROOT
    / "eval"
    / "expected_outcomes.json"
)


def load_cases() -> list[dict]:
    with PUBLIC_CASES.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def load_expected() -> dict:
    with EXPECTED.open(
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def main() -> None:
    cases = load_cases()
    expected = load_expected()

    engine = ClaimEngine()

    results: list[dict] = []

    correct = 0
    abstentions = 0

    print("=" * 80)
    print("CLAIM ENGINE EVALUATION")
    print("=" * 80)

    for raw_case in cases:

        case_id = raw_case["case_id"]

        claim = adapt_public_case(raw_case)

        state = engine.analyze(claim)

        decision_output = state["decision"]

        actual = decision_output.decision

        expected_decision = (
            expected[case_id]["expected_decision"]
        )

        is_correct = (
            actual == expected_decision
        )

        if is_correct:
            correct += 1

        if actual == "NEEDS_REVIEW":
            abstentions += 1

        results.append(
            {
                "case_id": case_id,
                "expected": expected_decision,
                "actual": actual,
                "correct": is_correct,
                "confidence": (
                    decision_output.confidence
                ),
                "payable_amount": (
                    decision_output.payable_amount
                ),
                "citation_count": len(
                    decision_output.citations
                ),
                "missing_evidence_count": len(
                    decision_output.missing_evidence
                ),
                "deduction_count": len(
                    decision_output.deductions
                ),
            }
        )

        status = (
            "PASS"
            if is_correct
            else "FAIL"
        )

        print(
            f"{case_id:<10} "
            f"Expected={expected_decision:<25} "
            f"Actual={actual:<25} "
            f"[{status}]"
        )

    # =========================================================
    # Summary
    # =========================================================

    total = len(results)

    accuracy = (
        correct / total
        if total
        else 0.0
    )

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        f"Total cases       : {total}"
    )

    print(
        f"Correct decisions : {correct}"
    )

    print(
        f"Accuracy          : {accuracy:.2%}"
    )

    print(
        f"Abstentions       : {abstentions}"
    )

    # =========================================================
    # Detailed results
    # =========================================================

    print("\nDetailed Results:")

    print(
        json.dumps(
            results,
            indent=2,
            default=str,
        )
    )

    # =========================================================
    # Save results
    # =========================================================

    output_file = (
        ROOT
        / "eval"
        / "results.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            {
                "total_cases": total,
                "correct": correct,
                "accuracy": accuracy,
                "abstentions": abstentions,
                "results": results,
            },
            f,
            indent=2,
            default=str,
        )

    print(
        f"\nResults saved to: {output_file}"
    )


if __name__ == "__main__":
    main()
