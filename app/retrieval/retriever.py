from app.retrieval.dense import DenseRetriever
from app.retrieval.sparse import SparseRetriever
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import PolicyReranker


class PolicyRetriever:

    def __init__(
        self,
        embedding_model="BAAI/bge-small-en-v1.5",
        reranker_model="BAAI/bge-reranker-base",
    ):
        self.dense = DenseRetriever(
            embedding_model=embedding_model
        )

        self.sparse = SparseRetriever()

        self.reranker = PolicyReranker(
            model_name=reranker_model
        )

    def retrieve(
        self,
        query: str,
        dense_k: int = 10,
        sparse_k: int = 10,
        fusion_k: int = 15,
        final_k: int = 5,
    ) -> list[dict]:

        dense_results = self.dense.search(
            query,
            top_k=dense_k,
        )

        sparse_results = self.sparse.search(
            query,
            top_k=sparse_k,
        )

        fused_results = reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            top_k=fusion_k,
        )

        final_results = self.reranker.rerank(
            query,
            fused_results,
            top_k=final_k,
        )

        return final_results