import pickle
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langfuse import observe

from rag.embedder import get_embedding_model
from rag.reranker import rerank

_db: FAISS | None = None
_bm25_data: dict | None = None


def get_vectorstore() -> FAISS:
    global _db
    if _db is None:
        _db = FAISS.load_local(
            "vectorstore", get_embedding_model(), allow_dangerous_deserialization=True
        )
    return _db


def get_bm25() -> dict:
    global _bm25_data
    if _bm25_data is None:
        with open(Path("vectorstore") / "bm25.pkl", "rb") as f:
            _bm25_data = pickle.load(f)
    return _bm25_data


def hybrid_retrieve(query: str, k: int = 10) -> list[Document]:
    """Combine dense (FAISS) and sparse (BM25) retrieval, deduplicated."""
    db = get_vectorstore()
    dense_results = db.similarity_search(query, k=k)

    bm25_data = get_bm25()
    tokenized_query = query.lower().split()
    bm25_scores = bm25_data["bm25"].get_scores(tokenized_query)
    top_bm25_indices = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )[:k]
    sparse_results = [bm25_data["documents"][i] for i in top_bm25_indices]

    seen = set()
    combined = []
    for doc in dense_results + sparse_results:
        key = doc.metadata.get("chunk_id")
        if key not in seen:
            seen.add(key)
            combined.append(doc)

    return combined


@observe(name="retrieve_context")
def retrieve(query: str, k: int = 4) -> list[Document]:
    """Full pipeline: rewrite -> hybrid retrieve -> optional rerank -> top k."""
    from config.settings import settings
    from rag.query_rewriter import rewrite_query  # avoid circular import at module load

    rewritten = rewrite_query(query)
    candidates = hybrid_retrieve(rewritten, k=10)

    if settings.enable_reranker:
        return rerank(query, candidates, top_k=k)  # rerank against ORIGINAL query

    return candidates[:k]  # skip reranking, truncate hybrid results


def format_context(docs: list[Document]) -> str:
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page_number", "?")
        parts.append(f"[Source: {source}, page {page}]\n{doc.page_content}")
    return "\n\n".join(parts)