import os
from qdrant_client import QdrantClient
from qdrant_client.models import Filter


def clear_collection() -> dict:
    """Clear all documents from the Qdrant collection."""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_KEY")

    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)
    collection_name = "document-qna"

    try:
        response = qdrant.delete(
            collection_name=collection_name,
            points_selector=Filter(must=[])  # Match all documents
        )

        return {"success": True, "message": "Collection cleared", "response": str(response)}
    except Exception as error:
        print(f"❌ Error while clearing collection: {error}")
        return {
            "success": False,
            "message": "Failed to clear collection",
            "error": str(error)
        }
