import os
import cohere

VECTOR_DIM = 1536
MODEL = "embed-v4.0"

_co = cohere.Client(os.getenv("COHERE_API_KEY"))


def _extract_vectors(response) -> list[list[float]]:
    emb = response.embeddings
    # cohere v5 with embedding_types returns EmbeddingsByType
    if isinstance(emb, list):
        return emb
    return emb.float_


def embed_documents(texts: list[str]) -> list[list[float]]:
    response = _co.embed(texts=texts, model=MODEL, input_type="search_document")
    return _extract_vectors(response)


def embed_query(text: str) -> list[float]:
    response = _co.embed(texts=[text], model=MODEL, input_type="search_query")
    return _extract_vectors(response)[0]
