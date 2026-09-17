from FlagEmbedding import FlagReranker


class PolicyReranker:

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-base",
    ):
        print("Loading reranker...")

        self.reranker = FlagReranker(
            model_name,
            use_fp16=False,
        )

    def rerank(
        self,
        query: str,
        candidates: list[dict],
        top_k: int = 5,
    ) -> list[dict]:

        if not candidates:
            return []

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