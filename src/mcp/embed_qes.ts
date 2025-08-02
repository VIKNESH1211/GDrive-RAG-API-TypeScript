  import { CohereClient } from 'cohere-ai';

const cohere = new CohereClient({
  token: process.env.COHERE_API_KEY!,
});

export async function getQuestionEmbedding(question: string) {
  const response = await cohere.embed({
    texts: [question],
    model: 'embed-v4.0',
    inputType: 'search_query',
  });

  return response.embeddings[0];
}
