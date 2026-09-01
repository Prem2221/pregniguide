import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from rag.chunker import Chunk, chunk_pages
from rag.embedder import get_embedding_model
from rag.loader import load_all_pdfs

logger = logging.getLogger(__name__)

VECTORSTORE_DIR = Path("vectorstore")


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


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    build_vectorstore()