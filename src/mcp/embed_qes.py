import os
import cohere


def get_question_embedding(question: str) -> list[float]:
    """Get embedding for a question."""
    api_key = os.getenv("COHERE_API_KEY")
    co = cohere.Client(api_key=api_key)

    response = co.embed(
        texts=[question],
        model="embed-v4.0",
        input_type="search_query"
    )

    return response.embeddings[0]
