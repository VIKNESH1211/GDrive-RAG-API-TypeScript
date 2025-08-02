import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';
import readline from 'readline';

import { ingestFromDrive } from './mcp/drive-ingest.js';
import { chunkText } from './mcp/chunk.js';
import { embedAndUploadChunks } from './mcp/embedAndUpload.js';

// Resolve __dirname in ES module
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ✅ Load environment variables
dotenv.config({
  path: path.resolve(__dirname, '../.env'), // Adjusted to relative if needed
});

async function main() {
  const folderId = process.env.GOOGLE_DRIVE_FOLDER_ID;
  if (!folderId) {
    console.error("❌ Missing GOOGLE_DRIVE_FOLDER_ID in .env");
    return;
  }

  try {
    // ✅ Step 1: Ingest documents from Google Drive
    const documents = await ingestFromDrive(folderId);
    console.log(`✅ Loaded ${documents.length} documents`);

    // ✅ Step 2: Chunk the documents
    const allChunks: string[] = documents.flatMap(doc => {
      return chunkText(doc.text, 250, 50)
        .filter(chunk => chunk.trim().length > 0);
    });
    console.log(`✅ Created ${allChunks.length} chunks`);

    // ✅ Step 3: Embed + Upload to Qdrant
    await embedAndUploadChunks(allChunks);
    console.log("✅ Embedding and upload complete.");

    // ✅ Step 4: Ask Question, Search, Answer (NEW PART)
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    rl.question("Ask a question: ", async (userQuestion) => {
      const { getQuestionEmbedding } = await import('./mcp/embed_qes.js');
      const { searchContext } = await import('./mcp/search_quad.js');
      const { getLLMResponse } = await import('./mcp/llm_response.js');

      const questionEmbedding = await getQuestionEmbedding(userQuestion);
      const context = await searchContext(questionEmbedding);
      const answer = await getLLMResponse(context, userQuestion);

      console.log("\n🧠 Answer:");
      console.log(answer);

      rl.close();
    });

  } catch (error) {
    console.error("❌ Error during pipeline execution:", error);
  }
}

main();
