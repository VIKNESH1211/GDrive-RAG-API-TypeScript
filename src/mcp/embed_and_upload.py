import os
import uuid
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct


def chunk_array(array: list, chunk_size: int) -> list[list]:
    """Split an array into chunks."""
    result = []
    for i in range(0, len(array), chunk_size):
        result.append(array[i:i + chunk_size])
    return result


def embed_and_upload_chunks(chunks: list[str]) -> None:
    """Embed chunks using Cohere and upload to Qdrant."""
    cohere_key = os.getenv("COHERE_API_KEY")
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_key = os.getenv("QDRANT_KEY")

    co = cohere.Client(api_key=cohere_key)
    qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)

    collection_name = "document-qna"
    max_batch_size = 96

    print(f"📦 Total chunks: {len(chunks)}")
    chunked_chunks = chunk_array(chunks, max_batch_size)

    for i, batch in enumerate(chunked_chunks):
        print(f"🔹 Processing batch {i + 1}/{len(chunked_chunks)} (size: {len(batch)})")

        embed_response = co.embed(
            texts=batch,
            model="embed-v4.0",
            input_type="search_document"
        )

        embeddings = embed_response.embeddings

        if not embeddings or len(embeddings) != len(batch):
            raise Exception("❌ Embedding failed or mismatched for batch.")

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[idx],
                payload={"text": chunk}
            )
            for idx, chunk in enumerate(batch)
        ]

        qdrant.upsert(
            collection_name=collection_name,
            points=points,
            wait=True
        )

        print(f"✅ Batch {i + 1} uploaded successfully.")

    print("🎉 All chunks embedded and uploaded to Qdrant.")
