from app.retrieval.retriever import PolicyRetriever


def main():

    retriever = PolicyRetriever()

    query = """
    What is the pre-hospitalization and
    post-hospitalization coverage period?
    """

    results = retriever.retrieve(query)

    print("\n========== RETRIEVAL RESULTS ==========\n")

    for i, result in enumerate(results, start=1):

        print(f"Result #{i}")
        print("Chunk ID:", result["chunk_id"])
        print("Page:", result["page"])
        print("Section:", result["section"])
        print(
            "Reranker Score:",
            result["reranker_score"],
        )
        print("Text:")
        print(result["text"][:500])
        print("\n--------------------------------------\n")


if __name__ == "__main__":
    main()