import json
import pickle
from pathlib import Path

import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer


INDEX_DIR = Path("indexes")
INDEX_DIR.mkdir(exist_ok=True)


def build_indexes(chunks: list[dict], embedding_model: str):
    """
    Build FAISS dense index and BM25 sparse index.
    """

    if not chunks:
        raise ValueError("No chunks provided.")

    texts = [chunk["text"] for chunk in chunks]

    print("Loading embedding model...")
    model = SentenceTransformer(embedding_model)

    print("Creating embeddings...")
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )

    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]

    # Dense FAISS index
    faiss_index = faiss.IndexFlatIP(dimension)
    faiss_index.add(embeddings)

    faiss.write_index(
        faiss_index,
        str(INDEX_DIR / "policy.faiss"),
    )

    # Sparse BM25 index
    tokenized_documents = [
        text.lower().split()
        for text in texts
    ]

    bm25 = BM25Okapi(tokenized_documents)

    with open(
        INDEX_DIR / "policy_bm25.pkl",
        "wb",
    ) as f:
        pickle.dump(bm25, f)

    # Store metadata separately
    with open(
        INDEX_DIR / "chunks.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            chunks,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print("Indexes created successfully.")
    print(f"Chunks: {len(chunks)}")
    print(f"Embedding dimension: {dimension}")


if __name__ == "__main__":
    from app.ingestion.loader import load_policy
    from app.ingestion.chunker import chunk_pages

    pdf_path = (
        "data/policy/"
        "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
    )

    embedding_model = "BAAI/bge-small-en-v1.5"

    pages = load_policy(pdf_path)

    chunks = chunk_pages(pages)

    build_indexes(
        chunks,
        embedding_model,
    )