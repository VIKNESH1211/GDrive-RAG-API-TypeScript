import os
import requests

VECTOR_DIM = 1536
MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
_URL = "https://api.openai.com/v1/embeddings"


def _embed(texts: list[str]) -> list[list[float]]:
    resp = requests.post(
        _URL,
        json={"model": MODEL, "input": texts, "dimensions": VECTOR_DIM},
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = sorted(resp.json()["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in data]


def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts)


def embed_query(text: str) -> list[float]:
    return _embed([text])[0]
