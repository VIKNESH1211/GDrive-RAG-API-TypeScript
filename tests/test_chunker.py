from src.chunker import chunk_text


def test_empty_text_gives_no_chunks():
    assert chunk_text("   \n\n ") == []


def test_chunks_respect_max_chars():
    text = " ".join(f"This is sentence number {i}." for i in range(200))
    chunks = chunk_text(text, max_chars=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 + 60 for c in chunks)


def test_overlap_repeats_trailing_sentence():
    text = "Alpha one. Bravo two. Charlie three. Delta four. Echo five."
    chunks = chunk_text(text, max_chars=30, overlap=15)
    assert len(chunks) >= 2
    assert any(w in chunks[1] for w in ("Bravo", "Charlie", "Delta"))
