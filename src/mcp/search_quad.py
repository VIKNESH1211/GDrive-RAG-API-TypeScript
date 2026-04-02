import os
from qdrant_client import QdrantClient


def search_context(vector: list[float]) -> str:
    """Search Qdrant for context based on a vector."""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_KEY")

    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)

    results = qdrant.query_points(
        collection_name="document-qna",
        query=vector,
        limit=5
    ).points

    context = "\n\n".join(
        point.payload.get("text", "") for point in results if point.payload
    )

    return context
