def chunk_text(full_text: str, max_chars: int = 500, overlap: int = 25) -> list[str]:
    """Chunk text into overlapping pieces."""
    chunks: list[str] = []
    start = 0

    while start < len(full_text):
        end = min(start + max_chars, len(full_text))
        chunk = full_text[start:end].strip()

        if len(chunk) > 0:
            chunks.append(chunk)

        start += max_chars - overlap

    return chunks
