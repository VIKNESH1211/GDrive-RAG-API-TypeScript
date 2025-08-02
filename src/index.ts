import express from 'express';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { ingestFromDrive } from './mcp/drive-ingest';
import { chunkText } from './mcp/chunk';
import { embedAndUploadChunks } from './mcp/embedAndUpload';
import { getQuestionEmbedding } from './mcp/embed_qes';
import { searchContext } from './mcp/search_quad';
import { getLLMResponse } from './mcp/llm_response';
import { clearCollection } from "./mcp/clear_collection";
import cors from 'cors';


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({
  path: path.resolve(__dirname, '../.env'),
});

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
}));


app.post('/ingest', async (req, res) => {
  const folderId = req.body.folderId;

  if (!folderId) {
    return res.status(400).json({ error: 'Missing folderId in request body' });
  }

  try {
    const documents = await ingestFromDrive(folderId);
    const allChunks = documents.flatMap(doc =>
      chunkText(doc.text, 250, 50).filter(chunk => chunk.trim().length > 0)
    );
    await embedAndUploadChunks(allChunks);

    res.json({
      message: 'Ingestion, chunking, embedding, and upload successful',
      documents: documents.length,
      chunks: allChunks.length,
    });
  } catch (error) {
    console.error('❌ Error in /ingest:', error);
    res.status(500).json({ error: 'Failed to ingest and update vector DB' });
  }
});


app.post('/ask', async (req, res) => {
  const question = req.body.question;
  if (!question) {
    return res.status(400).json({ error: 'Missing question in request body' });
  }

  try {
    const embedding = await getQuestionEmbedding(question);
    const context = await searchContext(embedding);
    const answer = await getLLMResponse(context, question);

    res.json({
      question,
      context,
      answer,
    });
  } catch (error) {
    console.error('❌ Error in /ask:', error);
    res.status(500).json({ error: 'Failed to generate answer' });
  }
});

app.post("/clear", async (req, res) => {
  const result = await clearCollection();
  if (result.success) {
    res.status(200).json(result);
  } else {
    res.status(500).json(result);
  }
});


app.listen(port, '0.0.0.0', () => {
  console.log(`🚀 RAG API running on http://0.0.0.0:${port}`);
});

