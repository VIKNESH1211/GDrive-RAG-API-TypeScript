import { CohereClient } from 'cohere-ai';
import { QdrantClient } from '@qdrant/js-client-rest';
import { v4 as uuidv4 } from 'uuid';
import dotenv from 'dotenv';

dotenv.config();

// ✅ Cohere setup
const cohere = new CohereClient({
  token: process.env.COHERE_API_KEY!, // put in .env
});

// ✅ Qdrant setup
const qdrant = new QdrantClient({
  url: process.env.QDRANT_URL!, 
  apiKey: process.env.QDRANT_KEY!,
});

const COLLECTION_NAME = 'document-qna';

export async function embedAndUploadChunks(chunks: string[]) {
  console.log("📦 Chunk count:", chunks.length);

  const embed = await cohere.v2.embed({
    texts: chunks,
    model: 'embed-v4.0',
    inputType: 'search_document',
    // embeddingTypes: ['float'],  // ❌ Optional — try removing if error continues
  });

  //console.log("🧠 Embed response:", JSON.stringify(embed, null, 2));

  const embeddings = embed.embeddings['float']; // ✅ Fix here

  if (!embeddings || embeddings.length !== chunks.length) {
    throw new Error("❌ Embedding failed or mismatched.");
  }

  const points = chunks.map((chunk, index) => ({
    id: uuidv4(),
    vector: embeddings[index],
    payload: {
      text: chunk,
    },
  }));

  const uploadResponse = await qdrant.upsert(COLLECTION_NAME, {
    wait: true,
    batch: {
      vectors: points.map(p => p.vector),
      ids: points.map(p => p.id),
      payloads: points.map(p => p.payload),
    },
  });

  console.log("✅ Upload complete:", uploadResponse);
}