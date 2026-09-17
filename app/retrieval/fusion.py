def reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    k: int = 60,
    top_k: int = 15,
) -> list[dict]:

    fused = {}

    # Dense ranking
    for rank, result in enumerate(
        dense_results,
        start=1,
    ):
        chunk_id = result["chunk_id"]

        if chunk_id not in fused:
            fused[chunk_id] = {
                **result,
                "rrf_score": 0.0,
            }

        fused[chunk_id]["rrf_score"] += (
            1 / (k + rank)
        )

    # Sparse ranking
    for rank, result in enumerate(
        sparse_results,
        start=1,
    ):
        chunk_id = result["chunk_id"]

        if chunk_id not in fused:
            fused[chunk_id] = {
                **result,
                "rrf_score": 0.0,
            }

        fused[chunk_id]["rrf_score"] += (
            1 / (k + rank)
        )

    results = sorted(
        fused.values(),
        key=lambda x: x["rrf_score"],
        reverse=True,
    )

    return results[:top_k]