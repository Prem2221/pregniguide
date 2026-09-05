from rag.loader import clean_text, load_all_pdfs


def test_clean_text_removes_non_ascii_lines():
    raw = "This is fine.\nयह हिंदी में है और हटाया जाना चाहिए।\nThis is also fine."
    result = clean_text(raw)
    assert "This is fine." in result
    assert "This is also fine." in result
    assert "हिंदी" not in result


def test_clean_text_handles_empty_input():
    assert clean_text("") == ""


def test_load_all_pdfs_returns_pages():
    pages = load_all_pdfs()
    assert len(pages) > 0
    assert all(p.text for p in pages)
    assert all(p.topic != "" for p in pages)