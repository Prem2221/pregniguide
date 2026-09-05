import logging
import pickle
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from rag.chunker import Chunk, chunk_pages
from rag.embedder import get_embedding_model
from rag.loader import load_all_pdfs

logger = logging.getLogger(__name__)

VECTORSTORE_DIR = Path("vectorstore")
BM25_PATH = VECTORSTORE_DIR / "bm25.pkl"


def chunks_to_documents(chunks: list[Chunk]) -> list[Document]:
    return [
        Document(
            page_content=chunk.text,
            metadata={
                "chunk_id": chunk.chunk_id,
                "source": chunk.source,
                "topic": chunk.topic,
                "page_number": chunk.page_number,
            },
        )
        for chunk in chunks
    ]


def build_bm25_index(documents: list[Document]) -> None:
    tokenized_corpus = [doc.page_content.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)

    with open(BM25_PATH, "wb") as f:
        pickle.dump({"bm25": bm25, "documents": documents}, f)

    logger.info("Saved BM25 index with %d documents", len(documents))


def build_vectorstore() -> None:
    logger.info("Loading and chunking PDFs...")
    pages = load_all_pdfs()
    chunks = chunk_pages(pages)
    documents = chunks_to_documents(chunks)

    logger.info("Embedding %d chunks (this may take a minute on CPU)...", len(documents))
    embeddings = get_embedding_model()
    db = FAISS.from_documents(documents, embeddings)

    VECTORSTORE_DIR.mkdir(exist_ok=True)
    db.save_local(str(VECTORSTORE_DIR))
    logger.info("Saved vectorstore with %d vectors to %s", db.index.ntotal, VECTORSTORE_DIR)

    build_bm25_index(documents)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build_vectorstore()