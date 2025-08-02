import { QdrantClient } from "@qdrant/js-client-rest";
import dotenv from "dotenv";

dotenv.config();

const client = new QdrantClient({
  url: process.env.QDRANT_URL!,
  apiKey: process.env.QDRANT_KEY!,
});

export async function clearCollection() {
  const collectionName = "document-qna";

  try {
    const response = await client.delete(collectionName, {
      filter: {
        must: [], // Match all documents
      },
    });

    return { success: true, message: "Collection cleared", response };
  } catch (error: any) {
    console.error("❌ Error while clearing collection:", error);
    return {
      success: false,
      message: "Failed to clear collection",
      error: error?.message || error,
    };
  }
}
