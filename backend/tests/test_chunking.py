from app.utils.text import semantic_chunks


def test_document_chunking_preserves_all_content():
    text = "First sentence. " * 80 + "Critical final fact."
    chunks = semantic_chunks(text, target_chars=180, overlap_chars=20)
    assert len(chunks) > 2
    assert "Critical final fact" in chunks[-1]
    assert all(len(chunk) < 260 for chunk in chunks)


def test_empty_document_has_no_chunks():
    assert semantic_chunks("   \n") == []

