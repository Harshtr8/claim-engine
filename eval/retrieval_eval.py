from pathlib import Path
import json
import re
from app.retrieval.retriever import PolicyRetriever


ROOT = Path(__file__).resolve().parents[1]
CHUNKS_FILE = ROOT / "indexes" / "chunks.json"


RETRIEVAL_TESTS = [
    {
        "id": "R-001",
        "query": "general waiting period 30 days continuous coverage exception",
        "keywords": [
            "30 days",
            "waiting period",
            "continuous",
        ],
    },
    {
        "id": "R-002",
        "query": "pre-existing disease signs symptoms diagnosis medical advice treatment 48 months",
        "keywords": [
            "pre-existing",
            "48 months",
        ],
    },
    {
        "id": "R-003",
        "query": "portability transfer credit pre-existing disease waiting period previous insurer",
        "keywords": [
            "portability",
            "waiting period",
        ],
    },
    {
        "id": "R-004",
        "query": "hospitalization minimum 24 consecutive hours day care treatment",
        "keywords": [
            "24",
            "consecutive",
            "hospitalization",
        ],
    },
    {
        "id": "R-005",
        "query": "room rent 1% basic sum insured ICU 2% doctor fees 25%",
        "keywords": [
            "1%",
            "2%",
            "room",
            "ICU",
        ],
    },
    {
        "id": "R-006",
        "query": "medicines diagnostics other expenses 40% sum insured",
        "keywords": [
            "40%",
            "medicines",
            "diagnostics",
        ],
    },
    {
        "id": "R-007",
        "query": "ambulance charges 1% basic sum insured 1000 whichever less",
        "keywords": [
            "ambulance",
            "1%",
            "1000",
        ],
    },
    {
        "id": "R-008",
        "query": "pre hospitalization maximum 30 days post hospitalization maximum 60 days",
        "keywords": [
            "30 days",
            "60 days",
            "pre-hospitalization",
            "post-hospitalization",
        ],
    },
    {
        "id": "R-009",
        "query": "cosmetic aesthetic treatment plastic surgery injury disease exclusion",
        "keywords": [
            "cosmetic",
            "aesthetic",
            "plastic surgery",
        ],
    },
    {
        "id": "R-010",
        "query": "unproven experimental treatment excluded policy",
        "keywords": [
            "experimental",
            "unproven",
        ],
    },
]


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def keyword_hit(text: str, keywords: list[str]) -> bool:
    text = normalize(text)
    return any(normalize(keyword) in text for keyword in keywords)


def main():
    print("=" * 80)
    print("RETRIEVAL + CITATION EVALUATION")
    print("=" * 80)

    retriever = PolicyRetriever()

    results = []

    for test in RETRIEVAL_TESTS:
        retrieved = retriever.retrieve(
            test["query"],
            dense_k=10,
            sparse_k=10,
            fusion_k=15,
            final_k=5,
        )

        retrieved_chunks = []

        for item in retrieved:
            if isinstance(item, dict):
                chunk = item
            else:
                chunk = getattr(item, "metadata", {}) or {}

            retrieved_chunks.append(chunk)

        hit_rank = None

        for rank, chunk in enumerate(retrieved_chunks, start=1):
            text = chunk.get("text", "")

            if keyword_hit(text, test["keywords"]):
                hit_rank = rank
                break

        hit = hit_rank is not None
        reciprocal_rank = 1 / hit_rank if hit_rank else 0.0

        results.append(
            {
                "id": test["id"],
                "query": test["query"],
                "hit_at_5": hit,
                "first_relevant_rank": hit_rank,
                "reciprocal_rank": round(reciprocal_rank, 4),
                "retrieved_count": len(retrieved_chunks),
                "top_chunks": [
                    {
                        "chunk_id": c.get("chunk_id"),
                        "page": c.get("page"),
                        "section": c.get("section"),
                    }
                    for c in retrieved_chunks
                ],
            }
        )

        status = "PASS" if hit else "FAIL"

        print(
            f"{test['id']}  "
            f"Hit@5={str(hit):5}  "
            f"Rank={str(hit_rank):4}  "
            f"MRR={reciprocal_rank:.2f}  "
            f"[{status}]"
        )

    total = len(results)
    hits = sum(r["hit_at_5"] for r in results)

    hit_rate = hits / total if total else 0.0
    mrr = (
        sum(r["reciprocal_rank"] for r in results) / total
        if total
        else 0.0
    )

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Retrieval tests : {total}")
    print(f"Hit@5 correct   : {hits}")
    print(f"Hit@5 accuracy  : {hit_rate:.2%}")
    print(f"Mean Reciprocal : {mrr:.4f}")

    output = {
        "total_tests": total,
        "hit_at_5": hits,
        "hit_at_5_accuracy": round(hit_rate, 4),
        "mean_reciprocal_rank": round(mrr, 4),
        "results": results,
    }

    output_path = ROOT / "eval" / "retrieval_results.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()