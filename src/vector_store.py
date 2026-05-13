import os
import uuid
import logging
from datetime import datetime, timezone

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)

from src.embedder import embed_documents, embed_query, VECTOR_DIM
from src.chunker import chunk_text

logger = logging.getLogger(__name__)

COLLECTION = "rag-documents"
BATCH_SIZE = 96


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            api_key=os.getenv("QDRANT_KEY") or None,
            timeout=30,
        )

    def init(self):
        existing = {c.name for c in self.client.get_collections().collections}
        if COLLECTION not in existing:
            self.client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection: %s", COLLECTION)

    def add_document(self, text: str, source_type: str, filename: str, doc_id: str) -> int:
        chunks = chunk_text(text)
        if not chunks:
            return 0

        ingested_at = datetime.now(timezone.utc).isoformat()
        points: list[PointStruct] = []

        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_start : batch_start + BATCH_SIZE]
            vectors = embed_documents(batch)
            for j, (chunk, vector) in enumerate(zip(batch, vectors)):
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload={
                            "text": chunk,
                            "doc_id": doc_id,
                            "filename": filename,
                            "source_type": source_type,
                            "chunk_index": batch_start + j,
                            "ingested_at": ingested_at,
                        },
                    )
                )

        for i in range(0, len(points), BATCH_SIZE):
            self.client.upsert(COLLECTION, points=points[i : i + BATCH_SIZE])

        logger.info("Stored %d chunks for '%s'", len(points), filename)
        return len(points)

    def search(self, question: str, limit: int = 5) -> str:
        vector = embed_query(question)
        results = self.client.query_points(
            collection_name=COLLECTION,
            query=vector,
            limit=limit,
        ).points
        return "\n\n".join(p.payload["text"] for p in results)

    def list_documents(self) -> list[dict]:
        docs: dict[str, dict] = {}
        offset = None
        while True:
            points, next_offset = self.client.scroll(
                collection_name=COLLECTION,
                with_payload=True,
                with_vectors=False,
                limit=100,
                offset=offset,
            )
            for point in points:
                doc_id = point.payload.get("doc_id")
                if not doc_id:
                    continue
                if doc_id not in docs:
                    docs[doc_id] = {
                        "doc_id": doc_id,
                        "filename": point.payload.get("filename", ""),
                        "source_type": point.payload.get("source_type", ""),
                        "ingested_at": point.payload.get("ingested_at", ""),
                        "chunks": 0,
                    }
                docs[doc_id]["chunks"] += 1
            if next_offset is None:
                break
            offset = next_offset

        return sorted(docs.values(), key=lambda x: x.get("ingested_at", ""), reverse=True)

    def delete_document(self, doc_id: str) -> None:
        self.client.delete(
            collection_name=COLLECTION,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                )
            ),
        )
        logger.info("Deleted document: %s", doc_id)

    def clear(self) -> None:
        self.client.delete_collection(COLLECTION)
        self.client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        logger.info("Collection cleared and recreated")

    def get_stats(self) -> dict:
        try:
            info = self.client.get_collection(COLLECTION)
            return {
                "total_chunks": info.points_count,
                "collection": COLLECTION,
                "vector_size": VECTOR_DIM,
            }
        except Exception:
            return {"total_chunks": 0, "collection": COLLECTION, "vector_size": VECTOR_DIM}
