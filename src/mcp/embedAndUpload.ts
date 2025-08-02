import { CohereClient } from 'cohere-ai';
import { QdrantClient } from '@qdrant/js-client-rest';
import { v4 as uuidv4 } from 'uuid';
import dotenv from 'dotenv';

dotenv.config();


const cohere = new CohereClient({
  token: process.env.COHERE_API_KEY!,
});

const qdrant = new QdrantClient({
  url: process.env.QDRANT_URL!,
  apiKey: process.env.QDRANT_KEY!,
});

const COLLECTION_NAME = 'document-qna';
const MAX_BATCH_SIZE = 96;

function chunkArray<T>(array: T[], chunkSize: number): T[][] {
  const result: T[][] = [];
  for (let i = 0; i < array.length; i += chunkSize) {
    result.push(array.slice(i, i + chunkSize));
  }
  return result;
}

export async function embedAndUploadChunks(chunks: string[]) {
  console.log("📦 Total chunks:", chunks.length);
  const chunkedChunks = chunkArray(chunks, MAX_BATCH_SIZE);

  for (let i = 0; i < chunkedChunks.length; i++) {
    const batch = chunkedChunks[i];
    console.log(`🔹 Processing batch ${i + 1}/${chunkedChunks.length} (size: ${batch.length})`);

    const embed = await cohere.v2.embed({
      texts: batch,
      model: 'embed-v4.0',
      inputType: 'search_document',
    });

    const embeddings = embed.embeddings['float'];

    if (!embeddings || embeddings.length !== batch.length) {
      throw new Error("❌ Embedding failed or mismatched for batch.");
    }

    const points = batch.map((chunk, index) => ({
      id: uuidv4(),
      vector: embeddings[index],
      payload: { text: chunk },
    }));

    const uploadResponse = await qdrant.upsert(COLLECTION_NAME, {
      wait: true,
      batch: {
        vectors: points.map(p => p.vector),
        ids: points.map(p => p.id),
        payloads: points.map(p => p.payload),
      },
    });

    console.log(`✅ Batch ${i + 1} uploaded successfully.`);
  }

  console.log("🎉 All chunks embedded and uploaded to Qdrant.");
}
