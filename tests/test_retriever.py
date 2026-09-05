from rag.retriever import retrieve


def test_retrieve_returns_relevant_results():
    results = retrieve("what foods should I avoid during pregnancy", k=4)

    assert len(results) == 4
    topics = [doc.metadata["topic"] for doc in results]
    # at least one result should be from a food-relevant topic
    assert any(t in ("nutrition", "lifestyle") for t in topics)


def test_retrieve_respects_k_parameter():
    results = retrieve("pregnancy vaccination", k=2)
    assert len(results) == 2