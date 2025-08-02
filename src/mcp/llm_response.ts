import dotenv from "dotenv";

dotenv.config();

export async function getLLMResponse(context: string, question: string): Promise<string> {
  if (!process.env.GROQ_API_KEY) {
    throw new Error("❌ GROQ_API_KEY not found in environment variables");
  }

  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${process.env.GROQ_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: "llama-3.1-8b-instant", 
      messages: [
        {
          role: "system",
          content: "You are a helpful assistant. Answer the user using only the provided context."
        },
        {
          role: "user",
          content: `Context:\n${context}\n\nQuestion: ${question}`
        }
      ],
      temperature: 0.2,
      max_tokens: 1024
    })
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Groq API Error ${response.status}: ${err}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}
