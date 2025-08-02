import { QdrantClient } from "@qdrant/js-client-rest";
import dotenv from "dotenv";


dotenv.config();


const qdrant = new QdrantClient({
  url: process.env.QDRANT_URL!,   // from .env
  apiKey: process.env.QDRANT_KEY! // from .env
});

export async function searchContext(vector: number[]): Promise<string> {
  const result = await qdrant.search("document-qna", {
    vector,
    top: 4
  });

  const context = result
    .map((point) => point.payload?.text ?? "")
    .filter(Boolean)
    .join("\n\n");

  return context;
}
