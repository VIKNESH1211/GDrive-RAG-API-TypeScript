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
  content: `You are WABAG's intelligent AI assistant, designed to communicate in a natural, friendly, and professional tone. 
  You represent WABAG — a global leader in sustainable water and wastewater management.

  - When users greet you (e.g., "Hi", "Hello"), respond warmly and conversationally, like: 
    "Hi there! How can I help you today?" or "Hello! What would you like to know about WABAG?"
    Avoid sounding overly formal or like a chatbot starting a scripted conversation.

  - For general queries, provide concise, human-like answers using only the information provided in the context. 
    Never say phrases like “according to the context” or “based on the context”.

  - If users ask for factual, contact, or location-specific details not in the context, 
    politely guide them to visit WABAG’s official website or contact page for the most accurate information.

  - Maintain WABAG’s professional and trustworthy tone. 
    Be informative and engaging, but never fabricate or guess any data.

  - Respond with proper line breaks and markdown(bold , itallics etc) to enhance readability.  

  Your goal: make users feel like they’re chatting with a knowledgeable and approachable WABAG representative.`
},
{
  role: "user",
  content: `Here is some background information:\n${context}\n\nNow, please answer this user query naturally:\n${question}`
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
