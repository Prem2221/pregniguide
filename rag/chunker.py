import logging
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.loader import LoadedPage, load_all_pdfs

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    topic: str
    page_number: int


def chunk_pages(pages: list[LoadedPage]) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[Chunk] = []
    for page in pages:
        pieces = splitter.split_text(page.text)
        for i, piece in enumerate(pieces):
            chunk_id = f"{page.source}::p{page.page_number}::c{i}"
            chunks.append(Chunk(
                chunk_id=chunk_id,
                text=piece,
                source=page.source,
                topic=page.topic,
                page_number=page.page_number,
            ))

    return chunks


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    pages = load_all_pdfs()
    chunks = chunk_pages(pages)

    print(f"\nTotal chunks: {len(chunks)}")
    avg_len = sum(len(c.text) for c in chunks) / len(chunks)
    print(f"Average chunk length: {avg_len:.0f} characters")

    # Show one example so you can sanity-check the output
    print("\n--- Example chunk ---")
    print(f"ID: {chunks[50].chunk_id}")
    print(f"Topic: {chunks[50].topic}")
    print(chunks[50].text)