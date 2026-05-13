import re


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> list[str]:
    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text.strip())

    # Collect sentences across paragraphs, preserving paragraph breaks as context
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    sentences: list[str] = []
    for para in paragraphs:
        # Split on sentence boundaries: ., !, ? followed by space or end
        parts = re.split(r"(?<=[.!?])\s+", para)
        sentences.extend(s.strip() for s in parts if s.strip())

    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        if current_len + len(sent) + 1 > max_chars and current:
            chunks.append(" ".join(current))
            # Keep trailing sentences for overlap
            overlap_sents: list[str] = []
            used = 0
            for s in reversed(current):
                if used + len(s) <= overlap:
                    overlap_sents.insert(0, s)
                    used += len(s)
                else:
                    break
            current = overlap_sents
            current_len = sum(len(s) for s in current)

        current.append(sent)
        current_len += len(sent) + 1

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if c.strip()]
