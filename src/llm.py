import os
import logging
import requests

logger = logging.getLogger(__name__)

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_SYSTEM = (
    "You are a knowledgeable assistant. Answer questions using the provided context. "
    "If the context contains the answer, give it clearly. "
    "If the context is insufficient, say so briefly, then provide what insight you can. "
    "Never fabricate facts not found in the context."
)


def generate_answer(question: str, context: str) -> str:
    payload = {
        "model": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json",
    }
    resp = requests.post(_GROQ_URL, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
