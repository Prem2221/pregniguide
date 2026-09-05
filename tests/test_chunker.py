from rag.chunker import chunk_pages
from rag.loader import LoadedPage


def test_chunk_pages_splits_long_text():
    long_text = "This is a sentence. " * 200  # long enough to require multiple chunks
    page = LoadedPage(source="test.pdf", topic="test", page_number=1, text=long_text)

    chunks = chunk_pages([page])

    assert len(chunks) > 1
    assert all(chunk.source == "test.pdf" for chunk in chunks)
    assert all(chunk.topic == "test" for chunk in chunks)


def test_chunk_pages_keeps_short_text_as_one_chunk():
    short_text = "This is a short page."
    page = LoadedPage(source="test.pdf", topic="test", page_number=1, text=short_text)

    chunks = chunk_pages([page])

    assert len(chunks) == 1
    assert chunks[0].text == short_text