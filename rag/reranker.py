import logging

from sentence_transformers import CrossEncoder
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_reranker: CrossEncoder | None = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def rerank(query: str, documents: list[Document], top_k: int = 4) -> list[Document]:
    if not documents:
        return []

    reranker = get_reranker()
    pairs = [(query, doc.page_content) for doc in documents]
    scores = reranker.predict(pairs)

    scored_docs = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
    return [doc for doc, score in scored_docs[:top_k]]