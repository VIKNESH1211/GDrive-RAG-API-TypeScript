import os

from src.openai_client import post_json

VECTOR_DIM = 1536
MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
_URL = "https://api.openai.com/v1/embeddings"


def _embed(texts: list[str]) -> list[list[float]]:
    data = post_json(
        _URL,
        {"model": MODEL, "input": texts, "dimensions": VECTOR_DIM},
        timeout=60,
    )
    items = sorted(data["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in items]


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts)


def embed_query(text: str) -> list[float]:
    return _embed([text])[0]
