from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]

CHUNKS_FILE = ROOT / "indexes" / "chunks.json"
RESULTS_FILE = ROOT / "eval" / "results.json"
OUTPUT_FILE = ROOT / "eval" / "citation_results.json"


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_chunk_index(chunks):
    """
    Build:
        chunk_id -> chunk metadata
    """
    index = {}

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")

        if chunk_id:
            index[chunk_id] = chunk

    return index


def validate_citation(citation, chunk_index):
    """
    Validate one citation against the actual indexed policy chunk.
    """

    errors = []

    chunk_id = citation.get("chunk_id")
    citation_page = citation.get("page")
    citation_source = citation.get("source")
    citation_section = citation.get("section")

    # ---------------------------------------------------------
    # 1. chunk_id must exist
    # ---------------------------------------------------------

    if not chunk_id:
        errors.append("missing_chunk_id")
        return False, errors

    if chunk_id not in chunk_index:
        errors.append("invalid_chunk_id")
        return False, errors

    chunk = chunk_index[chunk_id]

    # ---------------------------------------------------------
    # 2. Page must match indexed chunk
    # ---------------------------------------------------------

    actual_page = chunk.get("page")

    if citation_page != actual_page:
        errors.append(
            f"page_mismatch: citation={citation_page}, actual={actual_page}"
        )

    # ---------------------------------------------------------
    # 3. Source must match indexed chunk
    # ---------------------------------------------------------

    actual_source = chunk.get("source")

    if citation_source != actual_source:
        errors.append(
            f"source_mismatch: citation={citation_source}, actual={actual_source}"
        )

    # ---------------------------------------------------------
    # 4. Section must match indexed chunk
    # ---------------------------------------------------------

    actual_section = chunk.get("section")

    if citation_section != actual_section:
        errors.append(
            "section_mismatch: "
            f"citation={citation_section}, actual={actual_section}"
        )

    return len(errors) == 0, errors


def main():

    print("=" * 80)
    print("CITATION CORRECTNESS EVALUATION")
    print("=" * 80)

    # ---------------------------------------------------------
    # Load files
    # ---------------------------------------------------------

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(
            f"Missing chunks file: {CHUNKS_FILE}"
        )

    if not RESULTS_FILE.exists():
        raise FileNotFoundError(
            f"Missing evaluation results: {RESULTS_FILE}"
        )

    chunks = load_json(CHUNKS_FILE)
    results_data = load_json(RESULTS_FILE)

    # ---------------------------------------------------------
    # Build chunk index
    # ---------------------------------------------------------

    chunk_index = build_chunk_index(chunks)

    print(f"Indexed policy chunks : {len(chunk_index)}")

    # ---------------------------------------------------------
    # Results structure supports:
    #
    # {
    #   "results": [...]
    # }
    #
    # ---------------------------------------------------------

    case_results = results_data.get("results", [])

    total_cases = len(case_results)

    total_citations = 0
    valid_citations = 0

    cases_with_citations = 0
    cases_without_citations = 0

    all_case_outputs = []

    # ---------------------------------------------------------
    # Validate every case
    # ---------------------------------------------------------

    for case in case_results:

        case_id = case.get("case_id")

        # The evaluation result currently contains citation_count,
        # but not the actual citations. Therefore, citation data
        # must be loaded from the engine output if available.
        #
        # We support an optional "citations" field so this evaluator
        # can work with richer result files.

        citations = case.get("citations", [])

        citation_count = case.get("citation_count", len(citations))

        total_citations += citation_count

        case_valid = True
        case_errors = []

        if citation_count > 0:
            cases_with_citations += 1
        else:
            cases_without_citations += 1
            case_valid = False
            case_errors.append("no_citations")

        # Validate actual citation objects when present.
        for citation in citations:

            is_valid, errors = validate_citation(
                citation,
                chunk_index,
            )

            if is_valid:
                valid_citations += 1
            else:
                case_valid = False
                case_errors.extend(errors)

        all_case_outputs.append(
            {
                "case_id": case_id,
                "citation_count": citation_count,
                "valid": case_valid,
                "errors": case_errors,
            }
        )

        status = "PASS" if case_valid else "FAIL"

        print(
            f"{case_id:<10} "
            f"Citations={citation_count:<3} "
            f"[{status}]"
        )

        if case_errors:
            for error in case_errors:
                print(f"  - {error}")

    # ---------------------------------------------------------
    # Citation metrics
    # ---------------------------------------------------------

    citation_validity = (
        valid_citations / total_citations
        if total_citations > 0
        else 0.0
    )

    citation_coverage = (
        cases_with_citations / total_cases
        if total_cases > 0
        else 0.0
    )

    invalid_citations = total_citations - valid_citations

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Cases evaluated       : {total_cases}")
    print(f"Total citations       : {total_citations}")
    print(f"Valid citations       : {valid_citations}")
    print(f"Invalid citations     : {invalid_citations}")
    print(f"Citation validity     : {citation_validity:.2%}")
    print(f"Cases with citations  : {cases_with_citations}")
    print(f"Citation coverage     : {citation_coverage:.2%}")

    # ---------------------------------------------------------
    # Save results
    # ---------------------------------------------------------

    output = {
        "cases_evaluated": total_cases,
        "total_citations": total_citations,
        "valid_citations": valid_citations,
        "invalid_citations": invalid_citations,
        "citation_validity": round(citation_validity, 4),
        "cases_with_citations": cases_with_citations,
        "cases_without_citations": cases_without_citations,
        "citation_coverage": round(citation_coverage, 4),
        "results": all_case_outputs,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Results saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()