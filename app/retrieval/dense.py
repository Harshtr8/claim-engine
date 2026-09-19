import json
from functools import lru_cache
from pathlib import Path

import faiss
from sentence_transformers import SentenceTransformer


INDEX_DIR = Path("indexes")


@lru_cache(maxsize=2)
def get_embedding_model(
    model_name: str,
) -> SentenceTransformer:

    print(f"Loading dense embedding model: {model_name}")

    return SentenceTransformer(model_name)


class DenseRetriever:

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-small-en-v1.5",
    ):

        self.index = faiss.read_index(
            str(INDEX_DIR / "policy.faiss")
        )

        with open(
            INDEX_DIR / "chunks.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.chunks = json.load(f)

        self.model = get_embedding_model(
            embedding_model
        )

    def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> list[dict]:

        embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        embedding = embedding.astype("float32")

        scores, indices = self.index.search(
            embedding,
            top_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index == -1:
                continue

            chunk = self.chunks[index].copy()

            chunk["dense_score"] = float(score)

            results.append(chunk)

        return results