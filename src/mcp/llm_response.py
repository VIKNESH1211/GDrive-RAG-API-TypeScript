import os
import requests


def get_llm_response(context: str, question: str) -> str:
    """Get LLM response from Groq API."""
    groq_api_key = os.getenv("GROQ_API_KEY")

    if not groq_api_key:
        raise ValueError("❌ GROQ_API_KEY not found in environment variables")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": "you are a helpful assistant that answers questions based on the provided context. If the context does not contain the answer, you have to infer from the provided data symantically and you need to answer , answer with fulll confidence. If you are not sure about the answer, you can say 'I am not sure but based on the context, I think the answer is ...'    "
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {question}"
            }
        ],
        "temperature": 0.2,
        "max_tokens": 1024
    }

    response = requests.post(url, json=payload, headers=headers)

    if not response.ok:
        raise Exception(f"Groq API Error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]
