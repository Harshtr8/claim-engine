from functools import lru_cache

from FlagEmbedding import FlagReranker


@lru_cache(maxsize=2)
def get_reranker(model_name: str) -> FlagReranker:
    print(f"Loading reranker model: {model_name}")

    return FlagReranker(
        model_name,
        use_fp16=False,
    )


class PolicyReranker:

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
    ):
        self.model_name = model_name
        self.reranker = get_reranker(model_name)

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:

        if not candidates:
            return []

        # No need to rerank when there are fewer candidates
        # than the requested final result count.
        if len(candidates) <= top_k:
            results = []

            for candidate in candidates:
                item = candidate.copy()
                item["reranker_score"] = float(
                    item.get("rrf_score", 0.0)
                )
                results.append(item)

            return results

        pairs = [
            [query, candidate["text"]]
            for candidate in candidates
        ]

        scores = self.reranker.compute_score(
            pairs,
            normalize=True,
        )

        if not isinstance(scores, list):
            scores = [scores]

        results = []

        for candidate, score in zip(
            candidates,
            scores,
        ):
            item = candidate.copy()
            item["reranker_score"] = float(score)
            results.append(item)

        results.sort(
            key=lambda x: x["reranker_score"],
            reverse=True,
        )

        return results[:top_k]