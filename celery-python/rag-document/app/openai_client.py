from openai import OpenAI
from functools import lru_cache
from app.config import get_settings


@lru_cache
def get_openai_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(api_key = settings.openai_api_key)


def generate_embedding(text: str) -> list[float]:
    settings = get_settings()
    client = get_openai_client()

    response = client.embeddings.create(
        model = settings.embedding_model, input = text,
    )
    return response.data[0].embedding

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    client = get_openai_client()

    response = client.embeddings.create(
        model = settings.embedding_model, input = texts,
    )

    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [item.embedding for item in sorted_data]

def chat_completion(messages: list[dict], temperature: float = 0.3) -> str:
    settings = get_settings()
    client = get_openai_client()

    response = client.chat.completions.create(
        model = settings.chat_model, messages = messages, temperature = temperature,
    )

    return response.choices[0].message.content


