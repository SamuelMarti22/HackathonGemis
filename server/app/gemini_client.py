from collections.abc import Iterator
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import get_settings

settings = get_settings()


@lru_cache
def get_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Embeddings para indexar (guardar en la base de datos)."""
    client = get_client()
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=settings.embedding_dim,
        ),
    )
    return [e.values for e in response.embeddings]


def embed_query(text: str) -> list[float]:
    """Embedding para una pregunta/caso del usuario."""
    client = get_client()
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=[text],
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=settings.embedding_dim,
        ),
    )
    return response.embeddings[0].values


def stream_text(prompt: str, system_instruction: str) -> Iterator[str]:
    client = get_client()
    for chunk in client.models.generate_content_stream(
        model=settings.chat_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
        ),
    ):
        if chunk.text:
            yield chunk.text


def generate_json(prompt: str, system_instruction: str, json_schema: dict) -> str:
    client = get_client()
    response = client.models.generate_content(
        model=settings.chat_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            response_mime_type="application/json",
            response_json_schema=json_schema,
        ),
    )
    return response.text
