import json
import pickle
from pathlib import Path


INDEX_DIR = Path("indexes")


class SparseRetriever:
    def __init__(self):
        with open(
            INDEX_DIR / "policy_bm25.pkl",
            "rb",
        ) as f:
            self.bm25 = pickle.load(f)

        with open(
            INDEX_DIR / "chunks.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.chunks = json.load(f)

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict]:

        tokens = query.lower().split()

        scores = self.bm25.get_scores(tokens)

        ranked_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True,
        )[:top_k]

        results = []

        for index in ranked_indices:

            chunk = self.chunks[index].copy()

            chunk["sparse_score"] = float(
                scores[index]
            )

            results.append(chunk)

        return results